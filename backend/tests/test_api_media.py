from io import BytesIO

from PIL import Image

QUOTE = {
    "text": "Rest is part of the climb, not a detour from it.",
    "author": "Studio",
    "keywords": ["mountain"],
    "hashtags": ["Rest", "#climb"],
    "reflection": "Slow days still count.",
}


def test_system_reports_providers(client):
    info = client.get("/api/v1/system").json()
    assert info["llm"]["enabled"] is True  # fake LLM injected
    assert info["images"]["enabled"] is False  # no Unsplash key in tests
    assert info["counts"]["quotes"] > 0
    assert "portrait" in info["aspect_ratios"]


def test_background_then_post_roundtrip(client):
    bg = client.post(
        "/api/v1/backgrounds", json={"aspect_ratio": "square", "source": "gradient", "palette": "ocean"}
    )
    assert bg.status_code == 201, bg.text
    bg = bg.json()
    assert bg["source"] == "gradient" and bg["palette"] == "ocean"
    image = Image.open(BytesIO(client.get(bg["url"]).content))
    assert image.size == (1080, 1080)

    res = client.post(
        "/api/v1/posts",
        json={"quote": QUOTE, "background_id": bg["id"], "style": {"aspect_ratio": "square"}},
    )
    assert res.status_code == 201, res.text
    post = res.json()
    assert (post["width"], post["height"]) == (1080, 1080)
    assert "#rest" in post["caption"] and "#climb" in post["caption"]
    assert "Slow days still count." in post["caption"]

    png = client.get(post["url"])
    assert png.status_code == 200 and png.headers["content-type"] == "image/png"

    download = client.get(post["download_url"])
    assert "attachment" in download.headers["content-disposition"]

    assert client.get("/api/v1/posts").json()["total"] == 1
    assert client.delete(f"/api/v1/posts/{post['id']}").status_code == 204
    assert client.get(post["url"]).status_code == 404
    assert client.get("/api/v1/posts").json()["total"] == 0


def test_post_without_background_picks_one(client):
    res = client.post("/api/v1/posts", json={"quote": QUOTE, "style": {"aspect_ratio": "story"}})
    assert res.status_code == 201, res.text
    assert res.json()["height"] == 1920


def test_post_with_unknown_background_is_404(client):
    res = client.post("/api/v1/posts", json={"quote": QUOTE, "background_id": "nope"})
    assert res.status_code == 404


def test_style_validation(client):
    res = client.post("/api/v1/posts", json={"quote": QUOTE, "style": {"text_color": "red"}})
    assert res.status_code == 422


def test_nothing_outside_media_is_served(client):
    # The old app served the whole project root, including .env. Make sure that is gone.
    for path in [
        "/static/assets/.env",
        "/media/.env",
        "/media/posts/../../.env",
        "/media/posts/..%2F..%2F.env",
    ]:
        assert client.get(path).status_code == 404, path
