from .config import Settings
from .image_service import get_image_based_on_keywords as _fetch_image
from .post_renderer import create_post as _render_post
from .post_renderer import generate_caption
from .quote_store import QuoteStore

SETTINGS = Settings.from_environment()
QUOTE_STORE = QuoteStore(SETTINGS.quotes_file, SETTINGS.index_file)
LOGO_PATH = SETTINGS.logo_path

def get_existing_quotes():
    """Read existing quotes from the JSON file."""
    try:
        return QUOTE_STORE.read()
    except Exception as e:
        print(f"Error reading existing quotes: {e}")
        return {"quotes": []}

def update_quotes_file(new_quotes):
    """Add new quotes to the JSON file, avoiding duplicates."""
    try:
        added_count = QUOTE_STORE.append_unique(new_quotes)
        if added_count:
            print(f"Added {added_count} new quotes to {QUOTE_STORE.quotes_file}")
        else:
            print("No new unique quotes to add")
        return added_count
    except Exception as e:
        print(f"Error updating quotes file: {e}")
        return 0

def get_next_quote():
    """Get the next quote and its keywords from the JSON file."""
    try:
        return QUOTE_STORE.next()
    except Exception as e:
        print(f"Error in get_next_quote: {e}")
        return None

def get_image_based_on_keywords(keywords):
    return _fetch_image(keywords, SETTINGS.unsplash_access_key)


def create_post(quote_obj, image, logo_path):
    return _render_post(
        quote_obj, image, logo_path, SETTINGS.font_path, SETTINGS.output_folder
    )

def main():
    try:
        from langchain_groq import ChatGroq
        from .quote_workflow import generate_new_quotes

        settings = Settings.from_environment(require_credentials=True)
        model = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.8,
            api_key=settings.groq_api_key,
        )
        # First, generate and update quotes
        new_quotes = generate_new_quotes(model)
        added_quotes = update_quotes_file(new_quotes)
        print(f"Successfully added {added_quotes} new quotes")

        # Then proceed with creating the post
        for _ in range(20):
            quote_obj = get_next_quote()
            if not quote_obj:
                raise ValueError("Failed to get a quote")

            background_image = get_image_based_on_keywords(quote_obj['keywords'])
            if not background_image:
                raise ValueError("Failed to get background image")

            post_image = create_post(quote_obj, background_image, LOGO_PATH)
            
            # if post_image:
            #     caption = generate_caption(quote_obj)
            #     print(f'Caption:\n{caption}')
    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == '__main__':
    main()