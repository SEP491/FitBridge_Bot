from pydantic import BaseModel, Field
from typing import Optional, Union

class NumberUpdate(BaseModel):
    """For fields like Max Price, Distance, and Rating (can be ints or floats)."""
    # Use Union for flexibility, but int/float for numeric fields
    absolute_change: Optional[Union[int, float]] = Field(default=None, description="The new exact numeric value.")
    relative_change: Optional[Union[int, float]] = Field(default=None, description="The amount to add or subtract (e.g., 500 or -500).")

class TimeUpdate(BaseModel):
    """For time fields (Open/Close Hours)."""
    absolute_change: Optional[str] = Field(default=None, description="The new exact time string (HH:MM:SS).")
    relative_change: Optional[str] = Field(default=None, description="The relative time duration string to add/subtract (e.g., '+01:00:00' or '-3600 seconds').")

class UpdateOperations(BaseModel):
    """Operations for updating list fields - add items, remove items, or both."""
    overwrite: Optional[list[str]] = Field(default=None, description="List of items to overwrite the existing list")
    add: Optional[list[str]] = Field(default=None, description="List of items to add to the existing list")
    remove: Optional[list[str]] = Field(default=None, description="List of items to remove from the existing list")

class ExtractedUserCriteria(BaseModel):
    """Schema for initial extraction - all fields extracted from user query."""
    training_goal: Optional[str] = Field(default=None, description="User's training goals (body part or fitness goal)")
    equipments_and_facilities: Optional[UpdateOperations] = Field(default=None, description="Update operations for preferred gym equipments and facilities, with add or remove operations")
    distance_in_meters: Optional[NumberUpdate] = Field(default=None, description="Maximum distance in meters from user's location")
    open_hours: Optional[TimeUpdate] = Field(default=None, description="Preferred opening hours in HH:MM:SS format")
    close_hours: Optional[TimeUpdate] = Field(default=None, description="Preferred closing hours in HH:MM:SS format")
    max_price: Optional[NumberUpdate] = Field(default=None, description="Maximum price user is willing to pay in VND currency")
    rating: Optional[NumberUpdate] = Field(default=None, description="Minimum rating requirement (0.0 to 5.0)")
    gender: Optional[str] = Field(default=None, description="Preferred gender of the trainer")
    min_experience_years: Optional[NumberUpdate] = Field(default=None, description="Minimum years of experience for the trainer")
    certificates: Optional[UpdateOperations] = Field(default=None, description="Update operations for preferred trainer certificates")