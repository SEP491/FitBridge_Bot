from langgraph.graph import StateGraph, START, END
from .state import State, InputState
from .nodes.extract_user_criteria import extract_user_criteria
from .nodes.update_user_criteria import update_user_criteria

builder = StateGraph(State, input_schema=InputState)

builder.add_node("extract_user_criteria", extract_user_criteria)
builder.add_node("update_user_criteria", update_user_criteria)

builder.add_edge(START, "extract_user_criteria")
builder.add_edge("extract_user_criteria", "update_user_criteria")
builder.add_edge("update_user_criteria", END)

graph = builder.compile()