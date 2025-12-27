from ..state import State
from ..entities.entities import RetrievedPtAsset
from react_agent.infrastructure import get_graph
import asyncio

async def graph_search(state: State) -> State:
    """Search the graph for freelance PTs that match the state criteria."""

    print(f"user_origin: {state.user_origin}")
    print(f"search_criteria: {state.search_criteria}")
    print(f"certificates: {state.search_criteria.certificates}")

    graph = await asyncio.to_thread(get_graph)
    query = """
MATCH (pt:FreelancePT)

// --- 1. Geospatial, Gender & EXISTENCE Filter ---
WITH pt, 
     point.distance(
         point({latitude: pt.lat, longitude: pt.lon}), 
         point({latitude: $lat, longitude: $lon})
     ) AS dist_meters

WHERE 
    // A. Location Filter
    (($lat IS NULL OR $lon IS NULL) OR (dist_meters < 5000))
    AND
    // B. Gender Filter
    ($gender IS NULL 
        OR ($gender = 'male' AND pt.isMale = true) 
        OR ($gender = 'female' AND pt.isMale = false)
    )
    AND
    // C. GHOST NODE FILTER (Added)
    // Only return PTs that actually have certificates uploaded
    (pt)-[:HAS_CERTIFICATE]->()

// --- 2. Certificate Search Subquery ---
CALL (pt) {
    // Branch A: No search terms -> Return null/empty
    WITH pt
    WHERE $query_terms IS NULL OR size($query_terms) = 0
    // Try to find at least one cert to calculate experience
    OPTIONAL MATCH (pt)-[r:HAS_CERTIFICATE]->(:Certificates)
    RETURN 
        [] AS found_certs, 
        0 AS cert_matches,
        min(r.providedDate) AS oldest_cert_date
    
    UNION
    
    // Branch B: User provided search terms
    WITH pt
    WHERE size($query_terms) > 0
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

// --- 3. Calculate Experience ---
WITH pt, dist_meters, found_certs, cert_matches,
     CASE 
        WHEN oldest_cert_date IS NOT NULL 
        THEN duration.between(date(oldest_cert_date), date()).years 
        ELSE 0 
     END AS experience_years

// --- 4. Experience Filter ---
WHERE $min_experience_years IS NULL OR experience_years >= $min_experience_years

// --- 5. Calculate Scores ---
WITH pt, dist_meters, found_certs, experience_years,
     (cert_matches * 10) AS cert_score,
     
     // Price Score
     CASE 
        WHEN $max_price IS NOT NULL AND pt.cheapestPrice IS NOT NULL AND pt.cheapestPrice <= $max_price THEN 20 
        ELSE 0 
     END AS price_score,

     // Rating Score (ADDED)
     CASE 
        WHEN $rating IS NOT NULL AND pt.avgRating IS NOT NULL 
             AND ($rating - 0.5 <= pt.avgRating <= $rating + 0.5) THEN 10 
        ELSE 0 
     END AS rating_score

WITH pt, found_certs, dist_meters, experience_years,
     (cert_score + price_score + rating_score) AS partial_score,
     {
         certificates: cert_score, 
         price: price_score,
         rating: rating_score
     } AS score_breakdown

// --- 6. Sorting & Limiting ---
ORDER BY partial_score DESC, dist_meters ASC
LIMIT coalesce($limit, 10)

// --- 7. Hydrate Details for the Top Results ---
OPTIONAL MATCH (pt)-[:HAS_CERTIFICATE]->(all_cert:Certificates)
WITH pt, found_certs, dist_meters, experience_years, partial_score, score_breakdown,
     collect(distinct all_cert.certName) AS all_certificates

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
    pt.avgRating AS rating,
    found_certs AS found_certificates,
    score_breakdown,
    partial_score
    """
    
    query_results = await asyncio.to_thread(
        graph.query,
        query, 
        {
            "fuzzy_levenshtein_distance": "~2",  # String format for Lucene fuzzy search
            "min_fuzzy_scoring": 1, 
            "lat": state.search_center.latitude, 
            "lon": state.search_center.longitude, 
            "query_terms": list(state.search_criteria.certificates) if state.search_criteria.certificates else None,
            "max_price": state.search_criteria.max_price,
            # "initial_radius_in_km": state.search_criteria.distance_in_meters / 1000 if state.search_criteria.distance_in_meters else None,
            "gender": state.search_criteria.gender,
            "min_experience_years": state.search_criteria.min_experience_years,
            "limit": 5,
            # "distance_buffer_factor": 1.5,
        }
    )
    print("query_results: ", query_results)
    candidates = [RetrievedPtAsset(**node) for node in query_results]
    state.candidates.extend(candidates)
    return state
