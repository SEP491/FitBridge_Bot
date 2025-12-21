from pydantic import BaseModel, Field
from react_agent.domain.criterias import SearchCriteria
from react_agent.domain.entities import UserLocation
from .entities.entities import ExtractedUserCriteria

class InputState(BaseModel):
    """Input state for the extract_user_criteria subgraph."""
    user_query: str = Field(description="The user's query asking for changes.")
    search_criteria: SearchCriteria = Field(default_factory=SearchCriteria) 
    user_location: UserLocation = Field(default_factory=UserLocation)

class State(InputState):
    """State for the extract_user_criteria subgraph."""
    extracted_criteria: ExtractedUserCriteria = Field(default_factory=ExtractedUserCriteria) 
    """Updated user criteria from the user's query."""
    error_code: int = Field(default=0)
    error: str = Field(default="")