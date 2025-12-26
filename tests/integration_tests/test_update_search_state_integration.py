import pytest
from react_agent.graph import graph
from react_agent.context import Context

@pytest.mark.anyio
async def test_agent_uses_update_search_state():
    """
    End-to-end integration test:
    1. Send user message with criteria ("I want to build muscle").
    2. Agent should call 'update_search_state'.
    3. Graph state should reflect the extracted criteria.
    """
    
    # 1. User message
    messages = [
        ("user", "I want to build muscle and find a gym with a pool. i am at lat 10.875, lon 106.800. Use update_search_state tool to update the search state. After receiving the updated search state, dont do anything else.")
    ]
    
    context = Context(
        # Use a model capable of tool calling
        model="openai/gpt-4o-mini"
    )

    # 2. Run the agent
    print("\n--- Invoking Agent ---")
    # This runs the full ReAct loop
    # We pass user_origin to ensure the tool receives it
    from react_agent.domain.entities import UserOrigin
    
    res = await graph.ainvoke(
        {
            "messages": messages,
        }, 
        context=context
    )

    print(res)
    # 3. Verify State Update
    print("\n--- Resulting State ---")
    search_criteria = res.get("search_criteria")
    print(f"Search Criteria: {search_criteria}")
    
    # Check if search_criteria was updated
    assert search_criteria is not None, "Search criteria should be initialized"
    
    # Verify Goal
    # The agent might not extract it if it thinks it's just chatting, but usually it should.
    assert search_criteria.goal is not None, "Goal should be extracted"
    assert "muscle" in search_criteria.goal.lower()
    
    # Verify Equipment
    # SearchCriteria uses equipments_and_facilities list
    facilities = [f.lower() for f in (search_criteria.equipments_and_facilities or [])]
    print(f"Extracted Facilities: {facilities}")
    
    # Assert pool is found
    found_pool = any("pool" in f for f in facilities)
    assert found_pool, f"Expected 'pool' in facilities, got: {facilities}"

    # Verify tool usage trace in messages
    tool_calls = []
    for msg in res["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(tc["name"])
    
    print(f"Tools called: {tool_calls}")
    assert "update_search_state" in tool_calls, "Agent did not call update_search_state"
