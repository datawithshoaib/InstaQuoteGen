"""Background images: Unsplash photos, with generated gradients as a fallback.

Backgrounds are saved to disk and recorded in the database, so the studio can
show the exact image in its live preview and the renderer can reuse it later.
"""

import logging
import random
from dataclasses import dataclass
from io import BytesIO

import httpx
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from app.core.config import Settings

logger = logging.getLogger(__name__)

SIZES: dict[str, tuple[int, int]] = {
    "portrait": (1080, 1350),  # 4:5 feed post
    "square": (1080, 1080),  # 1:1 classic post
    "story": (1080, 1920),  # 9:16 story / reel cover
}

# (top colour, bottom colour, glow colour)
PALETTES: dict[str, tuple[tuple[int, int, int], ...]] = {
    "aurora": ((12, 10, 38), (24, 64, 92), (122, 92, 255)),
    "ember": ((28, 10, 18), (92, 30, 24), (255, 138, 76)),
    "ocean": ((6, 18, 38), (10, 58, 92), (64, 196, 255)),
    "forest": ((8, 22, 18), (24, 58, 44), (132, 204, 140)),
    "dusk": ((26, 14, 44), (110, 46, 88), (255, 166, 158)),
    "mono": ((14, 14, 16), (40, 40, 46), (180, 180, 190)),
}

UNSPLASH_RANDOM = "https://api.unsplash.com/photos/random"


@dataclass
class FetchedBackground:
    image: Image.Image
    source: str  # unsplash | gradient
    palette: str | None = None
    photographer_name: str | None = None
    photographer_url: str | None = None
    photo_url: str | None = None


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scale and centre-crop to exactly `size`, like CSS object-fit: cover."""
    return ImageOps.fit(image.convert("RGB"), size, Image.Resampling.LANCZOS)


def gradient_background(size: tuple[int, int], palette: str | None = None) -> FetchedBackground:
    """A soft vertical gradient with an off-centre glow and a little film grain."""
    name = palette if palette in PALETTES else random.choice(list(PALETTES))
    top, bottom, glow = PALETTES[name]
    w, h = size

    # Vertical gradient: Pillow's 256px ramp stretched to size (fast, no per-pixel loops).
    mask = Image.linear_gradient("L").resize((w, h))
    base = Image.composite(Image.new("RGB", size, bottom), Image.new("RGB", size, top), mask)

    # Glow: a blurred ellipse drawn small and scaled up, so it has no hard edges.
    scale = 8
    small = Image.new("L", (w // scale, h // scale), 0)
    cx, cy = w * random.uniform(0.25, 0.75) / scale, h * random.uniform(0.15, 0.45) / scale
    r = w * 0.32 / scale
    ImageDraw.Draw(small).ellipse((cx - r, cy - r, cx + r, cy + r), fill=150)
    glow_mask = small.filter(ImageFilter.GaussianBlur(r * 0.8)).resize(size, Image.Resampling.BICUBIC)
    base = Image.composite(Image.new("RGB", size, glow), base, glow_mask)

    # Film grain keeps large gradients from banding on phone screens.
    grain = Image.effect_noise((w // 2, h // 2), 18).resize(size).filter(ImageFilter.GaussianBlur(0.6))
    base = ImageChops.overlay(base, Image.merge("RGB", (grain, grain, grain)))
    return FetchedBackground(image=base, source="gradient", palette=name)


class UnsplashClient:
    def __init__(self, access_key: str, timeout: float):
        self._client = httpx.Client(
            timeout=timeout,
            headers={"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"},
        )

    def random_photo(self, query: str, aspect_ratio: str, size: tuple[int, int]) -> FetchedBackground | None:
        orientation = "squarish" if aspect_ratio == "square" else "portrait"
        resp = self._client.get(
            UNSPLASH_RANDOM,
            params={"query": query, "orientation": orientation, "content_filter": "high"},
        )
        if resp.status_code == 404:  # nothing matched the query
            return None
        resp.raise_for_status()
        data = resp.json()

        # Ask Unsplash's CDN for an image already close to the target size.
        raw_url = data["urls"]["raw"]
        w, h = size
        img_resp = self._client.get(
            raw_url, params={"w": w, "h": h, "fit": "crop", "crop": "entropy", "q": 85, "fm": "jpg"}
        )
        img_resp.raise_for_status()
        image = fit_cover(Image.open(BytesIO(img_resp.content)), size)

        # Unsplash API guidelines: trigger a download event when a photo is used.
        try:
            self._client.get(data["links"]["download_location"])
        except httpx.HTTPError:
            logger.debug("Could not register Unsplash download event")

        user = data.get("user", {})
        utm = "?utm_source=instaquote_studio&utm_medium=referral"
        return FetchedBackground(
            image=image,
            source="unsplash",
            photographer_name=user.get("name"),
            photographer_url=(user.get("links", {}).get("html") or "") + utm,
            photo_url=(data.get("links", {}).get("html") or "") + utm,
        )


class BackgroundService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._unsplash = (
            UnsplashClient(settings.unsplash_access_key.get_secret_value(), settings.unsplash_timeout_seconds)
            if settings.unsplash_enabled
            else None
        )

    def fetch(
        self,
        *,
        aspect_ratio: str,
        keywords: list[str],
        source: str = "auto",
        palette: str | None = None,
    ) -> FetchedBackground:
        size = SIZES[aspect_ratio]
        want_photo = source in ("auto", "photo") and self._unsplash is not None
        if want_photo:
            queries = [", ".join(keywords[:3])] if keywords else []
            queries += [k for k in keywords[:3] if k] + ["minimal moody landscape"]
            for query in dict.fromkeys(q for q in queries if q):
                try:
                    photo = self._unsplash.random_photo(query, aspect_ratio, size)
                    if photo:
                        return photo
                except (httpx.HTTPError, KeyError, OSError) as exc:
                    logger.warning("Unsplash lookup for %r failed: %s", query, exc)
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (401, 403):
                        break  # bad key or rate limited: no point trying other queries
        return gradient_background(size, palette)
