from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.db.models.models import User

settings = get_settings()
security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis():
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    # Authentication bypassed for now
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            phone_number="+919000000000",
            full_name="Dummy User",
            preferred_language="hi",
            timezone="Asia/Kolkata",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
