from typing import Literal

from pydantic import Field, computed_field, field_validator

from app.core.text import clean_quote_text
from app.schemas import ApiModel, UtcDatetime

AspectRatio = Literal["portrait", "square", "story"]
BackgroundSource = Literal["auto", "photo", "gradient"]
Palette = Literal["aurora", "ember", "ocean", "forest", "dusk", "mono"]

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class BackgroundRequest(ApiModel):
    aspect_ratio: AspectRatio = "portrait"
    keywords: list[str] = Field(default_factory=list, max_length=6)
    source: BackgroundSource = "auto"
    palette: Palette | None = None


class Credit(ApiModel):
    name: str
    profile_url: str | None = None
    photo_url: str | None = None


class BackgroundRead(ApiModel):
    id: str
    source: str
    aspect_ratio: str
    width: int
    height: int
    palette: str | None
    keywords: list[str]
    url: str
    credit: Credit | None


class PostStyle(ApiModel):
    aspect_ratio: AspectRatio = "portrait"
    font_size: int = Field(default=64, ge=28, le=120)
    text_color: str = Field(default="#FFFFFF", pattern=HEX_COLOR)
    accent_color: str = Field(default="#F5C26B", pattern=HEX_COLOR)
    align: Literal["left", "center", "right"] = "center"
    overlay_opacity: float = Field(default=0.35, ge=0, le=0.9)
    watermark: str | None = Field(default="@instaquote.studio", max_length=40)
    show_author: bool = True
    show_logo: bool = False
    show_quote_mark: bool = True


class PostQuote(ApiModel):
    text: str = Field(min_length=3, max_length=300)
    author: str | None = Field(default=None, max_length=80)
    keywords: list[str] = Field(default_factory=list, max_length=6)
    hashtags: list[str] = Field(default_factory=list, max_length=12)
    reflection: str | None = Field(default=None, max_length=300)

    @field_validator("text")
    @classmethod
    def _clean(cls, value: str) -> str:
        return clean_quote_text(value)


class PostCreate(ApiModel):
    quote: PostQuote
    style: PostStyle = Field(default_factory=PostStyle)
    background_id: str | None = Field(
        default=None, description="Background from POST /backgrounds. Picked automatically if empty."
    )


class PostRead(ApiModel):
    id: str
    filename: str
    aspect_ratio: str
    width: int
    height: int
    quote_text: str
    quote_author: str | None
    caption: str
    background_source: str
    photographer_name: str | None
    photographer_url: str | None
    created_at: UtcDatetime

    @computed_field
    @property
    def url(self) -> str:
        return f"/media/posts/{self.filename}"

    @computed_field
    @property
    def download_url(self) -> str:
        return f"/api/v1/posts/{self.id}/download"
