from react_agent.infrastructure import get_graph
from langchain_core.tools import tool

@tool
def get_gym_equipments(gym_id: str, equipment_name: str = None, limit: int = 5) -> str:
    """Get the equipments of a gym by gym's ID (uuid). Call only once. If equipment_name is provided, return the equipment with the given name. The limit is the maximum number of equipments to return. If user requires getting all: assign limit = -1, or it will return 5 equipments by default."""
    graph = get_graph()
    
    # Count query (no limit) to get total available
    if equipment_name:
        count_query = """
            MATCH (gym:Gym)-[:OWNS]->(equipment:GymAsset)
            WHERE gym.dbId = $gym_id
            CALL db.index.fulltext.queryNodes("assetNameIndex", $equipment_name + "~2")
            YIELD node AS candidate_asset, score
            WHERE candidate_asset = equipment AND score > 0.5
            RETURN count(candidate_asset) AS total_count
        """
        data_query = """
            MATCH (gym:Gym)-[:OWNS]->(equipment:GymAsset)
            WHERE gym.dbId = $gym_id
            CALL db.index.fulltext.queryNodes("assetNameIndex", $equipment_name + "~2")
            YIELD node AS candidate_asset, score
            WHERE candidate_asset = equipment AND score > 0.5
            RETURN candidate_asset.name AS name,
                   candidate_asset.description AS description,
                   candidate_asset.equipmentCategory AS equipmentCategory,
                   candidate_asset.targetMuscularGroups AS targetMuscularGroups
        """
    else:
        count_query = """
            MATCH (gym:Gym)-[:OWNS]->(equipment:GymAsset)
            WHERE gym.dbId = $gym_id
            RETURN count(equipment) AS total_count
        """
        data_query = """
            MATCH (gym:Gym)-[:OWNS]->(equipment:GymAsset)
            WHERE gym.dbId = $gym_id
            RETURN equipment.name AS name,
                   equipment.description AS description,
                   equipment.equipmentCategory AS equipmentCategory,
                   equipment.targetMuscularGroups AS targetMuscularGroups
        """
    
    if limit != -1:
        data_query += " LIMIT $limit"

    # Get total count
    count_result = graph.query(count_query, {"gym_id": gym_id, "equipment_name": equipment_name})
    total_count = count_result[0]["total_count"] if count_result else 0
    
    # Get data with limit
    result = graph.query(data_query, {"gym_id": gym_id, "equipment_name": equipment_name, "limit": limit})
    
    if result:
        returned_count = len(result)
        return f"Found {total_count} total equipments, showing {returned_count}: {result}"
    else:
        return f"No equipments were found for the gym (total: 0)."