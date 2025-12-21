from ..state import State
from ..entities.entities import RetrievedGymAsset
from react_agent.infrastructure import get_graph
import re
import asyncio

async def graph_search(state: State) -> State:
    """Search the graph for the gyms and PTs that match the state."""

    print(f"user_location: {state.user_location}")
    print(f"search_criteria: {state.search_criteria}")
    print(f"equipments_and_facilities: {state.search_criteria.equipments_and_facilities}")

    graph = await asyncio.to_thread(get_graph)
    query = """
    MATCH (gym:Gym)
    // 1. Geospatial Filter (Null-safe)
    WITH gym, 
        point.distance(point({latitude: gym.lat, longitude: gym.lon}), point({latitude: $lat, longitude: $lon})) AS dist_meters,
        // Default buffer to 1.0 if not provided
        coalesce($distance_buffer_factor, 1.0) AS buffer
    WHERE $lat IS NULL OR $lon IS NULL OR $initial_radius_in_km IS NULL 
    OR dist_meters < ($initial_radius_in_km * 1000 * buffer)

    // 2. Main Equipment Search
    CALL (gym) {
        UNWIND $query_terms AS query_term
        CALL db.index.fulltext.queryNodes("assetNameIndex", query_term + coalesce($fuzzy_levenshtein_distance, ""))
        YIELD node AS candidate_asset, score
        WHERE score > coalesce($min_fuzzy_scoring, 0)
        
        MATCH (gym)-[:OWNS]->(candidate_asset)
        RETURN collect(distinct candidate_asset.name) as found_equip, count(distinct candidate_asset) as equip_matches
    }

    // 3. Related Equipment Logic
    CALL (gym, found_equip) {
        WITH gym, found_equip
        WHERE found_equip IS NOT NULL
        
        MATCH (gym)-[:OWNS]->(original:GymAsset)-[:TARGETS]->(m:Muscle)
        WHERE original.name IN found_equip

        MATCH (gym)-[:OWNS]->(related:GymAsset)-[:TARGETS]->(m)
        WHERE NOT related.name IN found_equip
        
        WITH m, related
        ORDER BY rand()
        RETURN m.name AS muscle_group, collect(distinct related.name)[0] AS alt_machine
    }

    // 4. Aggregate & Calculate Scores (Null-safe checks for Gym properties)
    WITH gym, dist_meters, 
        coalesce(found_equip, []) AS found_equip, 
        collect(distinct alt_machine) AS related_recommendations,
        (coalesce(equip_matches, 0) * 10) AS equip_score,
        
        // Price: Ensure gym.cheapestPrice isn't null before comparing
        CASE 
            WHEN $max_price IS NOT NULL AND gym.cheapestPrice IS NOT NULL AND gym.cheapestPrice <= $max_price THEN 20 
            ELSE 0 
        END AS price_score,
        
        // Rating: Ensure gym.avgRating isn't null
        CASE 
            WHEN $rating IS NOT NULL AND gym.avgRating IS NOT NULL 
                AND ($rating - 0.5 <= gym.avgRating <= $rating + 0.5) THEN 10 
            ELSE 0 
        END AS rating_score,
        
        // Time: Ensure both params and gym properties are present
        CASE 
            WHEN $open_time IS NOT NULL AND $close_time IS NOT NULL 
                AND gym.openTime IS NOT NULL AND gym.closeTime IS NOT NULL
                AND localtime(gym.closeTime) <= localtime($close_time) 
                AND localtime(gym.openTime) >= localtime($open_time) THEN 15 
            ELSE 0 
        END AS time_score

    // 5. Final Calculations
    WITH gym, found_equip, related_recommendations, dist_meters,
        (equip_score + price_score + rating_score + time_score) AS partial_score,
        {
            equipment: equip_score, 
            price: price_score, 
            rating: rating_score,
            time: time_score
        } AS score_breakdown

    // 6. Return Sorted Results
    RETURN 
        gym.dbId as id,
        gym.name AS name,
        gym.lat AS latitude,
        gym.lon AS longitude,
        gym.businessAddress AS address,
        gym.openTime AS open_hours,
        gym.closeTime AS close_hours,
        gym.cheapestPrice AS price,
        gym.avgRating AS rating,
        toInteger(dist_meters) AS distance_in_meters,
        found_equip,
        related_recommendations,
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
            "query_terms": list(state.search_criteria.equipments_and_facilities),
            "max_price": state.search_criteria.max_price, 
            "close_time": state.search_criteria.close_hours, 
            "open_time": state.search_criteria.open_hours,
            "initial_radius_in_km": state.search_criteria.distance_in_meters / 1000,
            "rating": state.search_criteria.rating,
            "limit": 5,
            "distance_buffer_factor": 1.5, # 150% of the initial radius, used to account for the actual distance to the gyms
        }
    )
    print("query_results: ", query_results)
    candidates = [RetrievedGymAsset(**node) for node in query_results]
    state.candidates.extend(candidates)
    return state
