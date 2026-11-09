from PIL import Image

from app.core.config import get_settings
from app.schemas.media import PostStyle
from app.services.captions import build_caption
from app.services.images import SIZES, gradient_background
from app.services.renderer import _greedy_wrap, load_font, render_post, wrap_balanced

LONG = (
    "The mountain does not care how you feel this morning, it only asks whether you will "
    "take one more honest step toward the top before the light goes."
)


def test_balanced_wrap_respects_width_and_evens_lines():
    font = load_font(str(get_settings().font_path), 64)
    greedy = _greedy_wrap(LONG, font, 864)
    balanced = wrap_balanced(LONG, font, 864)

    assert " ".join(balanced) == LONG
    assert all(font.getlength(line) <= 864 for line in balanced)
    assert len(balanced) == len(greedy)  # never costs an extra line

    def raggedness(lines):
        widths = [font.getlength(line) for line in lines]
        return max(widths) - min(widths)

    assert raggedness(balanced) < raggedness(greedy)


def test_render_all_aspect_ratios():
    settings = get_settings()
    for aspect, size in SIZES.items():
        bg = gradient_background(size, "dusk").image
        out = render_post(
            background=bg,
            text=LONG,
            author="Someone",
            style=PostStyle(aspect_ratio=aspect, font_size=120, show_logo=True),
            font_path=settings.font_path,
            logo_path=settings.logo_path,
        )
        assert isinstance(out, Image.Image)
        assert out.size == size


def test_caption_is_deterministic_and_credits_photographer():
    a = build_caption(text="Stay soft.", hashtags=["#Calm", "calm"], photographer="Ana")
    b = build_caption(text="Stay soft.", hashtags=["#Calm", "calm"], photographer="Ana")
    assert a == b
    assert "Photo by Ana on Unsplash" in a
    assert a.count("#calm") == 1
