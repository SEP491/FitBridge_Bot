# from langgraph.types import Command
# from asyncio import CancelledError
# from langchain_core.messages import ToolMessage
# from typing import Annotated
# from langchain_core.tools import tool, InjectedToolCallId
# from react_agent.subgraphs.extract_user_criteria.graph import graph as extract_user_criteria_graph
# from react_agent.state import State
# from langgraph.prebuilt import InjectedState
# from react_agent.domain.criterias import SearchCriteria
# @tool 
# async def update_search_state(
#     state: Annotated[State, InjectedState],
#     tool_call_id: Annotated[str, InjectedToolCallId]
# ):
#     """
#     Update the search state with user's query. 
#     Args:
#         state: The current search state.
#     Returns:
#         The updated search state.
#     """
#     try:
#         messages = state.messages
#         user_query = next(
#             (m.content for m in reversed(messages) if m.type == "human"),
#             ""
#         )
        
#         state_dict = state.model_dump()
#         subgraph_input = {
#             "search_criteria": state_dict.get("search_criteria", {}),
#             "user_location": state_dict.get("user_location", {}),
#             "user_query": user_query
#         }

#         final_subgraph_state = await extract_user_criteria_graph.ainvoke(
#             subgraph_input
#         )

            
#         return Command(
#             update={
#                 "search_criteria": SearchCriteria(**final_subgraph_state),
#                 "messages": [
#                     ToolMessage(
#                         content=SearchCriteria(**final_subgraph_state).model_dump_json(), 
#                         tool_call_id=tool_call_id
#                     )
#                 ]
#             }
#         )
#     except CancelledError:
#         print("Update Search State: Graph execution was cancelled gracefully.")

#     except Exception as e:
#         error_msg = f"Update Search State Error: {str(e)}"
#         print(error_msg)
#         return Command(
#             update={
#                 "messages": [ToolMessage(content=error_msg, tool_call_id=tool_call_id)]
#             }
#         )