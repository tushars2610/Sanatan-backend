import datetime as dt
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PanchangQuery(BaseModel):
    calc_date: Optional[dt.date] = Field(default=None, description="Date for calculation, defaults to today")
    calc_time: Optional[dt.time] = Field(default=dt.time(6, 0), description="Local time for calculation, defaults to 06:00")
    latitude: float = Field(default=28.6139, description="Latitude (default: New Delhi)")
    longitude: float = Field(default=77.2090, description="Longitude (default: New Delhi)")
    tz_offset_hours: float = Field(default=5.5, description="UTC timezone offset in hours")


class BirthChartRequest(BaseModel):
    date_of_birth: dt.date = Field(..., description="Birth date YYYY-MM-DD")
    time_of_birth: dt.time = Field(..., description="Birth time HH:MM or HH:MM:SS")
    place_name: Optional[str] = Field(default=None, description="Birth place name")
    latitude: float = Field(..., description="Latitude e.g. 28.6139")
    longitude: float = Field(..., description="Longitude e.g. 77.2090")
    tz_offset_hours: float = Field(default=5.5, description="Timezone offset in hours e.g. 5.5 for IST")


class PanchangResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]


class BirthChartResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
