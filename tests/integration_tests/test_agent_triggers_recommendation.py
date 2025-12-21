import pytest
from react_agent.domain.entities import UserLocation
from react_agent.graph import graph
from react_agent.context import Context
import os

@pytest.mark.anyio
async def test_agent_triggers_recommendation():
    # 1. User message that SHOULD trigger the tool
    messages = [
        ("user", "Hi, can you recommend some gyms? ")
    ]
    
    context = Context(
        system_prompt="You are a fitness assistant. Use the 'get_gym_recommendations' tool when you have goals and location.",
        model="openai/gpt-4o-mini"
    )

    # 2. Run the agent
    res = await graph.ainvoke({"messages": messages, "user_location": UserLocation(latitude=10.875, longitude=106.800)}, context=context)

    # 3. Verify tool usage
    last_message = res["messages"][-1]

    # print("\n--- Agent Messages (Length: {}) ---".format(len(res["messages"])))
    # print(res["messages"])
    # # We expect the agent to either have called the tool or summarized the result
    # assert len(res["messages"]) > 1, "Agent did not perform any actions"
    
    print("--------------------------------dorara")
    print(res)
    # Check if final_report made it to the main state (Blackbox verification)
    assert res["final_report"] is not None, "Main state failed to capture subgraph report"
    print("\n--- Agent Report (Length: {}) ---".format(len(res["final_report"])))
    print(res["final_report"])
    # We avoid printing the raw string to prevent UnicodeEncodeError on some Windows terminals
    # but we can check if it looks correct
    assert res["final_report"].startswith("##")