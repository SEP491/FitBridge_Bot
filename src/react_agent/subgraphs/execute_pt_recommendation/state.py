from pydantic import BaseModel, Field
from react_agent.domain.criterias import SearchCriteria
from react_agent.domain.entities import UserLocation, GymAsset, PTAsset
from typing import Union

class InputState(BaseModel):
    """Input state for the execute_gym_recommendation subgraph."""
    search_criteria: SearchCriteria = Field(default_factory=SearchCriteria) 
    user_location: UserLocation = Field(default_factory=UserLocation)

class State(InputState):
    """State for the execute_gym_recommendation subgraph."""
    candidates: list[Union[GymAsset, PTAsset]] = Field(default_factory=list)
    final_candidates: list[Union[GymAsset, PTAsset]] = Field(default_factory=list)
    distances: list[float] = Field(default_factory=list)
    final_report: str = Field(default="")
    error_code: int = Field(default=0)
    error: str = Field(default="")
    """The final synthesized report from subgraphs to be displayed to the user."""
