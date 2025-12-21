import pytest
from react_agent.subgraphs.execute_gym_recommendation.graph import graph as subgraph
from react_agent.domain.criterias import SearchCriteria
from react_agent.domain.entities import UserLocation

@pytest.mark.anyio
async def test_subgraph_execution():
    # 1. Setup Mock Input
    input_state = {
        "search_criteria": SearchCriteria(
            goal="Build muscle and strength",
            distance_in_meters=5000
        ),
        "user_location": UserLocation(
            latitude=10.875, 
            longitude=106.800
        )
    }

    # 2. Invoke the Subgraph
    # We use ainvoke because LangGraph is natively async
    final_state = await subgraph.ainvoke(input_state)

    # 3. Architect's Verification
    assert "final_report" in final_state, "Subgraph failed to produce a final_report"
    assert len(final_state["final_report"]) > 0, "Final report is empty"
    assert "🏋️" in final_state["final_report"], "Report is missing visual formatting"
    
    print(final_state)
    print("\n--- Generated Subgraph Report (Length: {}) ---".format(len(final_state["final_report"])))
    # We avoid printing the raw string to prevent UnicodeEncodeError on some Windows terminals
    # but we can check if it looks correct
    assert final_state["final_report"].startswith("##")