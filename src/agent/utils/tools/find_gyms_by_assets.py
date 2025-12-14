from agent import get_graph
from langchain_core.tools import tool
    
@tool
def find_gyms_by_assets(assets: list[str]) -> str:
    """Find gyms that have specific equipment.
    
    Args:
        assets: List of equipment names to search for (e.g., ["dumbbells", "treadmill"])
    
    Returns:
        A formatted string describing which gyms have the requested equipment.
    """
    # search gyms with preferred equipments and goals, then join the results
    graph = get_graph()
    query_result = graph.query(
        """
        // 1. Unwind the list so we can search for each item individually
        UNWIND $target_assets AS query_term

        // 2. Perform Fuzzy Search
        // We append '~' to the end of the term, which tells Lucene to allow typos
        CALL db.index.fulltext.queryNodes("assetNameIndex", query_term + "~", {limit: 1} )
        YIELD node AS asset, score
        // 3. Threshold to filter out bad matches
        WHERE score > 1.5

        // 4. Find the Gyms that own these specific fuzzy-matched assets
        MATCH (gym:Gym)-[:OWNS]->(asset)

        // 5. Aggregate results
        WITH 
            gym, 
            // Use DISTINCT so if "Dumbbell" matches 2 assets, we don't count duplicates
            collect(DISTINCT asset.name) AS AssetList, 
            count(DISTINCT asset) AS TotalAssetCount

        RETURN 
            gym.name AS GymName, 
            TotalAssetCount, 
            AssetList
        ORDER BY TotalAssetCount DESC;
        """,
        {"target_assets": assets})
    if not query_result:
        return f"No gyms found with the requested equipment: {', '.join(assets)}"
    
    # Format output as natural language for LLM understanding
    lines = [f"Found {len(query_result)} gym(s) with the requested equipment:\n"]
    for i, row in enumerate(query_result, 1):
        gym_name = row["GymName"]
        count = row["TotalAssetCount"]
        equipment = ", ".join(row["AssetList"])
        lines.append(f"{i}. {gym_name} - has {count} matching equipment: {equipment}")
    
    return "\n".join(lines)