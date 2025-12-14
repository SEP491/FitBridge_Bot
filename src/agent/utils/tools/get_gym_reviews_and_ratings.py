from langchain_core.tools import tool
from langsmith import traceable
from agent import get_postgres_connection

@tool
def get_gym_reviews_and_ratings(gym_id: str, limit: int = 5) -> str:
    """Get reviews and ratings for a gym by its ID (uuid). Call only once. Returns random sample of reviews."""
    connection = get_postgres_connection()
    cursor = connection.cursor()
    
    # Count query to get total reviews
    count_query = """
    SELECT COUNT(*) AS total_count
    FROM "Reviews" r
    JOIN "AspNetUsers" anu ON r."GymId" = anu."Id"
    WHERE anu."Id" = %s
    """
    
    # Data query with limit
    data_query = """
    SELECT
        r."Rating",
        r."Content",
        b."FullName" AS ReviewerFullName
    FROM
        "Reviews" r
    JOIN
        "AspNetUsers" anu ON r."GymId" = anu."Id"
    JOIN
        "AspNetUsers" b ON r."UserId" = b."Id"
    WHERE
        anu."Id" = %s
    ORDER BY random()
    LIMIT %s
    """

    # Get total count
    cursor.execute(count_query, (gym_id,))
    count_result = cursor.fetchone()
    total_count = count_result[0] if count_result else 0
    
    # Get data with limit
    cursor.execute(data_query, (gym_id, limit))
    results = cursor.fetchall()
    
    if results:
        returned_count = len(results)
        reviews_str = "\n".join([f"- {r[2]}: {r[0]}/5 stars - \"{r[1]}\"" for r in results])
        return f"Found {total_count} total reviews, showing {returned_count}:\n{reviews_str}"
    else:
        return f"No reviews found for gym {gym_id} (total: 0)."