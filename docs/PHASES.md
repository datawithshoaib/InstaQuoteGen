# Rebuild log: InstaQuoteGen → InstaQuote Studio (v3)

This file records how the project was rebuilt, one phase at a time: what was wrong, what changed,
why, and how each phase was checked. Read it top to bottom to follow the reasoning, or jump to a
phase.

| Phase | Topic | Result |
|---|---|---|
| 0 | Audit | 20+ problems found, 2 of them security issues |
| 1 | Restructure | one backend, one frontend, no duplicate code |
| 2 | Backend foundation | settings, SQLite, repositories, error envelope, logging |
| 3 | AI pipeline | LangGraph plan → write → review → (rewrite) → finalize, with guard rails and tracing |
| 4 | Images and rendering | Unsplash with attribution, fast gradients, balanced typography |
| 5 | API | versioned REST + SSE streaming, consistent errors |
| 6 | Tests and evals | 47 pytest tests, offline eval harness, fake model |
| 7 | Frontend | Next.js 16 + shadcn/ui rebuild, five pages, live pipeline view |
| 8 | Verification and docs | end-to-end browser run, performance fixes, docs |

---

## Phase 0: Audit

I read every file before changing anything. The main findings, worst first:

**Security**

1. **`.env` was publicly downloadable.** `main.py` mounted the whole project root as static files
   (`app.mount("/static/assets", StaticFiles(directory=ROOT_DIR))`), so
   `GET /static/assets/.env` returned the API keys. The same mount also exposed `quotes.json`,
   the source code and everything else in the folder.
2. **Anyone could overwrite the API keys.** `POST /settings/keys` had no auth and wrote whatever
   it received into `.env`. CORS was `*`, so any website you visited could call it.
3. Several endpoints accepted API keys in the request body (`groq_api_key`,
   `unsplash_access_key`), which encouraged keys to live in the browser.

**Structure**

4. The same logic existed twice: `insta_quote_gen/` (legacy package) and `backend/app/services/`
   had near-identical image, renderer, store and workflow code.
5. Three dependency files (`requirements.txt` at the root, `backend/requirements.txt`,
   `backend/pyproject.toml`) and no lock file.
6. The API was mounted twice (`/api` and `/api/v1`).
7. `run.py` created a root `.venv`, re-executed itself, and imported the backend as
   `backend.app`, which only worked from one directory.

**Data**

8. Quote IDs were list positions, so deleting quote 3 silently renumbered every quote after it.
   A stale page could delete the wrong quote.
9. JSON writes were not atomic and had no locking: two requests at once could corrupt
   `quotes.json`.
10. The rotation index lived in a separate text file that drifted when quotes were deleted.
11. Generated posts were only files on disk, so the gallery had no captions or metadata.

**AI**

12. The "LangGraph agent" had one real LLM step. `expand_themes` was a hard-coded dictionary
    lookup.
13. No quality control: whatever the model returned went straight into the library.
14. The model was asked to invent an author, which risks putting fake quotes in real people's
    mouths.
15. Errors were swallowed inside graph nodes and turned into empty lists, so failures looked like
    "no results".
16. The graph was rebuilt on every request. There were no retries, no timeouts, no record of what
    happened in a run, no evals and no tests.
17. Prompts had no version, so a change in output quality couldn't be traced to a prompt change.

**Rendering**

18. Text wrapped by character count, not pixel width, so large fonts overflowed the canvas.
19. The fallback gradient was drawn one line at a time in Python (slow) and then blurred.
20. Unsplash photos were used without attribution or the required download ping.
21. `quality=95` was passed to PNG (ignored), and file names used `random.randint` (collisions
    possible).

**Frontend**

22. `StudioTab.tsx` was over 600 lines; all four tabs lived on one client page.
23. No `components.json`, so shadcn could not be used to add components. A custom `gradient`
    button variant was referenced but did not exist.
24. No toasts, no loading skeletons, no empty states. Errors were shown as raw strings.

