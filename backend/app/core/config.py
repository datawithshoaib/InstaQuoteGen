"""Application settings, loaded once from environment variables / backend/.env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App -------------------------------------------------------------
    app_name: str = "InstaQuote Studio API"
    version: str = "3.0.0"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # --- Storage ---------------------------------------------------------
    data_dir: Path = BACKEND_DIR / "data"
    assets_dir: Path = BACKEND_DIR / "assets"
    seed_file: Path = BACKEND_DIR / "seeds" / "quotes.json"
    database_url: str | None = None

    # --- LLM (Groq via LangChain) -----------------------------------------
    # "fake" runs the whole pipeline offline with a deterministic stand-in model (demos, UI work).
    llm_provider: Literal["groq", "fake"] = "groq"
    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    writer_temperature: float = Field(0.9, ge=0, le=2)
    judge_temperature: float = Field(0.0, ge=0, le=2)
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2

    # --- Generation pipeline guard rails ---------------------------------
    max_rewrite_rounds: int = Field(2, ge=0, le=4)
    pipeline_timeout_seconds: float = 90.0
    min_quality_score: float = Field(7.0, ge=0, le=10)

    # --- Images ------------------------------------------------------------
    unsplash_access_key: SecretStr | None = None
    unsplash_timeout_seconds: float = 10.0

    # --- Derived paths -----------------------------------------------------
    @property
    def posts_dir(self) -> Path:
        return self.data_dir / "posts"

    @property
    def backgrounds_dir(self) -> Path:
        return self.data_dir / "backgrounds"

    @property
    def font_path(self) -> Path:
        return self.assets_dir / "fonts" / "NotoSerif-Italic.ttf"

    @property
    def logo_path(self) -> Path:
        return self.assets_dir / "logo.png"

    @property
    def sqlalchemy_url(self) -> str:
        return self.database_url or f"sqlite:///{(self.data_dir / 'app.db').as_posix()}"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.get_secret_value().strip())

    @property
    def unsplash_enabled(self) -> bool:
        return bool(self.unsplash_access_key and self.unsplash_access_key.get_secret_value().strip())

    def ensure_dirs(self) -> None:
        for path in (self.data_dir, self.posts_dir, self.backgrounds_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
