def test_library_is_seeded(client):
    body = client.get("/api/v1/quotes?limit=5").json()
    assert body["total"] > 50
    assert len(body["items"]) == 5
    assert body["items"][0]["source"] == "seed"


def test_create_search_and_delete(client):
    res = client.post(
        "/api/v1/quotes",
        json={"text": "  “Tiny gardens still feed the soul.” ", "keywords": ["Garden"], "tone": "Calm"},
    )
    assert res.status_code == 201, res.text
    quote = res.json()
    assert quote["text"] == "Tiny gardens still feed the soul."
    assert quote["keywords"] == ["garden"]

    # Same text with different punctuation/case is a duplicate.
    dup = client.post("/api/v1/quotes", json={"text": "tiny gardens still feed the soul"})
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "conflict"

    found = client.get("/api/v1/quotes", params={"search": "gardens"}).json()
    assert [q["id"] for q in found["items"]] == [quote["id"]]

    by_keyword = client.get("/api/v1/quotes", params={"search": "garden", "source": "user"}).json()
    assert by_keyword["total"] == 1

    assert client.delete(f"/api/v1/quotes/{quote['id']}").status_code == 204
    assert client.get(f"/api/v1/quotes/{quote['id']}").status_code == 404
    assert client.delete(f"/api/v1/quotes/{quote['id']}").status_code == 404


def test_ids_are_stable_after_delete(client):
    first, second = client.get("/api/v1/quotes?limit=2").json()["items"]
    client.delete(f"/api/v1/quotes/{first['id']}")
    assert client.get(f"/api/v1/quotes/{second['id']}").json()["text"] == second["text"]


def test_random_quote(client):
    assert client.get("/api/v1/quotes/random").json()["text"]


def test_validation(client):
    res = client.post("/api/v1/quotes", json={"text": "  "})
    assert res.status_code == 422
