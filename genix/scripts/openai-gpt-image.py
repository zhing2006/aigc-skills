"""
OpenAI GPT Image - Text/Image to Image Generation

Supported models: gpt-image-2 (default), gpt-image-1.5, gpt-image-1, gpt-image-1-mini
Supported sizes:
  - gpt-image-1.x: 1024x1024, 1536x1024 (landscape), 1024x1536 (portrait), auto
  - gpt-image-2: auto only (size is chosen by the model's routing layer; explicit
    sizes are rejected). Bias aspect ratio via the prompt instead.
Supported quality: auto, high, medium, low
Max input images: 16 (for image edit)

Note: gpt-image-2 does not accept input_fidelity (always treated as high) and
officially does not support background=transparent (transparency can still be
requested via the prompt; the model decides whether to emit an alpha channel).
"""

import argparse
import asyncio
import base64
import os
import sys
from pathlib import Path

import aiofiles
import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI, AsyncAzureOpenAI


SUPPORTED_MODELS = ["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]
GPT_IMAGE_1_X_SIZES = ["1024x1024", "1536x1024", "1024x1536", "auto"]
SUPPORTED_QUALITY = ["auto", "high", "medium", "low"]
SUPPORTED_FORMATS = ["png", "jpeg", "webp"]
SUPPORTED_BACKGROUNDS = ["auto", "transparent", "opaque"]
MAX_INPUT_IMAGES = 16


def validate_size(model: str, size: str) -> None:
    """Validate the size parameter against the model's supported set."""
    if model == "gpt-image-2":
        if size != "auto":
            raise ValueError(
                f"gpt-image-2 only supports size='auto' (routing layer decides). "
                f"Got: {size}. Bias aspect ratio via the prompt instead "
                f"(e.g. 'portrait composition', 'wide landscape', 'square 1:1')."
            )
        return

    if model.startswith("gpt-image-1"):
        if size not in GPT_IMAGE_1_X_SIZES:
            raise ValueError(
                f"Unsupported size for {model}: {size}. Supported: {GPT_IMAGE_1_X_SIZES}"
            )
        return

    raise ValueError(f"Unknown model for size validation: {model}")


async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    model: str = "gpt-image-2",
    size: str = "auto",
    quality: str = "auto",
    output_format: str = "png",
    background: str = "auto",
    n: int = 1,
    output_path: str | None = None,
) -> list[Path]:
    """
    Generate image(s) using OpenAI GPT Image API.

    Args:
        prompt: Text prompt for image generation (max 32000 characters)
        images: List of local image file paths for editing (max 16)
        model: Model to use (gpt-image-2, gpt-image-1.5, gpt-image-1, gpt-image-1-mini)
        size: Output size. "auto" (default) omits the param so the model decides.
              For gpt-image-1.x: 1024x1024, 1536x1024, 1024x1536, auto.
              For gpt-image-2: only "auto" is accepted; the routing layer chooses.
              Bias aspect ratio via the prompt for gpt-image-2.
        quality: Image quality (auto, high, medium, low)
        output_format: Output format (png, jpeg, webp)
        background: Background type (auto, transparent, opaque)
        n: Number of images to generate (1-10)
        output_path: Output file path (optional)

    Returns:
        List of paths to generated image files
    """
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    validate_size(model, size)

    if quality not in SUPPORTED_QUALITY:
        raise ValueError(f"Unsupported quality: {quality}. Supported: {SUPPORTED_QUALITY}")

    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {output_format}. Supported: {SUPPORTED_FORMATS}")

    if background not in SUPPORTED_BACKGROUNDS:
        raise ValueError(f"Unsupported background: {background}. Supported: {SUPPORTED_BACKGROUNDS}")

    if images and len(images) > MAX_INPUT_IMAGES:
        raise ValueError(f"Too many input images: {len(images)}. Maximum: {MAX_INPUT_IMAGES}")

    if n < 1 or n > 10:
        raise ValueError(f"Invalid n value: {n}. Must be between 1 and 10")

    # Transparent background requires png or webp
    if background == "transparent" and output_format == "jpeg":
        raise ValueError("Transparent background requires png or webp format, not jpeg")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    if os.environ.get("USE_AZURE_OPENAI", "false").lower() == "true":
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        client = AsyncAzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=api_base)
        print("Using Azure OpenAI endpoint with KEY:", api_key)
    else:
        client = AsyncOpenAI(api_key=api_key, base_url=api_base)
        print("Using OpenAI endpoint.")

    # Print info before generation
    print(f"Prompt: {prompt}")
    print(f"Generating {n} image(s) ({model}, {size}, {quality})...")

    output_files: list[Path] = []

    # Build kwargs; omit `size` when auto so the routing layer / server default
    # picks it. gpt-image-2 in particular only accepts auto.
    common_kwargs: dict = {
        "model": model,
        "prompt": prompt,
        "quality": quality,
        "output_format": output_format,
        "background": background,
        "n": n,
    }
    if size != "auto":
        common_kwargs["size"] = size

    if images:
        # Image edit mode
        image_files = []
        for image_path in images:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image_files.append(open(path, "rb"))

        try:
            response = await client.images.edit(
                image=image_files if len(image_files) > 1 else image_files[0],
                **common_kwargs,
            )
        finally:
            for f in image_files:
                f.close()
    else:
        # Text to image mode
        response = await client.images.generate(**common_kwargs)

    # Save generated images. The API may return either b64_json or url depending
    # on endpoint/model (Azure's gpt-image-2 routing sometimes returns url).
    http_client: "httpx.AsyncClient | None" = None
    try:
        for i, image_data in enumerate(response.data):
            if output_path:
                if n > 1:
                    base_path = Path(output_path)
                    file_path = base_path.parent / f"{base_path.stem}_{i+1}{base_path.suffix}"
                else:
                    file_path = Path(output_path)
            else:
                suffix = f"_{i+1}" if n > 1 else ""
                file_path = Path(f"generated_image{suffix}.{output_format}")

            if getattr(image_data, "b64_json", None):
                image_bytes = base64.b64decode(image_data.b64_json)
            elif getattr(image_data, "url", None):
                if http_client is None:
                    http_client = httpx.AsyncClient(timeout=120)
                resp = await http_client.get(image_data.url)
                resp.raise_for_status()
                image_bytes = resp.content
            else:
                raise ValueError(f"Image response item {i} has neither b64_json nor url")

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(image_bytes)

            output_files.append(file_path)
            print(f"Image saved to: {file_path}")
    finally:
        if http_client is not None:
            await http_client.aclose()

    return output_files


