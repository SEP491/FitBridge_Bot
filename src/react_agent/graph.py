"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from datetime import UTC, datetime
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime

from react_agent.context import Context
from react_agent.state import InputState, State
from react_agent.subgraphs.execute_gym_recommendation.graph import graph as execute_gym_recommendation_graph
from react_agent.nodes.call_model import call_model
from react_agent.nodes.route_model_output import route_model_output
from react_agent.tools import TOOLS
from react_agent.utils import load_chat_model

tools_node = ToolNode(TOOLS)
builder = StateGraph(State, input_schema=InputState, context_schema=Context)

builder.add_node("tools", tools_node)
builder.add_node("call_model", call_model)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges(
    "call_model",
    route_model_output,
)
builder.add_edge("tools", "call_model")

graph = builder.compile(name="ReAct Agent")
