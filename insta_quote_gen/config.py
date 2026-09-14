import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    groq_api_key: str
    unsplash_access_key: str
    logo_path: Path
    quotes_file: Path
    index_file: Path
    output_folder: Path
    font_path: Path

    @classmethod
    def from_environment(cls, base_dir=None, require_credentials=False):
        root = Path(base_dir or Path(__file__).resolve().parent.parent)
        load_dotenv(root / ".env")

        groq_api_key = os.getenv("GROQ_API_KEY")
        unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if require_credentials and not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        if require_credentials and not unsplash_access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY environment variable is not set")

        return cls(
            base_dir=root,
            groq_api_key=groq_api_key,
            unsplash_access_key=unsplash_access_key,
            logo_path=root / "logo.png",
            quotes_file=root / "quotes.json",
            index_file=root / "quote_index.txt",
            output_folder=root / "generated_posts",
            font_path=root / "font.ttf",
        )