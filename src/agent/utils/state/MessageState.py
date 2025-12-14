from typing import Optional, Annotated, Literal, Union
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# this will be the overall state of the chatbot, storing user's preferences and other information

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

class UserLocation(BaseModel):
    latitude: float = Field(description="Latitude of the user's location")
    longitude: float = Field(description="Longitude of the user's location")

class GymsPreferences(BaseModel):
    preferred_equipments: Optional[list[str]] = Field(default=None, description="List of preferred gym equipments")
    goals: Optional[str] = Field(default=None, description="User's fitness goals")
    max_price: Optional[int] = Field(default=None, description="Maximum price in local currency")
    rating: Optional[float] = Field(default=None, description="Minimum rating score, e.g. 4.5")
    distance_in_meters: Optional[int] = Field(default=None, description="Maximum distance from user location")
    open_hours: Optional[str] = Field(default=None, description="Opening hours of the gym, e.g. '0700', '1200', '1900'")
    close_hours: Optional[str] = Field(default=None, description="Closing hours of the gym, e.g. '0700', '1200', '1900'")

class PtsPreferences(BaseModel):
    distance_in_meters: Optional[int] = Field(default=None, description="Maximum distance from user location")
    experience_years: Optional[int] = Field(default=None, description="Minimum years of experience")
    gender: Optional[str] = Field(default=None, description="Preferred gender of the PT")
    certificates: Optional[list[str]] = Field(default=None, description="Required certificates, e.g. 'CPT', 'NASM', 'ACE'")
    max_price: Optional[int] = Field(default=None, description="Maximum price in local currency")
    rating: Optional[float] = Field(default=None, description="Minimum rating score, e.g. 4.5")

class Gym(BaseModel):
    name: str = Field(description="Name of the gym")
    address: str = Field(description="Address of the gym")
    latitude: float = Field(description="Latitude of the gym")
    longitude: float = Field(description="Longitude of the gym")
    distance_in_meters: int = Field(description="Distance from user location in meters")
    open_hours: str = Field(description="Opening hours of the gym, e.g. '0700', '1200', '1900'")
    close_hours: str = Field(description="Closing hours of the gym, e.g. '0700', '1200', '1900'")

class ScoreBreakdown(BaseModel):
    distance: Optional[int] = Field(default=None, description="Score for distance")
    equipment: int = Field(description="Score for equipment")
    price: int = Field(description="Score for price")
    rating: int = Field(description="Score for rating")
    time: int = Field(description="Score for time")

class RetrievedGyms(BaseModel):
    id: str = Field(description="ID of the gym")
    name: str = Field(description="Name of the gym")
    address: str = Field(description="Address of the gym")
    open_hours: str = Field(description="Opening hours of the gym, e.g. 0700, 1200, 1900")
    close_hours: str = Field(description="Closing hours of the gym, e.g. '0700', '1200', '1900'")
    price: int = Field(description="Price of the gym in VND currency")
    rating: float = Field(description="Rating of the gym")
    lat: float = Field(description="Latitude of the gym")
    lon: float = Field(description="Longitude of the gym")
    dist_meters: float = Field(description="Distance from user location in meters")
    score_breakdown: ScoreBreakdown = Field(description="Score breakdown of the gym")
    partial_score: int = Field(description="Partial score of the gym")
    found_equip: Optional[list[str]] = Field(default=None, description="List of user's preferred equipments found in the gym")
    real_distance: Optional[int] = Field(default=None, description="Real distance from user location in meters")
    real_duration_min: Optional[float] = Field(default=None, description="Real duration from user location in minutes")
    final_score: Optional[int] = Field(default=None, description="Final score of the gym")


class ExtractedUserCriteria(BaseModel):
    """Schema for initial extraction - all fields extracted from user query."""
    training_goal: Optional[str] = Field(default=None, description="User's training goals (body part or fitness goal)")
    equipments_and_facilities: Optional[UpdateOperations] = Field(default=None, description="Update operations for preferred gym equipments and facilities, with add or remove operations")
    distance_in_meters: Optional[NumberUpdate] = Field(default=None, description="Maximum distance in meters from user's location")
    open_hours: Optional[TimeUpdate] = Field(default=None, description="Preferred opening hours in HH:MM:SS format")
    close_hours: Optional[TimeUpdate] = Field(default=None, description="Preferred closing hours in HH:MM:SS format")
    max_price: Optional[NumberUpdate] = Field(default=None, description="Maximum price user is willing to pay in VND currency")
    rating: Optional[NumberUpdate] = Field(default=None, description="Minimum rating requirement (0.0 to 5.0)")

class OverallState(BaseModel):
    extracted_criteria: Optional[ExtractedUserCriteria] = Field(default=None, description="Extracted user criteria from the user's query")
    route_decision: Optional[Literal["modify_criteria", "inspect_results", "general_chat"]] =  Field(default=None, description="Route decision of the user's query")
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list, description="List of chat messages in the conversation")
    user_question: Optional[str] = Field(default=None, description="The user's original question")
    gyms_preferences: Optional[GymsPreferences] = Field(default=None, description="User's gym search preferences")
    pts_preferences: Optional[PtsPreferences] = Field(default=None, description="User's personal trainer search preferences")
    user_location: Optional[UserLocation] = Field(default=None, description="User's current location coordinates")
    candidate_gyms: list[RetrievedGyms] = Field(default_factory=list, description="List of candidate gyms from coarse retrieval")
    final_gyms: list[RetrievedGyms] = Field(default_factory=list, description="Final ranked list of gyms that satisfy the user's preferences after scoring")
    found_equip: Optional[list[str]] = Field(default=None, description="List of found equipments in the gym")
    error: Optional[str] = Field(default=None, description="Error message if any step fails")
    error_code: Optional[int] = Field(default=None, description="HTTP-style error code (200=success, 400=bad request, etc.)")
