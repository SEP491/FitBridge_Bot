from react_agent.domain.entities import PTAsset
from typing import Optional
from pydantic import BaseModel, Field

class ScoreBreakdown(BaseModel):
    distance: Optional[int] = Field(default=None, description="Score for distance")
    certificates: int = Field(description="Score for certificate matching")
    price: int = Field(description="Score for price")

class RetrievedPtAsset(PTAsset):
    id: str = Field(description="Database ID of the PT")
    score_breakdown: ScoreBreakdown = Field(description="Score breakdown of the PT")
    partial_score: int = Field(description="Partial score of the PT")
    found_certificates: Optional[list[str]] = Field(default=None, description="List of user's preferred certificates found in the PT")
    final_score: Optional[int] = Field(default=None, description="Final score of the PT")
    real_distance: Optional[float] = Field(default=None, description="Real distance in meters")
    real_duration_min: Optional[float] = Field(default=None, description="Real travel duration in minutes")