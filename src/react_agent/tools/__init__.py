# Tools module
from react_agent.tools.get_gym_details_by_id import get_gym_details_by_id
from react_agent.tools.get_gym_details_by_name import get_gym_details_by_name
from react_agent.tools.get_gym_facilities import get_gym_facilities
from react_agent.tools.get_gym_equipments import get_gym_equipments
from react_agent.tools.get_gym_reviews_and_ratings import get_gym_reviews_and_ratings
from react_agent.tools.get_gym_recommendations import get_gym_recommendations
from react_agent.tools.get_pt_recommendations import get_pt_recommendations
# Note: extract_locations is now a node, not a tool
# from react_agent.tools.extract_locations import extract_locations
# from react_agent.tools.update_search_state import update_search_state

TOOLS = [
    get_gym_details_by_id,
    # get_gym_details_by_name,
    get_gym_facilities,
    get_gym_equipments,
    get_gym_reviews_and_ratings,
    get_gym_recommendations,
    get_pt_recommendations,
]