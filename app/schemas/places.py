from typing import Optional, List
from pydantic import BaseModel, Field


class PlaceItem(BaseModel):
    name: str
    latitude: float
    longitude: float
    tz_offset_hours: float
    state: Optional[str] = "India"
    country: str = "India"


class PlaceSearchResponse(BaseModel):
    success: bool = True
    count: int
    results: List[PlaceItem]


class PlaceResolveRequest(BaseModel):
    place_name: str = Field(..., min_length=2, description="Place or city name to resolve")


class PlaceResolveResponse(BaseModel):
    success: bool = True
    found: bool
    place: Optional[PlaceItem] = None
