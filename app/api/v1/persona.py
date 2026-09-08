from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, get_current_user
from app.db.models.models import User, UserProfile, BirthProfile, Persona
from app.schemas.persona import PersonaResponse, PersonaGenerateRequest
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/persona", tags=["Spiritual Persona"])


@router.get("/{user_id}", response_model=PersonaResponse)
async def get_persona(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current Canonical SpiritualSakha Persona JSON for the specified user."""
    u_res = await db.execute(select(User).where(User.id == user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(Persona).where(Persona.user_id == user_id))
    persona = result.scalar_one_or_none()

    if not persona:
        # Build initial
        p_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        prof = p_res.scalar_one_or_none()
        canonical = await PersonaService.build_canonical_persona_async(user, prof)
        persona = Persona(user_id=user_id, completeness_level=0, canonical_json=canonical)
        db.add(persona)
        await db.commit()

    return PersonaResponse(
        user_id=user_id,
        persona_version=persona.persona_version,
        completeness_level=persona.completeness_level,
        canonical_persona=persona.canonical_json,
    )


@router.post("/{user_id}/generate", response_model=PersonaResponse)
async def generate_persona(
    user_id: str,
    body: PersonaGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate the Canonical SpiritualSakha Persona JSON from the latest user profile & birth chart data."""
    u_res = await db.execute(select(User).where(User.id == user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    p_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    prof = p_res.scalar_one_or_none()

    b_res = await db.execute(
        select(BirthProfile)
        .options(selectinload(BirthProfile.astrology_snapshot))
        .where(BirthProfile.user_id == user_id)
    )
    bp = b_res.scalar_one_or_none()
    snapshot = bp.astrology_snapshot if bp else None

    canonical = await PersonaService.build_canonical_persona_async(user, prof, bp, snapshot)

    per_res = await db.execute(select(Persona).where(Persona.user_id == user_id))
    persona = per_res.scalar_one_or_none()
    if not persona:
        persona = Persona(user_id=user_id)
        db.add(persona)

    persona.completeness_level = canonical.get("completenessLevel", 0)
    persona.canonical_json = canonical
    await db.commit()

    return PersonaResponse(
        user_id=user_id,
        persona_version=persona.persona_version,
        completeness_level=persona.completeness_level,
        canonical_persona=persona.canonical_json,
    )
