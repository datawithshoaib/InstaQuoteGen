from fastapi import APIRouter

from app.api.routes import generations, media, quotes, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(quotes.router)
api_router.include_router(generations.router)
api_router.include_router(media.router)
