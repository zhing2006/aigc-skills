"""
Google Nano Banana Image Generation - Text/Image to Image Generation

Supported models: gemini-3.1-flash-image-preview (Nano Banana 2, default),
                  gemini-3-pro-image-preview (Nano Banana Pro)
Supported aspect ratios: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9,
                          4:1, 1:4, 8:1, 1:8 (Nano Banana 2 only)
Supported resolutions: 1K, 2K, 4K
Max input images: 14
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


SUPPORTED_MODELS = [
    "gemini-3.1-flash-image-preview",  # Nano Banana 2 (default)
    "gemini-3-pro-image-preview",      # Nano Banana Pro
]
SUPPORTED_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4",
    "9:16", "16:9", "21:9",
    "4:1", "1:4", "8:1", "1:8",  # Nano Banana 2 only
]
SUPPORTED_RESOLUTIONS = ["1K", "2K", "4K"]
MAX_INPUT_IMAGES = 14
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"


async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    model_id: str = DEFAULT_MODEL,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    search: bool = False,
    output_path: str | None = None,
) -> Path:
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {SUPPORTED_MODELS}")

    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}. Supported: {SUPPORTED_ASPECT_RATIOS}")

    if resolution.upper() not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if images and len(images) > MAX_INPUT_IMAGES:
        raise ValueError(f"Too many input images: {len(images)}. Maximum: {MAX_INPUT_IMAGES}")

    if search and model_id != "gemini-3.1-flash-image-preview":
        raise ValueError(
            "Image Search grounding is only supported with "
            "gemini-3.1-flash-image-preview (Nano Banana 2)"
        )

    use_vertex_ai = os.environ.get("USE_VERTEX_AI", "false").lower() == "true"
    if use_vertex_ai:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

        client = genai.Client(vertexai=True, project=project, location=location)
    else:
        api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_CLOUD_API_KEY environment variable is not set")

        client = genai.Client(api_key=api_key)

    # Build contents with prompt and optional images
    contents: list = [prompt]
    if images:
        for image_path in images:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            contents.append(Image.open(path))

    config_kwargs = {
        "response_modalities": ["TEXT", "IMAGE"],
        "image_config": types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution.upper(),
            output_mime_type="image/png",
        ),
    }
    if search:
        config_kwargs["search_types"] = ["IMAGE"]

    config = types.GenerateContentConfig(**config_kwargs)

    # Print prompt before generation
    print(f"Prompt: {prompt}")
    search_str = ", search grounding" if search else ""
    print(f"Generating image ({aspect_ratio}, {resolution.upper()}, model: {model_id}{search_str})...")

    output_file = Path(output_path) if output_path else Path("generated_image.png")

    # Use non-streaming API to avoid aiohttp "Chunk too big" error
    # when receiving large inline image data
    response = await client.aio.models.generate_content(
        model=model_id,
        contents=contents,
        config=config,
    )

    if response.parts:
        for part in response.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                image = part.as_image()
                image.save(output_file)

    print(f"Image saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Google Nano Banana (Gemini Image)"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text prompt for image generation",
    )
    parser.add_argument(
        "-i", "--images",
        type=str,
        nargs="*",
        help=f"Input image file paths (max {MAX_INPUT_IMAGES})",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-a", "--aspect-ratio",
        type=str,
        default="1:1",
        choices=SUPPORTED_ASPECT_RATIOS,
        help="Aspect ratio (default: 1:1)",
    )
    parser.add_argument(
        "-r", "--resolution",
        type=str,
        default="1K",
        choices=SUPPORTED_RESOLUTIONS,
        help="Output resolution (default: 1K)",
    )
    parser.add_argument(
        "-s", "--search",
        action="store_true",
        help="Enable Image Search grounding (Nano Banana 2 only)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: generated_image.png)",
    )

    args = parser.parse_args()

    try:
        await generate_image(
            prompt=args.prompt,
            images=args.images,
            model_id=args.model,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            search=args.search,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
