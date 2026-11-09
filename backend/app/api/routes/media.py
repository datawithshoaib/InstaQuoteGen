from typing import Annotated

from fastapi import APIRouter, Query, status
from fastapi.responses import FileResponse

from app.api.deps import PostServiceDep, SessionDep, SettingsDep
from app.core.errors import NotFoundError
from app.db.models import Background
from app.repositories.media import PostRepository
from app.schemas import Page
from app.schemas.media import BackgroundRead, BackgroundRequest, Credit, PostCreate, PostRead

router = APIRouter(tags=["media"])


def _background_read(bg: Background) -> BackgroundRead:
    credit = (
        Credit(name=bg.photographer_name, profile_url=bg.photographer_url, photo_url=bg.photo_url)
        if bg.photographer_name
        else None
    )
    return BackgroundRead(
        id=bg.id,
        source=bg.source,
        aspect_ratio=bg.aspect_ratio,
        width=bg.width,
        height=bg.height,
        palette=bg.palette,
        keywords=bg.keywords,
        url=f"/media/backgrounds/{bg.filename}",
        credit=credit,
    )


@router.post("/backgrounds", response_model=BackgroundRead, status_code=status.HTTP_201_CREATED)
def create_background(payload: BackgroundRequest, service: PostServiceDep):
    """Fetch a photo (or generate a gradient) for the studio preview."""
    return _background_read(service.create_background(payload))


@router.post("/posts", response_model=PostRead, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, service: PostServiceDep):
    """Render a finished post PNG and its caption."""
    return service.create_post(payload)


@router.get("/posts", response_model=Page[PostRead])
def list_posts(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 40,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = PostRepository(session).page(limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/posts/{post_id}", response_model=PostRead)
def get_post(post_id: str, session: SessionDep):
    post = PostRepository(session).get(post_id)
    if post is None:
        raise NotFoundError("Post not found.")
    return post


@router.get("/posts/{post_id}/download", response_class=FileResponse)
def download_post(post_id: str, session: SessionDep, settings: SettingsDep):
    post = PostRepository(session).get(post_id)
    if post is None:
        raise NotFoundError("Post not found.")
    path = settings.posts_dir / post.filename
    if not path.is_file():
        raise NotFoundError("The image file for this post is missing.")
    return FileResponse(path, media_type="image/png", filename=f"instaquote-{post.id[:8]}.png")


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: str, session: SessionDep, service: PostServiceDep) -> None:
    post = PostRepository(session).get(post_id)
    if post is None:
        raise NotFoundError("Post not found.")
    service.delete_post(post)
