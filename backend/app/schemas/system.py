from app.schemas import ApiModel


class ProviderStatus(ApiModel):
    enabled: bool
    detail: str


class SystemInfo(ApiModel):
    app: str
    version: str
    environment: str
    llm: ProviderStatus
    images: ProviderStatus
    model: str | None
    prompt_version: str
    min_quality_score: float
    max_rewrite_rounds: int
    max_quotes_per_request: int
    tones: list[str]
    aspect_ratios: list[str]
    palettes: list[str]
    counts: dict[str, int]
