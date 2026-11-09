from fastapi import APIRouter, Request

from app.ai.prompts import PROMPT_VERSION
from app.api.deps import SessionDep, SettingsDep
from app.repositories.media import PostRepository
from app.repositories.quotes import QuoteRepository
from app.repositories.runs import RunRepository
from app.schemas.generation import TONES
from app.schemas.system import ProviderStatus, SystemInfo
from app.services.images import PALETTES, SIZES

router = APIRouter(tags=["system"])

MAX_QUOTES_PER_REQUEST = 6


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/system", response_model=SystemInfo)
def system_info(request: Request, settings: SettingsDep, session: SessionDep) -> SystemInfo:
    llm = request.app.state.llm
    return SystemInfo(
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        llm=ProviderStatus(
            enabled=llm is not None,
            detail=(
                f"{'Demo' if settings.llm_provider == 'fake' else 'Groq'} · {llm.model_name}"
                if llm
                else "Set GROQ_API_KEY in backend/.env"
            ),
        ),
        images=ProviderStatus(
            enabled=settings.unsplash_enabled,
            detail="Unsplash photos" if settings.unsplash_enabled else "Generated gradients",
        ),
        model=llm.model_name if llm else None,
        prompt_version=PROMPT_VERSION,
        min_quality_score=settings.min_quality_score,
        max_rewrite_rounds=settings.max_rewrite_rounds,
        max_quotes_per_request=MAX_QUOTES_PER_REQUEST,
        tones=list(TONES),
        aspect_ratios=list(SIZES),
        palettes=list(PALETTES),
        counts={
            "quotes": QuoteRepository(session).count(),
            "posts": PostRepository(session).count(),
            "runs": RunRepository(session).page(limit=1)[1],
        },
    )
