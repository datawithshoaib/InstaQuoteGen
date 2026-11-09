import os

import pytest
from fastapi.testclient import TestClient

# Make sure tests never pick up real keys from backend/.env.
os.environ["GROQ_API_KEY"] = ""
os.environ["UNSPLASH_ACCESS_KEY"] = ""
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Every test gets its own empty data folder and SQLite database."""
    from app.core.config import get_settings
    from app.db.engine import get_engine

    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_engine().dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()


@pytest.fixture
def fake_llm():
    from app.ai.fake_llm import FakeQuoteLLM

    return FakeQuoteLLM()


def make_client(llm) -> TestClient:
    from app.main import create_app

    app = create_app()
    app.state.llm = llm
    return TestClient(app)


@pytest.fixture
def client(fake_llm):
    with make_client(fake_llm) as c:
        yield c


@pytest.fixture
def offline_client():
    """App with no LLM configured, i.e. library fallback mode."""
    with make_client(None) as c:
        yield c