async def main():
    parser = argparse.ArgumentParser(
        description="Generate images using OpenAI GPT Image API"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text prompt for image generation (max 32000 characters)",
    )
    parser.add_argument(
        "-i", "--images",
        type=str,
        nargs="*",
        help=f"Input image file paths for editing (max {MAX_INPUT_IMAGES})",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="gpt-image-2",
        choices=SUPPORTED_MODELS,
        help="Model to use (default: gpt-image-2)",
    )
    parser.add_argument(
        "-s", "--size",
        type=str,
        default="auto",
        help=(
            "Output size (default: auto - omit to let model decide). "
            "gpt-image-1.x accepts: 1024x1024, 1536x1024, 1024x1536, auto. "
            "gpt-image-2 only accepts auto (routing layer chooses); "
            "bias aspect ratio via the prompt instead."
        ),
    )
    parser.add_argument(
        "-q", "--quality",
        type=str,
        default="auto",
        choices=SUPPORTED_QUALITY,
        help="Image quality (default: auto)",
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        default="png",
        choices=SUPPORTED_FORMATS,
        dest="output_format",
        help="Output format (default: png)",
    )
    parser.add_argument(
        "-b", "--background",
        type=str,
        default="auto",
        choices=SUPPORTED_BACKGROUNDS,
        help="Background type (default: auto)",
    )
    parser.add_argument(
        "-n", "--number",
        type=int,
        default=1,
        help="Number of images to generate (1-10, default: 1)",
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
            model=args.model,
            size=args.size,
            quality=args.quality,
            output_format=args.output_format,
            background=args.background,
            n=args.number,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
