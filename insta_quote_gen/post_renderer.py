import os
import random
import textwrap

from PIL import Image, ImageDraw, ImageFont


FONT_SIZE = 60
TEXT_COLOR = (255, 255, 255)


def create_post(quote_obj, image, logo_path, font_path, output_folder):
    """Render a quote and logo onto an image and save the finished post."""
    try:
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo not found: {logo_path}")
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font not found: {font_path}")

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, FONT_SIZE)
        logo = Image.open(logo_path).convert("RGBA")
        max_logo_width = 150
        logo_ratio = max_logo_width / logo.size[0]
        logo = logo.resize(
            (max_logo_width, int(logo.size[1] * logo_ratio)), Image.LANCZOS
        )

        lines = textwrap.wrap(quote_obj["text"], width=25)
        line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
        y_text = (image.height - sum(line_heights)) / 2

        for line, line_height in zip(lines, line_heights):
            bbox = draw.textbbox((0, 0), line, font=font)
            x_text = (image.width - (bbox[2] - bbox[0])) / 2
            draw.text(
                (x_text, y_text),
                line,
                font=font,
                fill=TEXT_COLOR,
                stroke_width=2,
                stroke_fill="black",
            )
            y_text += line_height

        logo_x = (image.width - logo.size[0]) // 2
        logo_y = image.height - logo.size[1] - 50
        image.paste(logo, (logo_x, logo_y), logo)

        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(
            output_folder, f"post_{random.randint(1000, 9999)}.png"
        )
        image.save(output_path)
        print(f"Post created: {output_path}")
        return output_path
    except Exception as error:
        print(f"Error creating post: {error}")
        return None


def generate_caption(quote_obj):
    hashtags = [
        "#motivation",
        "#inspiration",
        "#selfimprovement",
        "#positivity",
        "#mindset",
        "#success",
        "#quotes",
    ]
    keyword_hashtags = [
        f"#{keyword.replace(' ', '')}" for keyword in quote_obj["keywords"]
    ]
    all_hashtags = list(set(hashtags + keyword_hashtags))
    selected_hashtags = " ".join(random.sample(all_hashtags, min(7, len(all_hashtags))))
    return f"{quote_obj['text']}\n\n{selected_hashtags}"