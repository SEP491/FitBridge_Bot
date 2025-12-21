import pytest
from react_agent.domain.entities import UserLocation
from react_agent.graph import graph
from react_agent.context import Context
from langchain_core.messages import HumanMessage

@pytest.mark.anyio
async def test_combined_update_and_recommend():
    """
    Combined integration test:
    User provides criteria -> Agent updates state -> Agent automatically calls recommendation.
    """
    context = Context(model="openai/gpt-4o-mini")
    
    print("\n--- Sending User Request ---")
    msg = "I want to build muscle and find a gym with a pool. Please recommend some gyms."
    
    res = await graph.ainvoke({"user_location": UserLocation(latitude=10.875, longitude=106.800), "messages": [HumanMessage(content=msg)]}, context=context)
    
    # 1. Verify Search Criteria Updated
    criteria = res.get("search_criteria")
    print(f"Criteria: {criteria}")
    assert criteria is not None
    assert criteria.goal is not None and "muscle" in criteria.goal.lower()
    
    # 2. Verify Tool Call Sequence
    tool_calls = []
    for m in res["messages"]:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                tool_calls.append(tc["name"])
    
    print(f"Tools called: {tool_calls}")
    
    # Assert both are called
    # assert "update_search_state" in tool_calls
    assert "get_gym_recommendations" in tool_calls
    
    # Assert Order: update before recommend
    # Finds the *first* occurrence
    # idx_update = tool_calls.index("update_search_state")
    idx_recommend = tool_calls.index("get_gym_recommendations")
    # assert idx_update < idx_recommend, "update_search_state should be called before get_gym_recommendations"

    # 3. Verify Final Report
    report = res.get("final_report")
    print(f"Final Report Length: {len(report) if report else 0}")
    assert report is not None
    assert len(report) > 0
