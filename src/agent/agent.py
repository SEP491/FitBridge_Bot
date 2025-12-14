import os
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# Package imports (package name is 'agent' -> maps to src/agent/)
from agent import get_model
from agent.utils.conditional_edges.should_continue_gym_retrieval import should_continue_gym_retrieval
from agent.utils.conditional_edges.should_continue import should_continue
from agent.utils.tools.get_gym_details_by_id import get_gym_details_by_id
from agent.utils.tools.get_gym_details_by_name import get_gym_details_by_name
from agent.utils.tools.get_gym_equipments import get_gym_equipments
from agent.utils.tools.get_gym_facilities import get_gym_facilities
from agent.utils.tools.get_gym_reviews_and_ratings import get_gym_reviews_and_ratings
from agent.utils.nodes.modify_criteria.extract_user_criteria import extract_user_criteria
from agent.utils.nodes.modify_criteria.update_user_criteria import update_user_criteria
from agent.utils.nodes.modify_criteria.update_equipment_criteria import update_equipment_criteria
from agent.utils.nodes.assistant_chat.assistant_chat import assistant_chat
from agent.utils.nodes.initial_routing import initial_routing
from agent.utils.nodes.initial_search.process_user_preferences import process_user_preferences
from agent.utils.nodes.initial_search.coarse_gym_retrieval import coarse_gym_retrieval
from agent.utils.nodes.initial_search.calculate_distance_point import calculate_distance_point
from agent.utils.nodes.initial_search.final_scoring import final_scoring
from agent.utils.nodes.initial_search.llm_response import llm_response
from agent.utils.state.MessageState import OverallState, GymsPreferences, PtsPreferences, UserLocation


def get_state_with_checkpoint(graph, config, user_question=None):
    """Load state from checkpoint and merge new user question."""
    checkpointed_state = graph.get_state(config)
    
    if checkpointed_state.values:
        state_dict = dict(checkpointed_state.values)
        if user_question:
            state_dict["user_question"] = user_question
            if state_dict.get("messages") is None:
                state_dict["messages"] = []
            state_dict["messages"].append(HumanMessage(content=user_question))
        return state_dict
    else:
        state = OverallState(user_question=user_question)
        if user_question:
            state.messages = [HumanMessage(content=user_question)]
        return state


def build_graph(checkpointer=None):
    """Build and return the compiled LangGraph."""
    builder = StateGraph(OverallState)
    
    # Tool node
    tool_node = ToolNode(tools=[get_gym_details_by_id, get_gym_details_by_name, get_gym_equipments, get_gym_facilities, get_gym_reviews_and_ratings])
    builder.add_node("tool_node", tool_node)
    
    # Search nodes
    builder.add_node("process_user_preferences", process_user_preferences)
    builder.add_node("coarse_gym_retrieval", coarse_gym_retrieval)
    builder.add_node("calculate_distance_point", calculate_distance_point)
    builder.add_node("final_scoring", final_scoring)
    builder.add_node("llm_response", llm_response)
    
    # Modify criteria nodes
    builder.add_node("extract_user_criteria", extract_user_criteria)
    builder.add_node("update_user_criteria", update_user_criteria)
    builder.add_node("update_equipment_criteria", update_equipment_criteria)
    
    # Chat node
    builder.add_node("assistant_chat", assistant_chat)
    
    # Entry routing
    builder.add_conditional_edges(
        START,
        initial_routing,
        {
            "initial_search": "process_user_preferences",
            "modify_criteria": "extract_user_criteria",
            "assistant_chat": "assistant_chat",
        }
    )
    
    # Modify criteria flow
    builder.add_edge("extract_user_criteria", "update_user_criteria")
    builder.add_edge("update_user_criteria", "update_equipment_criteria")
    builder.add_edge("update_equipment_criteria", "process_user_preferences")
    
    # Search flow
    builder.add_conditional_edges("process_user_preferences", should_continue, {True: "coarse_gym_retrieval", False: END})
    builder.add_conditional_edges("coarse_gym_retrieval", should_continue, {True: "calculate_distance_point", False: END})
    builder.add_conditional_edges("calculate_distance_point", should_continue, {True: "final_scoring", False: END})
    builder.add_conditional_edges("final_scoring", should_continue, {True: "llm_response", False: END})
    builder.add_edge("llm_response", END)
    
    # Assistant chat flow - should_continue returns "tool_node" when there are tool calls
    builder.add_conditional_edges("assistant_chat", should_continue, {
        True: END,           # No tool calls, done
        False: END,          # Error occurred
        "tool_node": "tool_node"  # Has tool calls, execute them
    })
    builder.add_edge("tool_node", "assistant_chat")
    
    return builder.compile()


# ============================================
# EXPORTED GRAPH FOR LANGGRAPH DEV
# Run: langgraph dev --host 0.0.0.0 --port 8123
# ============================================
graph = build_graph()


# ============================================
# TEST CODE - Only runs when executed directly
# ============================================
if __name__ == "__main__":
    from uuid import uuid4
    from langgraph.checkpoint.postgres import PostgresSaver
    
    print(os.environ.get("NEO4J_URI"))
    
    gyms_preferences = GymsPreferences(
        goals="build muscle",
        preferred_equipments=["chest press"],
        distance_in_meters=2000,
        open_hours="00:00:00",
        close_hours="08:00:00",
        max_price=10_000,
        rating=4.5,
    )
    pts_preferences = PtsPreferences(
        distance_in_meters=1000,
        experience_years=10,
        gender="male",
        certificates=["CPT", "NASM", "ACE"],
        max_price=200,
        rating=4.5
    )
    overall_state = OverallState(
        user_question=None,
        gyms_preferences=gyms_preferences,
        pts_preferences=pts_preferences,
        user_location=UserLocation(latitude=10.858253515937571, longitude=106.81163926590125)
    )
    
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Use PostgreSQL checkpointer for persistence
    checkpointer_cm = PostgresSaver.from_conn_string(os.getenv("CHECKPOINTER_DB_URI"))
    checkpointer = checkpointer_cm.__enter__()
    checkpointer.setup()
    test_graph = build_graph(checkpointer)
    
    result = test_graph.invoke(overall_state, config=config)
    print("First result:", result["messages"][-1].content)
    
    follow_up_state = get_state_with_checkpoint(test_graph, config, user_question="what equipments does the first gym have?")
    result = test_graph.invoke(follow_up_state, config=config)
    print("Second result:", result["messages"][-1].content)