---

## Phase 1: Restructure

- Removed `insta_quote_gen/`, the root `requirements.txt` and `backend/requirements.txt`.
- Moved assets to the code that uses them: `backend/assets/logo.png`,
  `backend/assets/fonts/NotoSerif-Italic.ttf`, `backend/seeds/quotes.json` (with `git mv`, so
  history is kept).
- Moved `.env` into `backend/.env`; added `backend/.env.example` and `frontend/.env.example`.
- Backed up the old `backend/`, `frontend/` and `run.py` (they were untracked) before replacing
  them.
- `backend/` is now a uv project: `pyproject.toml` + `uv.lock` are the single source of truth.

**Check:** `git status` shows renames, not deletes, for the assets.

---

## Phase 2: Backend foundation

| Concern | Before | After |
|---|---|---|
| Settings | mutable global, keys written at runtime | `pydantic-settings`, `SecretStr` for keys, read-only, cached with `lru_cache` |
| Storage | `quotes.json` + `quote_index.txt` | SQLite via SQLModel, WAL mode, unique index on normalised text |
| IDs | list position | integer primary keys (quotes), UUIDs (posts, backgrounds, runs) |
| Data access | file reads inside endpoints | repository classes (`repositories/`) |
| Errors | `HTTPException(detail=str(e))`, sometimes 200 with `None` | domain errors → one JSON shape `{"error": {"code", "message"}}`, including validation errors |
| Logging | `basicConfig` | one formatter with a per-request id (`X-Request-ID`), request timing |

Tables: `Quote`, `Background`, `Post`, `GenerationRun`. Starter quotes are seeded on first start.
Duplicate detection normalises text (case, punctuation, curly quotes), so
"Stay curious." and "stay curious" count as the same quote.

---

## Phase 3: The AI pipeline

This is the core of the project. The goal was a pipeline that is small enough to understand but
built the way production LLM features should be.

### Graph

```
START → plan → write → review ─┬─(enough good quotes, or out of rounds)→ finalize → END
                 ▲             │
                 └─ feedback ──┘
```

