"""Pillow renderer for quote posts.

The layout rules here are mirrored by the studio's live preview in the
frontend (same font, same proportions, balanced line wrapping), so what you
see while editing is what you get in the exported PNG.
"""

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.schemas.media import PostStyle

LINE_HEIGHT = 1.28
MAX_BLOCK_RATIO = 0.56  # quote block may use at most this share of the canvas height
MIN_FONT_SIZE = 30
AUTHOR_GAP = 0.45  # space between the quote and the author line, as a share of font size


@lru_cache(maxsize=64)
def load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


@lru_cache(maxsize=4)
def load_round_logo(path: str, diameter: int) -> Image.Image | None:
    if not Path(path).exists():
        return None
    logo = ImageOps.fit(Image.open(path).convert("RGBA"), (diameter, diameter), Image.Resampling.LANCZOS)
    mask = Image.new("L", (diameter * 4, diameter * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter * 4, diameter * 4), fill=255)
    logo.putalpha(mask.resize((diameter, diameter), Image.Resampling.LANCZOS))
    return logo


def _greedy_wrap(text: str, font, max_width: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or font.getlength(candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrap_balanced(text: str, font, max_width: float) -> list[str]:
    """Wrap to the fewest lines, then even out line lengths (like CSS text-wrap: balance)."""
    target = len(_greedy_wrap(text, font, max_width))
    lo, hi = max_width * 0.4, max_width
    for _ in range(14):
        mid = (lo + hi) / 2
        if len(_greedy_wrap(text, font, mid)) <= target:
            hi = mid
        else:
            lo = mid
    return _greedy_wrap(text, font, hi)


def _scrim(size: tuple[int, int], opacity: float) -> Image.Image:
    """Flat darkening plus a gentle vignette at the top and bottom edges."""
    _, h = size
    flat = int(255 * opacity)
    # distance from the vertical centre: 0 in the middle, 1 at the top/bottom edge
    edge = [abs(y / max(h - 1, 1) - 0.5) * 2 for y in range(h)]
    column = Image.new("L", (1, h))
    column.putdata([min(255, flat + int(70 * d**2.2)) for d in edge])
    alpha = column.resize(size)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.putalpha(alpha)
    return layer


def _x_for(align: str, line_width: float, canvas_w: int, margin: int) -> float:
    if align == "left":
        return margin
    if align == "right":
        return canvas_w - margin - line_width
    return (canvas_w - line_width) / 2


def render_post(
    *,
    background: Image.Image,
    text: str,
    author: str | None,
    style: PostStyle,
    font_path: Path,
    logo_path: Path,
) -> Image.Image:
    canvas = background.convert("RGBA")
    w, h = canvas.size
    canvas = Image.alpha_composite(canvas, _scrim(canvas.size, style.overlay_opacity))

    margin = int(w * 0.1)
    max_text_width = w - 2 * margin
    font_file = str(font_path)
    text_rgb = ImageColor.getrgb(style.text_color)
    accent_rgb = ImageColor.getrgb(style.accent_color)

    # Shrink the font until the quote block fits comfortably.
    size = style.font_size
    while True:
        font = load_font(font_file, size)
        lines = wrap_balanced(text, font, max_text_width)
        line_h = size * LINE_HEIGHT
        if len(lines) * line_h <= h * MAX_BLOCK_RATIO or size <= MIN_FONT_SIZE:
            break
        size -= 2

    mark_size = int(size * 2.2)
    mark_font = load_font(font_file, mark_size)
    mark_h = int(mark_size * 0.55) if style.show_quote_mark else 0
    author_size = max(24, int(size * 0.42))
    author_font = load_font(font_file, author_size)
    show_author = bool(style.show_author and author)
    author_block = int(AUTHOR_GAP * size + author_size * LINE_HEIGHT) if show_author else 0

    block_h = mark_h + len(lines) * line_h + author_block
    y = (h - block_h) / 2 - h * 0.02  # sit slightly above centre, where the eye lands

    # Text goes on its own layer so we can add a soft shadow behind it.
    text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    if style.show_quote_mark:
        mark = "“"
        mark_w = mark_font.getlength(mark)
        draw.text(
            (_x_for(style.align, mark_w, w, margin), y - mark_size * 0.28),
            mark,
            font=mark_font,
            fill=(*accent_rgb, 235),
        )
        y += mark_h

    for line in lines:
        draw.text(
            (_x_for(style.align, font.getlength(line), w, margin), y),
            line,
            font=font,
            fill=(*text_rgb, 255),
        )
        y += line_h

    if show_author:
        label = f"— {author}"
        y += AUTHOR_GAP * size
        draw.text(
            (_x_for(style.align, author_font.getlength(label), w, margin), y),
            label,
            font=author_font,
            fill=(*accent_rgb, 255),
        )

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow.putalpha(text_layer.getchannel("A").point(lambda a: int(a * 0.65)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(4, size // 7)))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas = Image.alpha_composite(canvas, text_layer)

    # Footer: optional round logo, then the handle.
    footer_y = h - int(h * 0.055)
    draw = ImageDraw.Draw(canvas)
    if style.show_logo and (logo := load_round_logo(str(logo_path), 84)):
        logo_y = footer_y - 84 - (44 if style.watermark else 0)
        canvas.alpha_composite(logo, ((w - 84) // 2, logo_y))
    if style.watermark:
        wm_font = load_font(font_file, 30)
        wm = style.watermark.strip()
        draw.text(
            ((w - wm_font.getlength(wm)) / 2, footer_y - 30),
            wm,
            font=wm_font,
            fill=(255, 255, 255, 190),
        )

    return canvas.convert("RGB")
