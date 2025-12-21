from pydantic import BaseModel, Field
from typing import Optional

class UserLocation(BaseModel):
    latitude: Optional[float] = Field(default=None, description="Latitude of the user's location")
    longitude: Optional[float] = Field(default=None, description="Longitude of the user's location")
class GymAsset(BaseModel):
    name: str = Field(description="Name of the gym")
    address: str = Field(description="Address of the gym")
    latitude: float = Field(description="Latitude of the gym")
    longitude: float = Field(description="Longitude of the gym")
    distance_in_meters: float = Field(description="Distance from user location in meters")
    open_hours: str = Field(description="Opening hours of the gym, e.g. '0700', '1200', '1900'")
    close_hours: str = Field(description="Closing hours of the gym, e.g. '0700', '1200', '1900'")
    price: float = Field(description="Cheapest price of the gym in VND")
    rating: float = Field(description="Rating of the gym")

class PTAsset(BaseModel):
    name: str = Field(description="Name of the PT")
    address: str = Field(description="Address of the PT")
    latitude: float = Field(description="Latitude of the PT")
    longitude: float = Field(description="Longitude of the PT")
    distance_in_meters: int = Field(description="Distance from user location in meters")
    experience_years: int = Field(description="Experience years of the PT")
    gender: str = Field(description="Gender of the PT")
    certificates: list[str] = Field(description="Certificates of the PT")
    price: int = Field(description="Cheapest price of the PT in VND")    # rating: float = Field(description="Rating of the PT")
