"""
OpenAI GPT Image - Text/Image to Image Generation

Supported models: gpt-image-2 (default), gpt-image-1.5, gpt-image-1, gpt-image-1-mini
Supported sizes:
  - gpt-image-1.x: 1024x1024, 1536x1024 (landscape), 1024x1536 (portrait), auto
  - gpt-image-2: any WxH where both edges are multiples of 16, the long:short
    ratio is at most 3:1, the long edge is at most 3840, and the total pixel
    count is between 655,360 and 8,294,400. Above 2560x1440 is experimental.
    "auto" (default) lets the routing layer decide.
Supported quality: auto, high, medium, low
Max input images: 16 (for image edit)

Notes:
  - gpt-image-2 does not accept input_fidelity (always treated as high).
  - background=transparent is supported on gpt-image-2 since 2026-08 (preview),
    on both generate and edit, and requires output_format png or webp.
  - During the preview, opaque regions come back with alpha 252-254 instead of
    255 and edges can carry a grey halo. Pass --normalize-alpha to clip the
    near-opaque alpha back to 255.
"""

import argparse
import asyncio
import base64
import io
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

# gpt-image-2 size constraints (see module docstring)
GPT_IMAGE_2_EDGE_MULTIPLE = 16
GPT_IMAGE_2_MAX_EDGE = 3840
GPT_IMAGE_2_MAX_RATIO = 3.0
GPT_IMAGE_2_MIN_PIXELS = 655_360
GPT_IMAGE_2_MAX_PIXELS = 8_294_400  # 3840x2160
GPT_IMAGE_2_EXPERIMENTAL_PIXELS = 3_686_400  # above 2560x1440 is experimental

# Alpha at or above this value is treated as "meant to be fully opaque".
ALPHA_OPAQUE_THRESHOLD = 250

# Output formats that carry an alpha channel
ALPHA_FORMATS = ("png", "webp")

JPEG_SUFFIXES = (".jpg", ".jpeg")
SUFFIX_TO_FORMAT = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}


def validate_size(model: str, size: str) -> None:
    """Validate the size parameter against the model's supported set."""
    if size == "auto":
        return

    if model == "gpt-image-2":
        validate_gpt_image_2_size(size)
        return

    if model.startswith("gpt-image-1"):
        if size not in GPT_IMAGE_1_X_SIZES:
            raise ValueError(
                f"Unsupported size for {model}: {size}. Supported: {GPT_IMAGE_1_X_SIZES}"
            )
        return

    raise ValueError(f"Unknown model for size validation: {model}")


def validate_gpt_image_2_size(size: str) -> None:
    """Validate an explicit WxH size against gpt-image-2's constraints."""
    # No leniency on whitespace: the size string is forwarded to the API verbatim,
    # so anything we accept here has to be something the API accepts too.
    parts = size.lower().split("x")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise ValueError(
            f"Invalid size for gpt-image-2: {size}. Expected 'auto' or 'WIDTHxHEIGHT' "
            f"(e.g. 1536x864)."
        )

    width, height = (int(p) for p in parts)
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid size for gpt-image-2: {size}. Both edges must be positive.")

    if width % GPT_IMAGE_2_EDGE_MULTIPLE or height % GPT_IMAGE_2_EDGE_MULTIPLE:
        raise ValueError(
            f"Invalid size for gpt-image-2: {size}. Both edges must be multiples of "
            f"{GPT_IMAGE_2_EDGE_MULTIPLE}."
        )

    long_edge, short_edge = max(width, height), min(width, height)
    if long_edge > GPT_IMAGE_2_MAX_EDGE:
        raise ValueError(
            f"Invalid size for gpt-image-2: {size}. The long edge must be at most "
            f"{GPT_IMAGE_2_MAX_EDGE}px."
        )

    if long_edge / short_edge > GPT_IMAGE_2_MAX_RATIO:
        raise ValueError(
            f"Invalid size for gpt-image-2: {size}. The aspect ratio must be between "
            f"1:3 and 3:1."
        )

    pixels = width * height
    if pixels < GPT_IMAGE_2_MIN_PIXELS:
        raise ValueError(
            f"Invalid size for gpt-image-2: {size} ({pixels:,} pixels). At least "
            f"{GPT_IMAGE_2_MIN_PIXELS:,} pixels are required."
        )
    if pixels > GPT_IMAGE_2_MAX_PIXELS:
        raise ValueError(
            f"Invalid size for gpt-image-2: {size} ({pixels:,} pixels). At most "
            f"{GPT_IMAGE_2_MAX_PIXELS:,} pixels are supported."
        )

    if pixels > GPT_IMAGE_2_EXPERIMENTAL_PIXELS:
        print(
            f"Warning: {size} is {pixels:,} pixels, above the "
            f"{GPT_IMAGE_2_EXPERIMENTAL_PIXELS:,} (2560x1440) threshold OpenAI marks as "
            f"experimental. Generation may be slower or fail."
        )


