import math
import random
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, get_current_user
from app.core.security import create_access_token
from app.db.models.models import User, UserProfile, BirthProfile, AstrologySnapshot, Persona
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    UserResponse,
    UserUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
    BirthProfileRequest,
    BirthProfileResponse,
    UserListItem,
    UserListResponse,
    UserDetailResponse,
    DeleteUserResponse,
)
from app.astronomy.engine import VedicAstronomyEngine
from app.services.place_service import PlaceService
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/user", tags=["User & Profile"])


# ---------------------------------------------------------------------------
# 1. Create New User
# ---------------------------------------------------------------------------
@router.post("/create", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Onboard and register a new user with full spiritual & birth context.
    Persists data in PostgreSQL and returns only user_id and a confirmation message.
    """
    # 1. Resolve phone number
    phone = body.phone_number
    if not phone:
        phone = f"+919{random.randint(100000000, 999999999)}"

    # Check if user already exists
    res = await db.execute(select(User).where(User.phone_number == phone))
    user = res.scalar_one_or_none()
    if not user:
        user = User(
            phone_number=phone,
            full_name=body.name,
            preferred_language=body.language,
            timezone="Asia/Kolkata",
        )
        db.add(user)
        await db.flush()
    else:
        user.full_name = body.name
        user.preferred_language = body.language

    # 2. Resolve place coordinates automatically from place_of_birth
    resolved_place = PlaceService.resolve(body.place_of_birth)
    if resolved_place:
        lat = resolved_place.latitude
        lon = resolved_place.longitude
        tz_offset = resolved_place.tz_offset_hours
    else:
        search_results = PlaceService.search(body.place_of_birth)
        if search_results:
            lat = search_results[0].latitude
            lon = search_results[0].longitude
            tz_offset = search_results[0].tz_offset_hours
        else:
            lat = 28.6139
            lon = 77.2090
            tz_offset = 5.5

    # 3. Create or update Birth Profile
    b_res = await db.execute(select(BirthProfile).where(BirthProfile.user_id == user.id))
    bp = b_res.scalar_one_or_none()
    if not bp:
        bp = BirthProfile(user_id=user.id)
        db.add(bp)

    bp.date_of_birth = body.date_of_birth
    bp.time_of_birth = body.time_of_birth
    bp.birth_place = body.place_of_birth
    bp.latitude = lat
    bp.longitude = lon
    bp.timezone = "Asia/Kolkata"
    await db.flush()

    # 4. Calculate deterministic Vedic Astrology with Swiss Ephemeris
    astro_data = VedicAstronomyEngine.calculate_birth_chart(
        birth_date=body.date_of_birth,
        birth_time=body.time_of_birth,
        latitude=lat,
        longitude=lon,
        tz_offset_hours=tz_offset,
    )

    s_res = await db.execute(select(AstrologySnapshot).where(AstrologySnapshot.birth_profile_id == bp.id))
    snapshot = s_res.scalar_one_or_none()
    if not snapshot:
        snapshot = AstrologySnapshot(birth_profile_id=bp.id)
        db.add(snapshot)

    snapshot.rashi = astro_data["rashi"]
    snapshot.nakshatra = astro_data["nakshatra"]
    snapshot.panchang_data = astro_data["panchang"]
    snapshot.dasha_data = astro_data["dasha"]
    await db.flush()

    # 5. Create or update UserProfile with onboarding context
    p_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = p_res.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile.current_state = body.current_state
    profile.working_hours = body.working_hours
    profile.deity = body.deity
    profile.inner_feeling = body.inner_feeling
    profile.seeking = body.seeking
    profile.primary_concern = body.seeking
    profile.life_stage = body.current_state
    profile.deities = [body.deity.lower()] if body.deity else ["shiva", "hanuman"]
    profile.current_practices = ["prayer", "mindful reflection"]
    profile.daily_time_minutes = 10
    await db.flush()

    # 6. Generate and save Canonical Spiritual Persona JSON
    canonical_persona = await PersonaService.build_canonical_persona_async(user, profile, bp, snapshot)

    per_res = await db.execute(select(Persona).where(Persona.user_id == user.id))
    persona_row = per_res.scalar_one_or_none()
    if not persona_row:
        persona_row = Persona(user_id=user.id)
        db.add(persona_row)

    persona_row.completeness_level = canonical_persona["completenessLevel"]
    persona_row.canonical_json = canonical_persona

    await db.commit()

    return CreateUserResponse(
        success=True,
        message="User registered successfully",
        user_id=user.id,
    )


# ---------------------------------------------------------------------------
# 2. Get All Users (with Pagination and Search)
# ---------------------------------------------------------------------------
@router.get("/list", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Optional search term for name or phone number"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all users' basic details with pagination and optional search.
    """
    query = (
        select(User, UserProfile)
        .outerjoin(UserProfile, User.id == UserProfile.user_id)
    )

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.full_name.ilike(search_pattern),
                User.phone_number.ilike(search_pattern),
            )
        )

    # Count total
    count_query = select(func.count(User.id))
    if search:
        search_pattern = f"%{search.strip()}%"
        count_query = count_query.where(
            or_(
                User.full_name.ilike(search_pattern),
                User.phone_number.ilike(search_pattern),
            )
        )
    total_count_res = await db.execute(count_query)
    total = total_count_res.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    paged_query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    rows_res = await db.execute(paged_query)
    rows = rows_res.all()

    items = []
    for user_row, profile_row in rows:
        items.append(
            UserListItem(
                id=user_row.id,
                name=user_row.full_name,
                phone_number=user_row.phone_number,
                language=user_row.preferred_language,
                timezone=user_row.timezone,
                current_state=profile_row.current_state if profile_row else None,
                working_hours=profile_row.working_hours if profile_row else None,
                deity=profile_row.deity if profile_row else None,
                seeking=profile_row.seeking if profile_row else None,
                created_at=user_row.created_at,
            )
        )

    total_pages = math.ceil(total / limit) if total > 0 else 1

    return UserListResponse(
        success=True,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=items,
    )


