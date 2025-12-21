from ..state import State
from ..entities.entities import RetrievedPtAsset
from react_agent.infrastructure import get_graph
import asyncio

async def graph_search(state: State) -> State:
    """Search the graph for freelance PTs that match the state criteria."""

    print(f"user_location: {state.user_location}")
    print(f"search_criteria: {state.search_criteria}")
    print(f"certificates: {state.search_criteria.certificates}")

    graph = await asyncio.to_thread(get_graph)
    query = """
    MATCH (pt:FreelancePT)

    // 1. Geospatial Filter (Null-safe)
    WITH pt, 
        point.distance(point({latitude: pt.lat, longitude: pt.lon}), point({latitude: $lat, longitude: $lon})) AS dist_meters,
        coalesce($distance_buffer_factor, 1.0) AS buffer
    WHERE $lat IS NULL OR $lon IS NULL OR $initial_radius_in_km IS NULL 
        OR dist_meters < ($initial_radius_in_km * 1000 * buffer)

    // 2. Gender Filter (Null-safe)
    AND($gender IS NULL 
        OR ($gender = 'male' AND pt.isMale = true) 
        OR ($gender = 'female' AND pt.isMale = false))

    // 3. Certificate Search via fulltext index
    CALL (pt) {
        WITH pt
        OPTIONAL MATCH (pt)-[r:HAS_CERTIFICATE]->(cert:Certificates)
        WITH pt, r, cert
        WHERE $query_terms IS NULL OR size($query_terms) = 0
        RETURN 
            collect(distinct cert.certName) AS found_certs, 
            0 AS cert_matches,
            min(r.providedDate) AS oldest_cert_date
        
        UNION
        
        WITH pt
        WHERE $query_terms IS NOT NULL AND size($query_terms) > 0
        UNWIND $query_terms AS query_term
        CALL db.index.fulltext.queryNodes("certificateSearchIndex", query_term + coalesce($fuzzy_levenshtein_distance, ""))
        YIELD node AS candidate_cert, score
        WHERE score > coalesce($min_fuzzy_scoring, 0)
        
        MATCH (pt)-[r:HAS_CERTIFICATE]->(candidate_cert)
        RETURN 
            collect(distinct candidate_cert.certName) AS found_certs, 
            count(distinct candidate_cert) AS cert_matches,
            min(r.providedDate) AS oldest_cert_date
    }

    // 4. Calculate Experience Years from oldest certificate
    WITH pt, dist_meters, 
        coalesce(found_certs, []) AS found_certs,
        coalesce(cert_matches, 0) AS cert_matches,
        CASE 
            WHEN oldest_cert_date IS NOT NULL 
            THEN duration.between(oldest_cert_date, date()).years
            ELSE 0 
        END AS experience_years

    // 5. Experience Filter (Null-safe)
    WHERE $min_experience_years IS NULL OR experience_years >= $min_experience_years

    // 6. Calculate Scores
    WITH pt, dist_meters, found_certs, experience_years,
        (cert_matches * 10) AS cert_score,
        
        // Price Score
        CASE 
            WHEN $max_price IS NOT NULL AND pt.cheapestPrice IS NOT NULL AND pt.cheapestPrice <= $max_price THEN 20 
            ELSE 0 
        END AS price_score

    // 7. Final Calculations
    WITH pt, found_certs, dist_meters, experience_years,
        (cert_score + price_score) AS partial_score,
        {
            certificates: cert_score, 
            price: price_score
        } AS score_breakdown

    // 8. Get all certificates for the PT
    OPTIONAL MATCH (pt)-[:HAS_CERTIFICATE]->(all_cert:Certificates)
    WITH pt, found_certs, dist_meters, experience_years, partial_score, score_breakdown,
        collect(distinct all_cert.certName) AS all_certificates

    // 9. Return Sorted Results
    RETURN 
        pt.dbId AS id,
        pt.fullName AS name,
        pt.lat AS latitude,
        pt.lon AS longitude,
        pt.businessAddress AS address,
        toInteger(dist_meters) AS distance_in_meters,
        experience_years,
        CASE WHEN pt.isMale THEN 'male' ELSE 'female' END AS gender,
        all_certificates AS certificates,
        pt.cheapestPrice AS price,
        found_certs AS found_certificates,
        score_breakdown,
        partial_score
    ORDER BY partial_score DESC, distance_in_meters ASC
    LIMIT coalesce($limit, 10)
    """
    
    query_results = await asyncio.to_thread(
        graph.query,
        query, 
        {
            "fuzzy_levenshtein_distance": "~2",  # String format for Lucene fuzzy search
            "min_fuzzy_scoring": 1, 
            "lat": state.user_location.latitude, 
            "lon": state.user_location.longitude, 
            "query_terms": list(state.search_criteria.certificates) if state.search_criteria.certificates else None,
            "max_price": state.search_criteria.max_price,
            "initial_radius_in_km": state.search_criteria.distance_in_meters / 1000 if state.search_criteria.distance_in_meters else None,
            "gender": state.search_criteria.gender,
            "min_experience_years": state.search_criteria.min_experience_years,
            "limit": 5,
            "distance_buffer_factor": 1.5,
        }
    )
    print("query_results: ", query_results)
    candidates = [RetrievedPtAsset(**node) for node in query_results]
    state.candidates.extend(candidates)
    return state
