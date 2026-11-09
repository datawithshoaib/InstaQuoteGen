"""Creating backgrounds and posts, and keeping files and rows in sync."""

import logging

from PIL import Image
from sqlmodel import Session

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.db.models import Background, Post, new_id
from app.repositories.media import BackgroundRepository, PostRepository
from app.schemas.media import BackgroundRequest, PostCreate
from app.services.captions import build_caption
from app.services.images import SIZES, BackgroundService, fit_cover
from app.services.renderer import render_post

logger = logging.getLogger(__name__)


class PostService:
    def __init__(self, settings: Settings, session: Session, backgrounds: BackgroundService):
        self.settings = settings
        self.backgrounds = backgrounds
        self.background_repo = BackgroundRepository(session)
        self.post_repo = PostRepository(session)

    def create_background(self, req: BackgroundRequest) -> Background:
        fetched = self.backgrounds.fetch(
            aspect_ratio=req.aspect_ratio,
            keywords=[k.strip() for k in req.keywords if k.strip()],
            source=req.source,
            palette=req.palette,
        )
        bg_id = new_id()
        filename = f"{bg_id}.jpg"
        fetched.image.save(self.settings.backgrounds_dir / filename, "JPEG", quality=90)
        w, h = fetched.image.size
        return self.background_repo.add(
            Background(
                id=bg_id,
                source=fetched.source,
                aspect_ratio=req.aspect_ratio,
                width=w,
                height=h,
                filename=filename,
                keywords=req.keywords,
                palette=fetched.palette,
                photographer_name=fetched.photographer_name,
                photographer_url=fetched.photographer_url,
                photo_url=fetched.photo_url,
            )
        )

    def create_post(self, req: PostCreate) -> Post:
        style, quote = req.style, req.quote
        if req.background_id:
            bg = self.background_repo.get(req.background_id)
            if bg is None:
                raise NotFoundError("Background not found. Pick a new one and try again.")
        else:
            bg = self.create_background(
                BackgroundRequest(aspect_ratio=style.aspect_ratio, keywords=quote.keywords)
            )

        size = SIZES[style.aspect_ratio]
        with Image.open(self.settings.backgrounds_dir / bg.filename) as img:
            background = fit_cover(img, size) if img.size != size else img.convert("RGB")

        image = render_post(
            background=background,
            text=quote.text,
            author=quote.author,
            style=style,
            font_path=self.settings.font_path,
            logo_path=self.settings.logo_path,
        )
        post_id = new_id()
        filename = f"{post_id}.png"
        image.save(self.settings.posts_dir / filename, "PNG", optimize=True)

        caption = build_caption(
            text=quote.text,
            author=quote.author,
            reflection=quote.reflection,
            hashtags=quote.hashtags,
            keywords=quote.keywords,
            photographer=bg.photographer_name if bg.source == "unsplash" else None,
        )
        post = self.post_repo.add(
            Post(
                id=post_id,
                filename=filename,
                aspect_ratio=style.aspect_ratio,
                width=size[0],
                height=size[1],
                quote_text=quote.text,
                quote_author=quote.author,
                caption=caption,
                background_source=bg.source,
                photographer_name=bg.photographer_name,
                photographer_url=bg.photographer_url,
                style=style.model_dump(),
            )
        )
        logger.info("Rendered post %s (%s, %s background)", post.id, style.aspect_ratio, bg.source)
        return post

    def delete_post(self, post: Post) -> None:
        (self.settings.posts_dir / post.filename).unlink(missing_ok=True)
        self.post_repo.delete(post)
