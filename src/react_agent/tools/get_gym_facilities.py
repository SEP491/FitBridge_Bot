from langchain_core.tools import tool
from langsmith import traceable
from react_agent.infrastructure import get_postgres_connection, get_graph

@tool
def get_gym_facilities(gym_id: str, facility_name: str = None, limit: int = 5) -> str:
    """Get the gym facilities of a gym by its ID (uuid). Call only once. If facility_name is provided IN ENGLISH, return the facility with the given name. The limit is the maximum number of facilities to return. If user requires getting all: assign limit = -1, or it will return 5 facilities by default."""
    graph = get_graph()
    
    # Count query (no limit) to get total available
    if facility_name:
        count_query = """
            MATCH (gym:Gym)-[:OWNS]->(facility:GymFacility)
            WHERE gym.dbId = $gym_id
            CALL db.index.fulltext.queryNodes("facilityNameIndex", $facility_name + "~2")
            YIELD node AS candidate_facility, score
            WHERE candidate_facility = facility AND score > 0.5
            RETURN count(candidate_facility) AS total_count
        """
        data_query = """
            MATCH (gym:Gym)-[:OWNS]->(facility:GymFacility)
            WHERE gym.dbId = $gym_id
            CALL db.index.fulltext.queryNodes("facilityNameIndex", $facility_name + "~2")
            YIELD node AS candidate_facility, score
            WHERE candidate_facility = facility AND score > 0.5
            RETURN candidate_facility.name AS name,
                   candidate_facility.description AS description
        """
    else:
        count_query = """
            MATCH (gym:Gym)-[:OWNS]->(facility:GymFacility)
            WHERE gym.dbId = $gym_id
            RETURN count(facility) AS total_count
        """
        data_query = """
            MATCH (gym:Gym)-[:OWNS]->(facility:GymFacility)
            WHERE gym.dbId = $gym_id
            RETURN facility.name AS name,
                   facility.description AS description
        """

    if limit != -1:
        data_query += " LIMIT $limit"
    
    # Get total count
    count_result = graph.query(count_query, {"gym_id": gym_id, "facility_name": facility_name})
    total_count = count_result[0]["total_count"] if count_result else 0
    
    # Get data with limit
    result = graph.query(data_query, {"gym_id": gym_id, "facility_name": facility_name, "limit": limit})
    
    if result:
        returned_count = len(result)
        return f"Found {total_count} total facilities, showing {returned_count}: {result}"
    else:
        return f"No facilities were found for the gym (total: 0)."