from io import BytesIO

import requests
from PIL import Image, ImageEnhance


POST_WIDTH = 1080
POST_HEIGHT = 1350
BRIGHTNESS_FACTOR = 0.2


def get_image_based_on_keywords(keywords, access_key):
    """Fetch and prepare a portrait background image from Unsplash."""
    try:
        if not keywords:
            raise ValueError("No keywords provided")

        for keyword in keywords:
            print(f"Searching for image using keyword: {keyword}")
            response = requests.get(
                "https://api.unsplash.com/photos/random",
                params={"query": keyword, "client_id": access_key},
                timeout=30,
            )
            response.raise_for_status()

            image_url = response.json()["urls"]["regular"]
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            image = Image.open(BytesIO(image_response.content))
            image = _crop_to_post(image)
            return ImageEnhance.Brightness(image).enhance(BRIGHTNESS_FACTOR)
    except Exception as error:
        print(f"Error fetching image: {error}")
        return None


def _crop_to_post(image):
    image_ratio = image.width / image.height
    target_ratio = POST_WIDTH / POST_HEIGHT

    if image_ratio > target_ratio:
        new_height = POST_HEIGHT
        new_width = int(POST_HEIGHT * image_ratio)
        image = image.resize((new_width, new_height), Image.LANCZOS)
        left = (new_width - POST_WIDTH) // 2
        return image.crop((left, 0, left + POST_WIDTH, POST_HEIGHT))

    new_width = POST_WIDTH
    new_height = int(POST_WIDTH / image_ratio)
    image = image.resize((new_width, new_height), Image.LANCZOS)
    top = (new_height - POST_HEIGHT) // 2
    return image.crop((0, top, POST_WIDTH, top + POST_HEIGHT))