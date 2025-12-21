import pytest
from react_agent.tools import TOOLS
from react_agent.domain.criterias import SearchCriteria
from react_agent.domain.entities import UserLocation

def test_tools_registration():
    """Verify that all expected tools are registered in the TOOLS list."""
    tool_names = [tool.name for tool in TOOLS]
    expected_tools = [
        "get_gym_details_by_id",
        "get_gym_details_by_name",
        "get_gym_facilities",
        "get_gym_equipments",
        "get_gym_reviews_and_ratings",
        "find_gyms_by_assets",
        "get_gym_recommendations"
    ]
    for tool in expected_tools:
        assert tool in tool_names, f"Tool {tool} is missing from the registered TOOLS list"

@pytest.mark.anyio
async def test_get_gym_recommendations_tool_direct():
    """Verify the recommendation tool (the blackbox) can be called directly with state."""
    from react_agent.tools.get_gym_recommendations import get_gym_recommendations
    
    # Mock the state that InjectedState would provide
    mock_state = {
        "search_criteria": SearchCriteria(goal="Build muscle"),
        "user_location": UserLocation(latitude=10.8, longitude=106.8)
    }
    
    # Call the tool directly
    # Note: In a test, we pass the state manually because InjectedState is handled by LangGraph at runtime
    result = get_gym_recommendations.invoke({"state": mock_state})
    
    assert isinstance(result, str), "Tool should return a markdown string"
    assert "🏋️" in result or "I couldn't find" in result, "Unexpected tool output"

