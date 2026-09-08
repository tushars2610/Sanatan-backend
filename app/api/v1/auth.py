from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.auth import (
    LoginRequest,
    SendOtpRequest,
    SendOtpResponse,
    VerifyOtpRequest,
    TokenResponse,
)
from app.core.dependencies import get_db, get_redis
from app.core.security import create_access_token
from app.db.models.models import User, UserProfile, Persona
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _get_or_create_user(phone_number: str, full_name: str | None, db: AsyncSession) -> tuple[User, bool]:
    """Helper to fetch existing user or create a new user with default profile and persona."""
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    is_new = False

    if not user:
        is_new = True
        user = User(
            phone_number=phone_number,
            full_name=full_name,
            preferred_language="hi",
            timezone="Asia/Kolkata",
        )
        db.add(user)
        await db.flush()

        profile = UserProfile(user_id=user.id)
        db.add(profile)

        canonical_persona = await PersonaService.build_canonical_persona_async(user, profile)
        persona = Persona(
            user_id=user.id,
            completeness_level=0,
            canonical_json=canonical_persona,
        )
        db.add(persona)
        await db.commit()
    elif full_name and not user.full_name:
        user.full_name = full_name
        await db.commit()

    return user, is_new


@router.post("/login", response_model=TokenResponse)
async def direct_login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Direct login endpoint (OTP bypassed).
    Simply pass phone_number to immediately obtain access token and profile.
    """
    user, is_new = await _get_or_create_user(body.phone_number, body.full_name, db)
    token = create_access_token(data={"sub": user.id, "phone": user.phone_number})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        is_new_user=is_new,
    )


@router.post("/send-otp", response_model=SendOtpResponse)
async def send_otp(body: SendOtpRequest):
    """
    Simulated OTP sending endpoint.
    OTP verification is currently bypassed; use default code '123456' or call /login directly.
    """
    return SendOtpResponse(
        success=True,
        message="OTP sent (verification bypassed for development, use 123456 or call /login directly)",
        phone_number=body.phone_number,
        expires_in_seconds=300,
        dev_otp="123456",
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    body: VerifyOtpRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies phone OTP.
    OTP verification is currently bypassed; any OTP code will immediately authenticate.
    """
    user, is_new = await _get_or_create_user(body.phone_number, None, db)
    token = create_access_token(data={"sub": user.id, "phone": user.phone_number})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        is_new_user=is_new,
    )
