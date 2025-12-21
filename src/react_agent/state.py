"""Define the state structures for the agent."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Sequence, Optional, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated
from react_agent.domain.criterias import SearchCriteria
from react_agent.domain.entities import UserLocation


class InputState(BaseModel):
    """Defines the input state for the agent, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """
    search_criteria: SearchCriteria = Field(default_factory=SearchCriteria)
    """Search criteria for the agent."""
    user_location: UserLocation = Field(default_factory=UserLocation)
    """User's current location"""

    messages: Annotated[Sequence[AnyMessage], add_messages] = Field(
        default_factory=list
    )
    """List of chat messages in the conversation"""


class State(InputState):
    """Represents the complete state of the agent, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    """

    current_step: Literal["start", "update_criteria", "clarification", "graph_search", "distance_matrix", "results", "extract_gym_equipment"] = Field(default="start")
    """Current step of the agent."""
    final_report: str = Field(default="")
    """The final synthesized report from subgraphs to be displayed to the user."""

    is_last_step: IsLastStep = Field(default=False)
    """
    Indicates whether the current step is the last one before the graph raises an error.

    This is a 'managed' variable, controlled by the state machine rather than user code.
    It is set to 'True' when the step count reaches recursion_limit - 1.
    """

    # Additional attributes can be added here as needed.
    # Common examples include:
    # retrieved_documents: List[Document] = field(default_factory=list)
    # extracted_entities: Dict[str, Any] = field(default_factory=dict)
    # api_connections: Dict[str, Any] = field(default_factory=dict)
