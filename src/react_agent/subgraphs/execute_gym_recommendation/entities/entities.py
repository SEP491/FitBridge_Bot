from react_agent.domain.entities import GymAsset
from typing import Optional
from pydantic import BaseModel, Field

class ScoreBreakdown(BaseModel):
    distance: Optional[int] = Field(default=None, description="Score for distance")
    equipment: int = Field(description="Score for equipment matching")
    price: int = Field(description="Score for price")
    rating: int = Field(description="Score for rating")
    time: int = Field(description="Score for time")

class RetrievedGymAsset(GymAsset):
    id: str = Field(description="Database ID of the gym")
    score_breakdown: ScoreBreakdown = Field(description="Score breakdown of the gym")
    partial_score: int = Field(description="Partial score of the gym")
    found_equip: Optional[list[str]] = Field(default=None, description="List of user's preferred equipments found in the gym")
    related_recommendations: Optional[list[str]] = Field(default=None, description="List of related equipments found in the gym")
    final_score: Optional[int] = Field(default=None, description="Final score of the gym")
    real_distance: Optional[float] = Field(default=None, description="Real distance in meters")
    real_duration_min: Optional[float] = Field(default=None, description="Real duration in minutes")
