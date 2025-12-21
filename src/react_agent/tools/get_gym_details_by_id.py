from langchain_core.tools import tool
from langsmith import traceable
from react_agent.infrastructure import get_postgres_connection

@tool
def get_gym_details_by_id(gym_id: str) -> str:
    """Get the details of a gym by its ID (uuid). Call only once"""
    connection = get_postgres_connection()
    cursor = connection.cursor()
    query = """
    WITH GymOwnerIds AS (
        SELECT anur."UserId"
        FROM "AspNetUserRoles" anur
        JOIN "AspNetRoles" anr ON anur."RoleId" = anr."Id"
        WHERE anr."NormalizedName" = 'GYMOWNER'
    )
    select anu."UserName", anu."Email", anu."PhoneNumber" from "AspNetUsers" anu join GymOwnerIds a on a."UserId" = anu."Id" WHERE anu."Id" = %s"""

    cursor.execute(query, (gym_id,))
    result = cursor.fetchone()
    if result:
        print(result)
        return f"The details of the gym {gym_id} are as follows: {result}"
    else:
        print(f"The gym {gym_id} was not found.")
        return f"The gym {gym_id} was not found."