import datetime as dt
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full name of user e.g. 'Amit Sharma'")
    phone_number: Optional[str] = Field(default=None, description="Optional phone number, auto-generated if omitted")
    date_of_birth: dt.date = Field(..., description="Date of birth YYYY-MM-DD")
    time_of_birth: dt.time = Field(..., description="Time of birth HH:MM or HH:MM:SS")
    place_of_birth: str = Field(..., min_length=2, description="Place / city of birth e.g. 'Tehri Garhwal', 'Delhi'")
    language: str = Field(default="hi", description="Preferred language code ('hi', 'en', etc.)")
    current_state: str = Field(
        ...,
        description="Life stage: 'Student', 'Early career', 'Building a family', 'Parenting', 'Retired', 'Between chapters'"
    )
    working_hours: str = Field(
        ...,
        description="Occupation / work context e.g. 'Software engineer', 'teacher', 'homemaker', etc."
    )
    deity: str = Field(
        ...,
        description="Chosen deity: 'Shiva', 'Vishnu', 'Devi', 'Ganesha', 'Krishna', 'Hanuman', 'Still discovering'"
    )
    inner_feeling: str = Field(
        ...,
        description="Current emotional state: 'Peaceful', 'Hopeful', 'Restless', 'Searching', 'Heavy', 'Grateful', 'Prefer not to say'"
    )
    seeking: str = Field(
        ...,
        description="Spiritual goal: 'Peace of Mind', 'Clarity', 'Strength', 'Healing'"
    )


class CreateUserResponse(BaseModel):
    success: bool = True
    message: str = "User registered successfully"
    user_id: str


class UserResponse(BaseModel):
    id: str
    phone_number: str
    full_name: Optional[str] = None
    preferred_language: str = "hi"
    timezone: str = "Asia/Kolkata"
    created_at: Optional[dt.datetime] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None


class UserProfileResponse(BaseModel):
    user_id: str
    current_state: Optional[str] = None
    working_hours: Optional[str] = None
    deity: Optional[str] = None
    inner_feeling: Optional[str] = None
    seeking: Optional[str] = None
    primary_concern: Optional[str] = "work"
    faith_level: Optional[str] = "occasional"
    tradition: Optional[str] = "hindu"
    deities: List[str] = Field(default_factory=lambda: ["shiva", "hanuman"])
    current_practices: List[str] = Field(default_factory=lambda: ["prayer", "mantra"])
    daily_time_minutes: int = 10
    life_stage: Optional[str] = "professional"


class UserProfileUpdateRequest(BaseModel):
    current_state: Optional[str] = None
    working_hours: Optional[str] = None
    deity: Optional[str] = None
    inner_feeling: Optional[str] = None
    seeking: Optional[str] = None
    primary_concern: Optional[str] = None
    faith_level: Optional[str] = None
    tradition: Optional[str] = None
    deities: Optional[List[str]] = None
    current_practices: Optional[List[str]] = None
    daily_time_minutes: Optional[int] = None
    life_stage: Optional[str] = None


class BirthProfileRequest(BaseModel):
    date_of_birth: dt.date
    time_of_birth: dt.time
    birth_place: str
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"
    tz_offset_hours: float = 5.5
    is_time_approximate: bool = False


class BirthProfileResponse(BaseModel):
    user_id: str
    date_of_birth: Optional[dt.date] = None
    time_of_birth: Optional[dt.time] = None
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = "Asia/Kolkata"
    has_astrology_calculated: bool = False


class UserListItem(BaseModel):
    id: str
    name: Optional[str] = None
    phone_number: str
    language: str
    timezone: str
    current_state: Optional[str] = None
    working_hours: Optional[str] = None
    deity: Optional[str] = None
    seeking: Optional[str] = None
    created_at: Optional[dt.datetime] = None


class UserListResponse(BaseModel):
    success: bool = True
    total: int
    page: int
    limit: int
    total_pages: int
    items: List[UserListItem]


class UserDetailResponse(BaseModel):
    success: bool = True
    user_id: str
    user: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None
    birth_profile: Optional[Dict[str, Any]] = None
    vedic_astrology: Optional[Dict[str, Any]] = None
    canonical_persona: Optional[Dict[str, Any]] = None


class DeleteUserResponse(BaseModel):
    success: bool = True
    message: str
    deleted_user_id: str
