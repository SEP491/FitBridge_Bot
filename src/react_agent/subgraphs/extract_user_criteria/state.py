from pydantic import BaseModel, Field
from react_agent.domain.criterias import SearchCriteria
from react_agent.domain.entities import UserOrigin
from .entities.entities import ExtractedUserCriteria
from langchain_core.messages import AnyMessage

class InputState(BaseModel):
    """Input state for the extract_user_criteria subgraph."""
    messages: list[AnyMessage] = Field(description="The messages history of the conversation.")
    search_criteria: SearchCriteria = Field(default_factory=SearchCriteria) 
    user_origin: UserOrigin = Field(default_factory=UserOrigin)

class State(InputState):
    """State for the extract_user_criteria subgraph."""
    extracted_criteria: ExtractedUserCriteria = Field(default_factory=ExtractedUserCriteria) 
    """Updated user criteria from the user's query."""
    error_code: int = Field(default=0)
    error: str = Field(default="")