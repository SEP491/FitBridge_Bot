from pydantic import BaseModel, Field
from typing import List, Optional

class SearchCriteria(BaseModel):
    """Business logic: What defines a valid search?"""
    goal: Optional[str] = None
    equipments_and_facilities: set[str] = Field(default_factory=set)
    certificates: set[str] = Field(default_factory=set)
    distance_in_meters: int = 5000
    max_price: Optional[int] = None
    rating: Optional[float] = None
    gender: Optional[str] = None
    min_experience_years: Optional[int] = None
    open_hours: Optional[str] = None
    close_hours: Optional[str] = None

    def is_valid(self) -> bool:
        """The 'Business Rule': User must provide at least one criteria."""
        return any([self.goal, self.equipments_and_facilities, self.certificates])