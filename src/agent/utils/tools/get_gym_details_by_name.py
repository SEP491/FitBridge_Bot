from langchain_core.tools import tool

@tool
def get_gym_details_by_name(gym_name: str) -> str:
    """Get the details of a gym by its name. Only use this tool if you have no information about the gym's ID. Call only once"""
    return f"The details of the gym {gym_name} are as follows: Gym is very good, 10/10 would come again."