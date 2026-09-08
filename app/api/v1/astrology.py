from datetime import date, time
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.schemas.astrology import BirthChartRequest, BirthChartResponse, PanchangResponse
from app.astronomy.engine import VedicAstronomyEngine

router = APIRouter(tags=["Astrology & Panchang"])


@router.get("/content/panchang", response_model=PanchangResponse)
async def get_panchang(
    calc_date: Optional[date] = Query(default=None, description="Date for calculation, defaults to today"),
    calc_time: Optional[time] = Query(default=time(6, 0), description="Local time for calculation, defaults to 06:00:00"),
    latitude: float = Query(default=28.6139, description="Latitude (default New Delhi)"),
    longitude: float = Query(default=77.2090, description="Longitude (default New Delhi)"),
    tz_offset: float = Query(default=5.5, description="UTC timezone offset in hours"),
):
    """Calculate Vedic Panchang for a given date, time, and coordinates using Swiss Ephemeris."""
    target_date = calc_date or date.today()
    panchang = VedicAstronomyEngine.calculate_panchang(
        target_date=target_date,
        target_time=calc_time,
        latitude=latitude,
        longitude=longitude,
        tz_offset_hours=tz_offset,
    )
    return PanchangResponse(success=True, data=panchang)


@router.post("/astrology/birth-chart", response_model=BirthChartResponse)
async def calculate_birth_chart(body: BirthChartRequest):
    """
    Calculate deterministic Vedic birth chart, Rashi, Nakshatra, Pada,
    Tithi, Vara, Yoga, Karana, and Vimshottari Mahadasha sequence.
    """
    chart = VedicAstronomyEngine.calculate_birth_chart(
        birth_date=body.date_of_birth,
        birth_time=body.time_of_birth,
        latitude=body.latitude,
        longitude=body.longitude,
        tz_offset_hours=body.tz_offset_hours,
    )
    return BirthChartResponse(success=True, data=chart)
