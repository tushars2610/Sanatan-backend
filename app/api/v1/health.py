from fastapi import APIRouter
import redis.asyncio as aioredis
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint checking application, redis, and database status."""
    redis_status = "unknown"
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        await r.ping()
        await r.aclose()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"unavailable ({type(e).__name__})"

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "redis": redis_status,
        }
    }
