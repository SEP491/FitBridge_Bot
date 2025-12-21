import pytest
from datetime import datetime, UTC
from react_agent.graph import graph
from react_agent.context import Context
import os
from react_agent.prompts import SYSTEM_PROMPT

@pytest.mark.anyio
async def test_search_criteria_update():
    # 1. User message that SHOULD trigger the tool
    messages = [
        ("user", "I want to build muscle. I am at lat 10.875, lon 106.800. Can you recommend some gyms?"),
    ]
    
    context = Context(
        system_prompt=SYSTEM_PROMPT.format(system_time=datetime.now(tz=UTC).isoformat()),
        model="openai/gpt-4o-mini"
    )

    # 2. Run the agent
    res = await graph.ainvoke({"messages": messages}, context=context)

    # 3. Verify tool usage
    last_message = res["messages"][-1]

    # print("\n--- Agent Messages (Length: {}) ---".format(len(res["messages"])))
    # print(res["messages"])
    # # We expect the agent to either have called the tool or summarized the result
    # assert len(res["messages"]) > 1, "Agent did not perform any actions"
    
    print("--------------------------------initial search")
    print(res)
    assert res["final_report"] is not None, "Main state failed to capture subgraph report"
    print("\n--- Agent Report (Length: {}) ---".format(len(res["final_report"])))
    print(res["final_report"])
    assert res["final_report"].startswith("##")

    messages = [
        ("user", "Actually, I'm looking for a gym with a pool and a sauna.")
    ]   
    res = await graph.ainvoke({"messages": messages}, context=context)

    print("--------------------------------updated search")
    print(res)
    # Check if final_report made it to the main state (Blackbox verification)
    assert res["final_report"] is not None, "Main state failed to capture subgraph report"
    print("\n--- Agent Report (Length: {}) ---".format(len(res["final_report"])))
    print(res["final_report"])
    assert res["final_report"].startswith("##")