def clip_alpha(image_bytes: bytes, output_format: str) -> bytes:
    """
    Clip near-opaque alpha back to 255.

    During the gpt-image-2 transparency preview, regions that should be fully
    opaque come back with alpha 252-254, which lets the backdrop bleed through
    when the asset is composited. Returns the bytes unchanged when the image has
    no alpha channel or already looks clean.
    """
    from PIL import Image

    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode != "RGBA":
            return image_bytes

        alpha = img.getchannel("A")
        _, high = alpha.getextrema()
        if high == 255 or high < ALPHA_OPAQUE_THRESHOLD:
            # Nothing to clip: already fully opaque somewhere, or genuinely
            # semi-transparent throughout (clipping would alter the artwork).
            return image_bytes

        img.putalpha(alpha.point(lambda a: 255 if a >= ALPHA_OPAQUE_THRESHOLD else a))
        buffer = io.BytesIO()
        if output_format == "webp":
            # Pillow's WebP encoder is lossy by default, which would degrade the
            # entire RGB layer for the sake of an alpha-only fix. exact=True also
            # keeps the RGB values hidden under fully transparent pixels.
            img.save(buffer, format="WEBP", lossless=True, exact=True)
        else:
            img.save(buffer, format="PNG")
        print(f"Normalized alpha: clipped max alpha {high} -> 255")
        return buffer.getvalue()


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
    normalize_alpha: bool = False,
) -> list[Path]:
    """
    Generate image(s) using OpenAI GPT Image API.

    Args:
        prompt: Text prompt for image generation (max 32000 characters)
        images: List of local image file paths for editing (max 16)
        model: Model to use (gpt-image-2, gpt-image-1.5, gpt-image-1, gpt-image-1-mini)
        size: Output size. "auto" (default) omits the param so the model decides.
              For gpt-image-1.x: 1024x1024, 1536x1024, 1024x1536, auto.
              For gpt-image-2: any WxH within the documented constraints (both
              edges multiples of 16, ratio 1:3-3:1, long edge <= 3840,
              655,360-8,294,400 pixels).
        quality: Image quality (auto, high, medium, low)
        output_format: Output format (png, jpeg, webp)
        background: Background type (auto, transparent, opaque)
        n: Number of images to generate (1-10)
        output_path: Output file path (optional)
        normalize_alpha: Clip near-opaque alpha (252-254) back to 255

    Returns:
        List of paths to generated image files
    """
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    # Normalize before validating, since the validated value is what gets sent.
    size = size.strip().lower()
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
    if background == "transparent" and output_format not in ALPHA_FORMATS:
        raise ValueError("Transparent background requires png or webp format, not jpeg")

    # The output extension is used verbatim, so reconcile it with --format here:
    # a .jpg name would strip the alpha channel in many viewers.
    if output_path:
        out_suffix = Path(output_path).suffix.lower()
        if background == "transparent" and out_suffix in JPEG_SUFFIXES:
            raise ValueError(
                f"Transparent background cannot be saved as {out_suffix}. "
                f"Use a .png or .webp output path."
            )
        expected_format = SUFFIX_TO_FORMAT.get(out_suffix)
        if expected_format and expected_format != output_format:
            print(
                f"Warning: output path ends in {out_suffix} but --format is "
                f"{output_format}; the file will contain {output_format} data."
            )

    if normalize_alpha and output_format not in ALPHA_FORMATS:
        print(f"Warning: --normalize-alpha has no effect with --format {output_format}.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    if os.environ.get("USE_AZURE_OPENAI", "false").lower() == "true":
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
        client = AsyncAzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=api_base)
        print("Using Azure OpenAI endpoint.")
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

            if normalize_alpha and output_format in ALPHA_FORMATS:
                image_bytes = await asyncio.to_thread(clip_alpha, image_bytes, output_format)

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
            "gpt-image-2 accepts any WIDTHxHEIGHT with both edges multiples of 16, "
            "ratio 1:3-3:1, long edge <= 3840, and 655,360-8,294,400 total pixels."
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
        help="Background type (default: auto). transparent requires png or webp",
    )
    parser.add_argument(
        "--normalize-alpha",
        action="store_true",
        help=(
            "Clip near-opaque alpha (252-254) back to 255, working around a known "
            "gpt-image-2 transparency preview defect. Only affects png and webp"
        ),
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
            normalize_alpha=args.normalize_alpha,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
