from langgraph.types import Command
from asyncio import CancelledError
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
from ..subgraphs.execute_pt_recommendation.graph import graph as pt_recommendation_graph
from ..subgraphs.extract_user_criteria.graph import graph as extract_user_criteria_graph
from ..state import State

def _get_extract_criteria_input(state: State) -> dict:
    """Prepares the input for the user criteria extraction subgraph."""
    return {
        "search_criteria": state.search_criteria,
        "user_location": state.user_location,
        "messages": state.messages
    }


@tool
async def get_pt_recommendations(
    state: Annotated[State, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Executes the full personal trainer (PT) recommendation engine. Requires user location to be set first."""
    
    # Validate location is set
    if not state.user_location or state.user_location.latitude is None or state.user_location.longitude is None:
        return Command(
            update={
                "messages": [ToolMessage(
                    content="Error: User location is not set. Please use 'extract_user_location' tool first to set the user's location, then call this tool again.",
                    tool_call_id=tool_call_id
                )]
            }
        )
    
    try:
        extract_user_criteria_subgraph_input = _get_extract_criteria_input(state)

        extract_user_criteria_subgraph_state = await extract_user_criteria_graph.ainvoke(
            extract_user_criteria_subgraph_input
        )

        updated_search_criteria = extract_user_criteria_subgraph_state.get("search_criteria", None)
        if updated_search_criteria is None:
            return Command(
                update={
                    "messages": [ToolMessage(content="No search criteria provided.", tool_call_id=tool_call_id)]
                }
            )
        
        pt_recommendation_subgraph_input = {
            "search_criteria": updated_search_criteria,
            "user_location": state.user_location,
        }
        pt_recommendation_subgraph_state = await pt_recommendation_graph.ainvoke(
            pt_recommendation_subgraph_input
        )

        return Command(
            update={
                "search_criteria": updated_search_criteria,
                "user_location": state.user_location,
                "final_report": pt_recommendation_subgraph_state.get("final_report", "No report generated."),
                "messages": [ToolMessage(content=pt_recommendation_subgraph_state.get("final_report", "No report generated."), tool_call_id=tool_call_id)]
            }
        )
    except CancelledError:
        print("Graph execution was cancelled gracefully.")
        return Command(
            update={
                "messages": [ToolMessage(
                    content="Search was cancelled. Please try again.",
                    tool_call_id=tool_call_id
                )]
            }
        )

    except Exception as e:
        error_msg = f"PT Recommendation Engine Error: {str(e)}"
        return Command(
            update={
                "messages": [ToolMessage(content=error_msg, tool_call_id=tool_call_id)]
            }
        )

