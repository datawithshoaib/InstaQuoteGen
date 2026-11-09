from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db.engine import get_session
from app.services.generation import GenerationService
from app.services.images import BackgroundService
from app.services.posts import PostService

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_generation_service(request: Request, settings: SettingsDep) -> GenerationService:
    return GenerationService(settings=settings, llm=request.app.state.llm)


def get_background_service(request: Request) -> BackgroundService:
    return request.app.state.backgrounds


def get_post_service(
    session: SessionDep,
    settings: SettingsDep,
    backgrounds: Annotated[BackgroundService, Depends(get_background_service)],
) -> PostService:
    return PostService(settings=settings, session=session, backgrounds=backgrounds)


GenerationServiceDep = Annotated[GenerationService, Depends(get_generation_service)]
PostServiceDep = Annotated[PostService, Depends(get_post_service)]
