"""
OpenAI Sora - Text/Image to Video Generation

Supported models: sora-2, sora-2-pro
Supported durations: 4, 8, 12 seconds
Supported sizes: 720x1280, 1280x720, 1024x1792, 1792x1024
"""

import argparse
import asyncio
import io
import os
import sys
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from openai import AsyncOpenAI, AsyncAzureOpenAI
from PIL import Image


SUPPORTED_MODELS = ["sora-2", "sora-2-pro"]
SUPPORTED_DURATIONS = [4, 8, 12]
SUPPORTED_SIZES = ["720x1280", "1280x720", "1024x1792", "1792x1024"]
DEFAULT_MODEL = "sora-2"


def prepare_image_for_size(image_path: str, target_size: str) -> bytes:
    """
    Resize image to fit target size, padding with black if needed.

    Args:
        image_path: Path to the input image
        target_size: Target size string (e.g., "1280x720")

    Returns:
        PNG image bytes ready for API
    """
    # Parse target dimensions
    target_width, target_height = map(int, target_size.split("x"))

    # Open and convert image to RGB
    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA", "P"):
        # Convert to RGB, handling transparency
        background = Image.new("RGB", img.size, (0, 0, 0))
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    orig_width, orig_height = img.size

    # Check if resize is needed
    if orig_width == target_width and orig_height == target_height:
        # No resize needed, just return as PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    # Calculate scale to fit within target while maintaining aspect ratio
    scale_w = target_width / orig_width
    scale_h = target_height / orig_height
    scale = min(scale_w, scale_h)

    # Calculate new dimensions
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)

    # Resize image
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create black canvas and paste resized image centered
    canvas = Image.new("RGB", (target_width, target_height), (0, 0, 0))
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    canvas.paste(img_resized, (paste_x, paste_y))

    # Convert to bytes
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


async def generate_video(
    prompt: str,
    image: str | None = None,
    model: str = DEFAULT_MODEL,
    seconds: int = 4,
    size: str = "720x1280",
    output_path: str | None = None,
) -> Path:
    """
    Generate a video using OpenAI Sora API.

    Args:
        prompt: Text prompt for video generation
        image: Input image path for image-to-video (optional)
        model: Model to use (sora-2, sora-2-pro)
        seconds: Video duration in seconds (4, 8, 12)
        size: Output resolution (720x1280, 1280x720, 1024x1792, 1792x1024)
        output_path: Output file path (optional)

    Returns:
        Path to the generated video file
    """
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    if seconds not in SUPPORTED_DURATIONS:
        raise ValueError(f"Unsupported duration: {seconds}. Supported: {SUPPORTED_DURATIONS}")

    if size not in SUPPORTED_SIZES:
        raise ValueError(f"Unsupported size: {size}. Supported: {SUPPORTED_SIZES}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    if os.environ.get("USE_AZURE_OPENAI", "false").lower() == "true":
        client = AsyncOpenAI(api_key=api_key, base_url=api_base + "/openai/v1/")
        print("Using Azure OpenAI endpoint.")
    else:
        client = AsyncOpenAI(api_key=api_key, base_url=api_base)
        print("Using OpenAI endpoint.")

    output_file = Path(output_path) if output_path else Path("generated_video.mp4")

    # Print generation info
    print(f"Prompt: {prompt}")
    mode = "Image-to-Video" if image else "Text-to-Video"
    print(f"Generating video ({mode}, {size}, {seconds}s, model: {model})...")

    # Create video generation job
    if image:
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image}")

        # Prepare image: resize and pad with black if needed
        print(f"Preparing image to match target size {size}...")
        image_bytes = prepare_image_for_size(str(image_path), size)

        video = await client.videos.create(
            prompt=prompt,
            input_reference=("image.png", io.BytesIO(image_bytes), "image/png"),
            model=model,
            seconds=str(seconds),
            size=size,
        )
    else:
        video = await client.videos.create(
            prompt=prompt,
            model=model,
            seconds=str(seconds),
            size=size,
        )

    print(f"Video job created: {video.id}")

    # Poll until completion
    while True:
        video = await client.videos.retrieve(video.id)
        if video.status == "completed":
            break
        elif video.status == "failed":
            error_msg = video.error.message if video.error else "Unknown error"
            raise Exception(f"Video generation failed: {error_msg}")
        print(f"Status: {video.status}, Progress: {video.progress}%")
        await asyncio.sleep(5)

    # Download video content
    print("Downloading video...")
    response = await client.videos.download_content(video_id=video.id)

    async with aiofiles.open(output_file, "wb") as f:
        await f.write(response.content)

    print(f"Video saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate videos using OpenAI Sora API"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text prompt for video generation",
    )
    parser.add_argument(
        "-i", "--image",
        type=str,
        default=None,
        help="Input image file path for image-to-video",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=4,
        choices=SUPPORTED_DURATIONS,
        help="Duration in seconds (default: 4)",
    )
    parser.add_argument(
        "-s", "--size",
        type=str,
        default="720x1280",
        choices=SUPPORTED_SIZES,
        help="Output resolution (default: 720x1280)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: generated_video.mp4)",
    )

    args = parser.parse_args()

    try:
        await generate_video(
            prompt=args.prompt,
            image=args.image,
            model=args.model,
            seconds=args.duration,
            size=args.size,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())
