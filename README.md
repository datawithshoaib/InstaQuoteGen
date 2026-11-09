# InstaQuote Studio

Write, review and design Instagram quote posts with an AI pipeline you can actually watch.

You give it a topic. A small LangGraph pipeline plans a few angles, drafts quotes, runs them through
rule checks and an LLM judge, sends weak drafts back for a rewrite, and returns the best ones. The
studio then puts the quote on a matching Unsplash photo (or a generated gradient) and exports a
1080px PNG with a ready-to-paste caption.

```
topic ─► plan ─► write ─► review ─┬─► finalize ─► quotes ─► studio ─► PNG + caption
                   ▲              │
                   └── feedback ──┘  (up to 2 rewrite rounds)
```

## What's inside

| | |
|---|---|
| **Backend** | FastAPI · LangGraph · LangChain (Groq) · SQLModel/SQLite · Pillow · uv |
| **Frontend** | Next.js 16 (App Router) · React 19 · Tailwind CSS 4 · shadcn/ui · TanStack Query · Motion |
| **AI practices** | structured outputs, versioned prompts, input + output guard rails, LLM-as-judge with a rewrite loop, graceful fallback, per-run tracing, offline evals, deterministic fake model for tests |

Pages:

- **Generate**: topic, tone and count in; the pipeline lights up step by step over Server-Sent Events, with a live log of every draft the reviewer kept or rejected and why.
- **Studio**: live preview that uses the same font and layout rules as the exporter. Swap photos or gradients, change type, colours, format (4:5, 1:1, 9:16), then export.
- **Library**: starter quotes, your own, and AI quotes you chose to keep. Duplicate-proof.
- **Gallery**: every exported post with caption, download and photo credit.
- **Runs**: observability. Success rate, judge scores, draft acceptance, latency and tokens, plus a full trace for each run.

## Quick start

You need [uv](https://docs.astral.sh/uv/) and Node.js 20+.

```bash
# 1. keys (all optional, see below)
cp backend/.env.example backend/.env

# 2. run both apps
python run.py
```

- Web app: http://localhost:3000
- API docs: http://localhost:8000/docs

`run.py` uses only the standard library. It starts the API with `uv run` (which creates
`backend/.venv` on first run) and the web app with `npm run dev`. If those ports are busy:
`python run.py --api-port 8010 --web-port 3010`.

### Keys

| Variable | Without it | Get one |
|---|---|---|
| `GROQ_API_KEY` | Generation falls back to quotes from your library | [console.groq.com](https://console.groq.com/keys) (free) |
| `UNSPLASH_ACCESS_KEY` | Backgrounds are generated gradients | [unsplash.com/developers](https://unsplash.com/developers) |

No keys at all? Set `LLM_PROVIDER=fake` in `backend/.env` to run the full pipeline with a
deterministic stand-in model. It's handy for demos and frontend work.

### Running things separately

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload       # API on :8000
uv run pytest                              # 47 tests, no network or keys needed
uv run ruff check . && uv run ruff format --check .
uv run python -m evals.run --fake          # eval harness with the fake model
uv run python -m evals.run                 # ...or against the real model

cd frontend
cp .env.example .env.local                 # NEXT_PUBLIC_API_URL
npm install
npm run dev                                # web app on :3000
npm run lint && npm run build
```

## Project layout

```
backend/
  app/
    ai/            graph.py (LangGraph), llm.py, prompts.py, guardrails.py, tracing.py, schemas.py, fake_llm.py
    api/           routes/ (system, quotes, generations, media), deps.py, router.py
    core/          config.py (pydantic-settings), errors.py, logging.py, text.py
    db/            models.py (SQLModel tables), engine.py, seed.py
    repositories/  quotes.py, media.py, runs.py
    schemas/       request/response models (the API contract)
    services/      generation.py, images.py, renderer.py, captions.py, posts.py
    main.py        app factory, lifespan, middleware
  assets/          font + logo used by the renderer
  seeds/           starter quotes, loaded on first run
  evals/           dataset.jsonl + run.py (offline evaluation)
  tests/           pytest suite
  data/            runtime: SQLite DB, rendered posts, backgrounds (git-ignored)
frontend/
  app/             routes: / generate studio library gallery runs
  components/      ui/ (shadcn), layout/, generate/, studio/, post/, library/, gallery/, runs/, home/, shared/
  hooks/           data + streaming hooks
  lib/             api.ts (typed client + SSE reader), types.ts, format.ts
docs/
  PHASES.md        how the rebuild was done, phase by phase
  BLOG.md          the write-up
run.py             starts both apps
```

## API

All routes live under `/api/v1`. Interactive docs are at `/docs`.

| Method | Path | |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/system` | which providers are on, limits, prompt version, counts |
| POST | `/generations` | run the pipeline and return the result |
| POST | `/generations/stream` | same, as Server-Sent Events (`run`, `step`, `candidate`, `result`, `error`) |
| GET | `/runs`, `/runs/stats`, `/runs/{id}` | traces and aggregate metrics |
| GET/POST | `/quotes` | list (search, source filter, paging) / add |
| GET | `/quotes/random`, `/quotes/{id}` | |
| DELETE | `/quotes/{id}` | |
| POST | `/backgrounds` | fetch a photo or make a gradient for the studio |
| GET/POST | `/posts` | list / render a post |
| GET/DELETE | `/posts/{id}` | |
| GET | `/posts/{id}/download` | PNG as an attachment |

Errors always come back in the same shape: `{"error": {"code": "...", "message": "..."}}`.

## Configuration

Everything is read from environment variables or `backend/.env` (see `backend/.env.example`).
The ones you are most likely to touch:

| Variable | Default | |
|---|---|---|
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | any Groq chat model that supports tool calling |
| `LLM_PROVIDER` | `groq` | `fake` for the offline demo model |
| `MIN_QUALITY_SCORE` | `7.0` | judge score a draft needs to survive (0-10) |
| `MAX_REWRITE_ROUNDS` | `2` | extra writer attempts after the first |
| `PIPELINE_TIMEOUT_SECONDS` | `90` | hard limit per run, then fall back |
| `CORS_ORIGINS` | localhost:3000 | JSON list |
