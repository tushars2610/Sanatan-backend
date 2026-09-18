from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.places import router as places_router
from app.api.v1.astrology import router as astrology_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.persona import router as persona_router
from app.api.v1.chat import router as chat_router
from app.api.v1.content import router as content_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter(prefix="/api/v1")

# Mount all feature routers
api_router.include_router(health_router)
api_router.include_router(places_router)
api_router.include_router(astrology_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(persona_router)
api_router.include_router(chat_router)
api_router.include_router(content_router)
api_router.include_router(admin_router)