# ---------------------------------------------------------------------------
# Current Authenticated User Endpoints
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_my_info(user: User = Depends(get_current_user)):
    """Retrieve current authenticated user's details."""
    return UserResponse(
        id=user.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        preferred_language=user.preferred_language,
        timezone=user.timezone,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_my_info(
    body: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile information."""
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.preferred_language is not None:
        user.preferred_language = body.preferred_language
    if body.timezone is not None:
        user.timezone = body.timezone

    await db.commit()
    await db.refresh(user)
    return UserResponse(
        id=user.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        preferred_language=user.preferred_language,
        timezone=user.timezone,
        created_at=user.created_at,
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve spiritual preferences and practices profile."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()

    return UserProfileResponse(
        user_id=user.id,
        current_state=profile.current_state,
        working_hours=profile.working_hours,
        deity=profile.deity,
        inner_feeling=profile.inner_feeling,
        seeking=profile.seeking,
        primary_concern=profile.primary_concern,
        faith_level=profile.faith_level,
        tradition=profile.tradition,
        deities=profile.deities,
        current_practices=profile.current_practices,
        daily_time_minutes=profile.daily_time_minutes,
        life_stage=profile.life_stage,
    )


@router.patch("/profile", response_model=UserProfileResponse)
async def update_my_profile(
    body: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update spiritual practices, concerns, and deities."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    if body.current_state is not None:
        profile.current_state = body.current_state
    if body.working_hours is not None:
        profile.working_hours = body.working_hours
    if body.deity is not None:
        profile.deity = body.deity
    if body.inner_feeling is not None:
        profile.inner_feeling = body.inner_feeling
    if body.seeking is not None:
        profile.seeking = body.seeking
    if body.primary_concern is not None:
        profile.primary_concern = body.primary_concern
    if body.faith_level is not None:
        profile.faith_level = body.faith_level
    if body.tradition is not None:
        profile.tradition = body.tradition
    if body.deities is not None:
        profile.deities = body.deities
    if body.current_practices is not None:
        profile.current_practices = body.current_practices
    if body.daily_time_minutes is not None:
        profile.daily_time_minutes = body.daily_time_minutes
    if body.life_stage is not None:
        profile.life_stage = body.life_stage

    await db.commit()
    await db.refresh(profile)
    return UserProfileResponse(
        user_id=user.id,
        current_state=profile.current_state,
        working_hours=profile.working_hours,
        deity=profile.deity,
        inner_feeling=profile.inner_feeling,
        seeking=profile.seeking,
        primary_concern=profile.primary_concern,
        faith_level=profile.faith_level,
        tradition=profile.tradition,
        deities=profile.deities,
        current_practices=profile.current_practices,
        daily_time_minutes=profile.daily_time_minutes,
        life_stage=profile.life_stage,
    )


@router.get("/birth-profile", response_model=BirthProfileResponse)
async def get_birth_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's birth data and calculation status."""
    result = await db.execute(
        select(BirthProfile)
        .options(selectinload(BirthProfile.astrology_snapshot))
        .where(BirthProfile.user_id == user.id)
    )
    bp = result.scalar_one_or_none()
    if not bp:
        return BirthProfileResponse(user_id=user.id, has_astrology_calculated=False)

    return BirthProfileResponse(
        user_id=user.id,
        date_of_birth=bp.date_of_birth,
        time_of_birth=bp.time_of_birth,
        birth_place=bp.birth_place,
        latitude=bp.latitude,
        longitude=bp.longitude,
        timezone=bp.timezone,
        has_astrology_calculated=bp.astrology_snapshot is not None,
    )


@router.put("/birth-profile", response_model=BirthProfileResponse)
async def set_birth_profile(
    body: BirthProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save birth details and automatically compute Swiss Ephemeris Vedic Astrology snapshot,
    then regenerate the user's Canonical Spiritual Persona.
    """
    result = await db.execute(select(BirthProfile).where(BirthProfile.user_id == user.id))
    bp = result.scalar_one_or_none()
    if not bp:
        bp = BirthProfile(user_id=user.id)
        db.add(bp)

    bp.date_of_birth = body.date_of_birth
    bp.time_of_birth = body.time_of_birth
    bp.birth_place = body.birth_place
    bp.latitude = body.latitude
    bp.longitude = body.longitude
    bp.timezone = body.timezone
    bp.is_time_approximate = body.is_time_approximate

    await db.flush()

    # Calculate Vedic Chart
    astro_data = VedicAstronomyEngine.calculate_birth_chart(
        birth_date=body.date_of_birth,
        birth_time=body.time_of_birth,
        latitude=body.latitude,
        longitude=body.longitude,
        tz_offset_hours=body.tz_offset_hours,
    )

    s_res = await db.execute(select(AstrologySnapshot).where(AstrologySnapshot.birth_profile_id == bp.id))
    snapshot = s_res.scalar_one_or_none()
    if not snapshot:
        snapshot = AstrologySnapshot(birth_profile_id=bp.id)
        db.add(snapshot)

    snapshot.rashi = astro_data["rashi"]
    snapshot.nakshatra = astro_data["nakshatra"]
    snapshot.panchang_data = astro_data["panchang"]
    snapshot.dasha_data = astro_data["dasha"]

    await db.flush()

    # Regenerate persona
    p_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = p_result.scalar_one_or_none()

    canonical = await PersonaService.build_canonical_persona_async(user, profile, bp, snapshot)

    per_res = await db.execute(select(Persona).where(Persona.user_id == user.id))
    persona_row = per_res.scalar_one_or_none()
    if not persona_row:
        persona_row = Persona(user_id=user.id)
        db.add(persona_row)

    persona_row.completeness_level = canonical["completenessLevel"]
    persona_row.canonical_json = canonical

    await db.commit()

    return BirthProfileResponse(
        user_id=user.id,
        date_of_birth=bp.date_of_birth,
        time_of_birth=bp.time_of_birth,
        birth_place=bp.birth_place,
        latitude=bp.latitude,
        longitude=bp.longitude,
        timezone=bp.timezone,
        has_astrology_calculated=True,
    )


# ---------------------------------------------------------------------------
# 3. Get a User's Complete Details by User ID
# ---------------------------------------------------------------------------
@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_details_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all details of a specific user by their user_id:
    - Basic user details
    - Spiritual & onboarding profile
    - Birth profile & coordinates
    - Swiss Ephemeris Vedic astrology snapshot (Rashi, Nakshatra, Dasha)
    - Canonical Persona JSON
    """
    query = (
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.birth_profile).selectinload(BirthProfile.astrology_snapshot),
            selectinload(User.persona),
        )
        .where(User.id == user_id)
    )
    res = await db.execute(query)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    # Serialize profile
    profile_data = None
    if user.profile:
        p = user.profile
        profile_data = {
            "currentState": p.current_state,
            "workingHours": p.working_hours,
            "deity": p.deity,
            "innerFeeling": p.inner_feeling,
            "seeking": p.seeking,
            "primaryConcern": p.primary_concern,
            "faithLevel": p.faith_level,
            "tradition": p.tradition,
            "deities": p.deities,
            "currentPractices": p.current_practices,
            "dailyTimeMinutes": p.daily_time_minutes,
            "lifeStage": p.life_stage,
        }

    # Serialize birth profile & astrology
    birth_data = None
    astro_data = None
    if user.birth_profile:
        bp = user.birth_profile
        birth_data = {
            "dateOfBirth": bp.date_of_birth.isoformat() if bp.date_of_birth else None,
            "timeOfBirth": bp.time_of_birth.isoformat() if bp.time_of_birth else None,
            "birthPlace": bp.birth_place,
            "latitude": bp.latitude,
            "longitude": bp.longitude,
            "timezone": bp.timezone,
            "isTimeApproximate": bp.is_time_approximate,
        }
        if bp.astrology_snapshot:
            snap = bp.astrology_snapshot
            astro_data = {
                "rashi": snap.rashi,
                "nakshatra": snap.nakshatra,
                "panchang": snap.panchang_data,
                "dasha": snap.dasha_data,
                "calculatedAt": snap.calculated_at.isoformat() if snap.calculated_at else None,
            }

    # Serialize canonical persona
    persona_data = None
    if user.persona:
        persona_data = {
            "personaVersion": user.persona.persona_version,
            "completenessLevel": user.persona.completeness_level,
            "generatedAt": user.persona.generated_at.isoformat() if user.persona.generated_at else None,
            "canonicalJson": user.persona.canonical_json,
        }

    return UserDetailResponse(
        success=True,
        user_id=user.id,
        user={
            "id": user.id,
            "name": user.full_name,
            "phone_number": user.phone_number,
            "preferred_language": user.preferred_language,
            "timezone": user.timezone,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        },
        profile=profile_data,
        birth_profile=birth_data,
        vedic_astrology=astro_data,
        canonical_persona=persona_data,
    )


# ---------------------------------------------------------------------------
# 4. Delete User by User ID
# ---------------------------------------------------------------------------
@router.delete("/{user_id}", response_model=DeleteUserResponse)
async def delete_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user and cascade delete all their associated data:
    - User profile
    - Birth profile & astrology snapshots
    - Personas
    - Conversations & chat messages
    """
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    await db.delete(user)
    await db.commit()

    return DeleteUserResponse(
        success=True,
        message=f"User '{user_id}' and all associated records deleted successfully",
        deleted_user_id=user_id,
    )
