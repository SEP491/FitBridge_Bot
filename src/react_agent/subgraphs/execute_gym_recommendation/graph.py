from langgraph.graph import StateGraph, START, END
from .state import State, InputState
from .nodes.extract_gym_equipment import extract_gym_equipment
from .nodes.graph_search import graph_search
from .nodes.distance_matrix import distance_matrix
from .nodes.final_scoring import final_scoring
from .nodes.generate_report import generate_report

builder = StateGraph(State, input_schema=InputState)

builder.add_node("extract_gym_equipment", extract_gym_equipment)
builder.add_node("graph_search", graph_search)
builder.add_node("distance_matrix", distance_matrix)
builder.add_node("final_scoring", final_scoring)
builder.add_node("generate_report", generate_report)

builder.add_edge(START, "extract_gym_equipment")
builder.add_edge("extract_gym_equipment", "graph_search")
builder.add_edge("graph_search", "distance_matrix")
builder.add_edge("distance_matrix", "final_scoring")
builder.add_edge("final_scoring", "generate_report")
builder.add_edge("generate_report", END)

graph = builder.compile()