- **plan:** the LLM proposes 3-5 specific angles and photo-search phrases for the topic.
- **write:** the LLM drafts `count + 1` quotes (one spare, since some won't survive). It is told
  which existing quotes to avoid and what the editor said about the last attempt.
- **review:** two layers:
  1. *Rule checks* (free, deterministic): 5-28 words, no hashtags, links or emoji, no banned
     clichés, not too similar to a library quote or another draft (`difflib` ratio ≥ 0.82).
  2. *LLM judge* (temperature 0): scores originality, clarity, impact and topic fit from 1-10, plus
     a safety flag. A draft needs an average of 7.0 or better (configurable).
- **route:** if enough quotes passed, finalize. Otherwise go back to `write` with the rejection
  reasons as feedback, up to 2 rewrite rounds.
- **finalize:** keep the best N by score, clean hashtags and keywords.

The graph is compiled **once**. Per-run dependencies (LLM client, tracer, quality bar) are passed
through LangGraph's runtime `context`, not globals.

### Practices applied, and where

| Practice | Where |
|---|---|
| Structured outputs. Every LLM call is bound to a Pydantic schema (`with_structured_output(include_raw=True)`), and parse failures raise instead of returning junk | `ai/schemas.py`, `ai/llm.py` |
| Versioned prompts. `PROMPT_VERSION` is stored on every run | `ai/prompts.py` |
| Prompt-injection defence. Topic is validated (length, charset, injection patterns) before any call, and user text sits in tags the system prompt marks as data | `ai/guardrails.py`, `ai/prompts.py` |
| Output guard rails before the judge, so cheap checks run first | `ai/guardrails.py` |
| LLM-as-judge with a bounded self-correction loop | `ai/graph.py` |
| No fake attribution. AI quotes always have `author = None` | `ai/graph.py` (finalize) |
| Provider abstraction. The graph talks to a `QuoteLLM` protocol, not to Groq directly | `ai/llm.py` |
| Timeouts and retries. Per call (`timeout`, `max_retries`) and per run (`asyncio.wait_for`) | `ai/llm.py`, `services/generation.py` |
| Graceful degradation. No key, provider error or timeout falls back to library quotes, and the response says so (`status: fallback`, `note`) | `services/generation.py` |
| Observability. Each step is timed, and tokens are counted from `usage_metadata` | `ai/tracing.py` |
| Run records. Every run saves status, model, prompt version, rounds, tokens, latency, scores, rejection counts, step trace and results | `GenerationRun` table, `/runs` API, Runs page |
| Streaming. The same tracer events are streamed to the browser as SSE | `/generations/stream` |
| Deterministic test double. `FakeQuoteLLM` produces a cliché on purpose so the reject path is exercised | `ai/fake_llm.py` |

---

## Phase 4: Images and rendering

- **Unsplash:** `httpx` client with a timeout; asks the CDN for a pre-cropped image at the exact
  size; calls `download_location` as the API guidelines require; stores photographer name and
  links (with UTM tags) and puts the credit in the caption. A 401 or 403 stops further attempts
  instead of hammering the API.
- **Gradients:** six named palettes. Built from Pillow's 256px ramp stretched to size, a blurred
  ellipse for the glow (drawn at 1/8 scale) and light film grain. This replaces the per-line Python
  loop. The first version left a visible hard edge from `radial_gradient`; I caught it on a contact
  sheet and fixed it.
- **Backgrounds are saved** (`Background` table + `data/backgrounds/`), so the studio preview and
  the final render use the exact same image.
- **Renderer:** pixel-width wrapping with *balanced* lines (binary search for the narrowest width
  that keeps the same line count, like CSS `text-wrap: balance`); shrinks the font until the block
  fits; soft blurred text shadow instead of a hard stroke; accent-coloured opening quote mark;
  vignette scrim; optional round-masked logo; cached fonts.
- **Captions:** deterministic (same quote, same call to action), deduplicated hashtags, the
  model's one-line reflection, and the photo credit.

**Check:** rendered every aspect ratio and palette to a contact sheet and looked at them.

---

## Phase 5: API

- Versioned under `/api/v1`, mounted once.
- Only `data/posts` and `data/backgrounds` are served as static files (`/media/...`).
- The key-writing endpoint is gone. Keys come from the environment, and `/system` reports which
  providers are on without ever returning a key.
- CORS is an explicit origin list with credentials off and only the methods we use.
- `POST /generations/stream` uses FastAPI's built-in `EventSourceResponse`. Events: `run`, `step`,
  `candidate`, `result`, `error`. If the client disconnects, the run is cancelled.
- Request validation runs the topic guard rail, so injection attempts get a 422 before any model
  call.

---

## Phase 6: Tests and evals

**Tests** (`uv run pytest`, 47 tests, about 50 s, no network or keys):

- guard rails: injection patterns, bad shapes, every rejection reason, near-duplicates
- pipeline: happy path, cliché rejected, rewrite loop stops at the round limit, results sorted
  and deduplicated against the library, events emitted in order
- API: generation with the fake LLM, library mode, simulated provider outage (falls back and
  records the error), injection rejected, count capped, SSE stream parsed end to end
- quotes: seeding, create, normalised duplicate → 409, search, delete, stable IDs after delete
- media: background → post round trip, download headers, delete removes the file, style
  validation, **regression test that `.env` and paths outside `/media` are not served**
- rendering: balanced wrap never adds a line and is less ragged than greedy; all aspect ratios
  render; captions are deterministic

Each test gets its own temporary data folder and database.

**Evals** (`uv run python -m evals.run [--fake]`): ten topic/tone cases in
`evals/dataset.jsonl`, run through the same graph. Reports: success rate, mean judge score, draft
acceptance rate, rule pass rate of final quotes (should be 1.0), diversity inside a batch, rounds,
latency and tokens per quote. Each run writes a Markdown report to `evals/reports/` named after
the model, so prompt versions can be compared.

> The real-model eval has not been run yet because no `GROQ_API_KEY` was configured during the
> rebuild. Add a key and run `uv run python -m evals.run` to get the first baseline.

---

## Phase 7: Frontend

Rebuilt from a fresh `create-next-app@latest` (Next.js 16, React 19, Tailwind 4) and
`shadcn@latest init`. The old app was a single client page with four tabs.

**Design.** Dark "studio" look: deep ink background, slow-moving aurora colour fields with film
grain, glass panels, and a warm gold accent that matches the gold quote mark on the posts. Headings
use Noto Serif Italic, the same family the exporter renders with, so the UI and the output feel like
one product. Motion is used for meaning (pipeline progress, results arriving, score bars) and
respects `prefers-reduced-motion`.

**Pages**

- `/`: hero with floating live post previews, quick topic box, how-it-works, recent posts.
- `/generate`: form; pipeline graph whose nodes light up from SSE events (with the rewrite
  round shown); result cards with per-criterion score bars; reviewer log listing every rejected
  draft and why; run metadata (model, latency, tokens, prompt version); one-click "Make post".
- `/studio`: tabs for words, type and background; live preview that mirrors the Pillow layout in
  CSS container-query units; real Unsplash photo or gradient; export dialog with caption copy and
  download.
- `/library`: debounced search, source filter, infinite paging, add dialog, confirm before
  delete.
- `/gallery`: grid of posts, lightbox with caption, credit, download, delete.
- `/runs`: metric tiles plus a run table, with a side sheet showing the step timeline and results.

**Code practices:** typed API client with one error type; TanStack Query for caching and
invalidation; a hook that turns the SSE stream into state; shared components (post preview,
post dialog, page header, empty state, copy button); skeletons and empty states everywhere;
toasts for outcomes; Suspense fallbacks for pages that read the URL; `tsc`, ESLint and
`next build` all clean.

---

## Phase 8: Verification

Ran the real stack (API with the Unsplash key, `next start` production build) and drove it with a
headless browser:

- Generate streamed `run → step → candidate → result`; nodes lit up in order; the planted cliché
  showed up as "rejected by rule check".
- "Make post" rendered a 1080×1350 PNG on an Unsplash photo with the photographer credited in the
  caption.
- Runs page showed the trace; Library, Gallery and Studio rendered with real data.
- No console or page errors on any page.
- Mobile (390 px): no horizontal scroll on any page.
- `GET /static/assets/.env` → 404.

Problems found during this phase, and fixed:

1. The gradient headline rendered as solid colour blocks. It needed the `-webkit-` prefixed
   `background-clip: text` and `text-fill-color`.
2. The hero's side cards were hidden behind the middle one; I spread the fan out.
3. **Performance:** three viewport-sized layers with `filter: blur(140px)` and a constant animation
   pegged the browser on a busy machine. I replaced them with radial gradients, which look the
   same at a tiny fraction of the cost.
4. Studio and Generate showed an empty shell until JavaScript loaded; they now get skeleton
   fallbacks.
5. The gallery used CSS columns, which left an empty column with few posts; it's a grid now.
6. Two small mobile overflows (hero card, preview glow).

Also added `LLM_PROVIDER=fake`, which runs the whole pipeline offline with simulated latency, so
the live UI can be demoed and developed without a key.

---

## Not done yet / next steps

- **Run the real-model eval** once a Groq key is set, and commit that report as the baseline.
- If this is ever deployed publicly: authentication, per-user rate limiting on `/generations`, and
  object storage instead of the local `data/` folder.
- Schema migrations (Alembic) before the database shape changes again.
- CI (GitHub Actions) running `pytest`, `ruff`, `eslint` and `next build`.
- Optional LangSmith or OpenTelemetry export of the traces already being collected.
- The old `generated_posts/` folder from v2 is left on disk untouched; it isn't used anymore.
