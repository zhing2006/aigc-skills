"""
Google Nano Banana Pro (Gemini 3 Pro Image) - Text/Image to Image Generation

Supported aspect ratios: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
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


SUPPORTED_ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
SUPPORTED_RESOLUTIONS = ["1K", "2K", "4K"]
MAX_INPUT_IMAGES = 14


async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    output_path: str | None = None,
) -> Path:
    """
    Generate an image using Google Nano Banana Pro (Gemini 3 Pro Image).

    Args:
        prompt: Text prompt for image generation
        images: List of local image file paths (max 14)
        aspect_ratio: Aspect ratio (1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9)
        resolution: Output resolution (1K, 2K, 4K)
        output_path: Output file path (optional, defaults to generated_image.png)

    Returns:
        Path to the generated image file
    """
    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}. Supported: {SUPPORTED_ASPECT_RATIOS}")

    if resolution.upper() not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if images and len(images) > MAX_INPUT_IMAGES:
        raise ValueError(f"Too many input images: {len(images)}. Maximum: {MAX_INPUT_IMAGES}")

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

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=resolution.upper(),
            output_mime_type="image/png",
        ),
    )

    # Print prompt before generation
    print(f"Prompt: {prompt}")
    print(f"Generating image ({aspect_ratio}, {resolution.upper()})...")

    output_file = Path(output_path) if output_path else Path("generated_image.png")

    # Stream response for real-time output (async)
    async for chunk in await client.aio.models.generate_content_stream(
        model="gemini-3-pro-image-preview",
        contents=contents,
        config=config,
    ):
        if chunk.parts:
            for part in chunk.parts:
                if part.text is not None:
                    print(part.text, end="", flush=True)
                elif part.inline_data is not None:
                    image = part.as_image()
                    image.save(output_file)

    print()  # Newline after streaming text
    print(f"Image saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Google Nano Banana Pro (Gemini 3 Pro Image)"
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
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())
