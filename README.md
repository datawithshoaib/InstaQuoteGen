# InstaQuoteGen

Generate Instagram quote posts with AI-generated quotes, Unsplash backgrounds, and Pillow rendering.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
```

Do not commit `.env` or expose either key.

## Run

```powershell
python -m insta_quote_gen
```

The application generates quote records, selects the next quote, downloads a matching Unsplash image, and saves rendered posts in `generated_posts/`.

## Layout

```text
insta_quote_gen/
  config.py          Environment and path configuration
  image_service.py   Unsplash image retrieval and preparation
  post_generator.py  Application orchestration
  post_renderer.py   Pillow-based post rendering and captions
  quote_store.py     Quote JSON storage and rotation
  quote_workflow.py  LangChain and LangGraph quote generation
  __main__.py        Module entry point

quotes.json          Local quote database
quote_index.txt      Current quote position
logo.png             Post logo
font.ttf             Post font
```

## Notes

- `quotes.json`, `quote_index.txt`, and `generated_posts/` are local runtime data.
- The first run requires working Groq and Unsplash API keys.
- Image generation requires the logo and font files in the project root.
