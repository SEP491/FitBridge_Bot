import os
import re
from agent.utils.state.MessageState import OverallState, RetrievedGyms
from agent import get_graph

def escape_lucene_special_chars(term: str) -> str:
    """Escape special characters that have meaning in Lucene query syntax."""
    # Lucene special characters: + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
    special_chars = r'([+\-&|!(){}[\]^"~*?:\\/])'
    return re.sub(special_chars, r'\\\1', term)

def coarse_gym_retrieval(state: OverallState) -> OverallState:
    graph = get_graph()
    query = """
        MATCH (gym:Gym)
        WITH gym, point.distance(point({latitude: gym.lat, longitude: gym.lon}), point({latitude: $lat, longitude: $lon})) AS dist_meters
        WHERE dist_meters < ($initial_radius_in_km * 1000)

        // Isolate the search logic per gym
        CALL (gym) {
            UNWIND $query_terms AS query_term
            CALL db.index.fulltext.queryNodes("assetNameIndex", query_term + $fuzzy_levenshtein_distance)
            YIELD node AS candidate_asset, score
            WHERE score > $min_fuzzy_scoring
            
            // Check if THIS gym owns it
            MATCH (gym)-[:OWNS]->(candidate_asset)
            
            RETURN collect(candidate_asset.name) as found_equip, count(candidate_asset) as equip_matches
        }
        // Calculate Sub-Scores using CASE logic
        WITH gym, dist_meters, found_equip,
            (equip_matches * 10) AS equip_score,
            
            CASE WHEN gym.cheapestPrice <= $max_price THEN 20 ELSE 0 END AS price_score,
            
            CASE WHEN $rating - 0.5 <= gym.avgRating <= $rating + 0.5 THEN 10 ELSE 0 END AS rating_score,
            // Assuming gym.close_time is an integer (e.g., 2200) or time type
            CASE WHEN localtime(gym.closeTime) <= localtime($close_time) AND
                localtime(gym.openTime) >= localtime($open_time) THEN 15 ELSE 0 END AS time_score

        // 3. TOTAL SCORE
        WITH gym, found_equip, dist_meters,
            (equip_score + price_score + rating_score + time_score
            ) AS partial_score,
            {
                equipment: equip_score, 
                price: price_score, 
                rating: rating_score,
                time: time_score
            } AS score_breakdown

        // 4. RETURN SORTED RESULTS
        RETURN 
            gym.dbId as id,
            gym.name AS name,
            gym.lat AS lat,
            gym.lon AS lon,
            gym.businessAddress AS address,
            gym.openTime AS open_hours,
            gym.closeTime AS close_hours,
            gym.cheapestPrice AS price,
            gym.avgRating AS rating,
            dist_meters,
            found_equip,
            score_breakdown,
            partial_score
        ORDER BY partial_score DESC, dist_meters ASC
        LIMIT $limit
    """
    # Escape special Lucene characters in query terms to prevent parse errors
    raw_equipments = state.gyms_preferences.preferred_equipments or []
    escaped_query_terms = [escape_lucene_special_chars(term) for term in raw_equipments]

    query_results = graph.query(
        query, 
        {
            "fuzzy_levenshtein_distance": "~2",  # String format for Lucene fuzzy search
            "min_fuzzy_scoring": 1, 
            "lat": state.user_location.latitude, 
            "lon": state.user_location.longitude, 
            "query_terms": escaped_query_terms,
            "max_price": state.gyms_preferences.max_price, 
            "close_time": state.gyms_preferences.close_hours, 
            "open_time": state.gyms_preferences.open_hours,
            "initial_radius_in_km": state.gyms_preferences.distance_in_meters / 1000,
            "rating": state.gyms_preferences.rating,
            "limit": 5
        }
    )

    return { "candidate_gyms": query_results }