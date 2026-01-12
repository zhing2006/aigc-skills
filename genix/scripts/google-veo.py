"""
Google Veo 3.1 - Text/Image to Video Generation

Supported models: veo-3.1-generate-001, veo-3.1-fast-generate-001
Supported aspect ratios: 16:9, 9:16
Supported durations: 4, 6, 8 seconds
Supported resolutions: 720p, 1080p (1080p only with 8s + 16:9)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


SUPPORTED_MODELS = [
    "veo-3.1-generate-001",
    "veo-3.1-fast-generate-001",
]
SUPPORTED_ASPECT_RATIOS = ["16:9", "9:16"]
SUPPORTED_DURATIONS = [4, 6, 8]
SUPPORTED_RESOLUTIONS = ["720p", "1080p"]
DEFAULT_MODEL = "veo-3.1-generate-001"


async def generate_video(
    prompt: str,
    image: str | None = None,
    model_id: str = DEFAULT_MODEL,
    aspect_ratio: str = "16:9",
    duration: int = 8,
    resolution: str = "720p",
    negative_prompt: str | None = None,
    seed: int | None = None,
    output_path: str | None = None,
) -> Path:
    """
    Generate a video using Google Veo 3.1.

    Args:
        prompt: Text prompt for video generation
        image: Input image path for image-to-video (optional)
        model_id: Model to use for generation
        aspect_ratio: Video aspect ratio (16:9 or 9:16)
        duration: Video duration in seconds (4, 6, or 8)
        resolution: Video resolution (720p or 1080p)
        negative_prompt: Content to avoid generating
        seed: Seed for reproducibility
        output_path: Output file path (optional)

    Returns:
        Path to the generated video file
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {SUPPORTED_MODELS}")

    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}. Supported: {SUPPORTED_ASPECT_RATIOS}")

    if duration not in SUPPORTED_DURATIONS:
        raise ValueError(f"Unsupported duration: {duration}. Supported: {SUPPORTED_DURATIONS}")

    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if seed is not None and (seed < 0 or seed > 4294967295):
        raise ValueError("Seed must be between 0 and 4294967295")

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

    # Build config
    config_params = {
        "aspect_ratio": aspect_ratio,
        "duration_seconds": duration,
        "resolution": resolution,
    }

    if negative_prompt:
        config_params["negative_prompt"] = negative_prompt

    if seed is not None:
        config_params["seed"] = seed

    config = types.GenerateVideosConfig(**config_params)

    # Load image if provided
    input_image = None
    if image:
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image}")
        input_image = types.Image.from_file(location=image)

    output_file = Path(output_path) if output_path else Path("generated_video.mp4")

    # Print generation info
    print(f"Prompt: {prompt}")
    mode = "Image-to-Video" if input_image else "Text-to-Video"
    print(f"Generating video ({mode}, {aspect_ratio}, {duration}s, {resolution}, model: {model_id})...")

    # Generate video (async)
    if input_image:
        operation = await client.aio.models.generate_videos(
            model=model_id,
            prompt=prompt,
            image=input_image,
            config=config,
        )
    else:
        operation = await client.aio.models.generate_videos(
            model=model_id,
            prompt=prompt,
            config=config,
        )

    # Poll until completion (async)
    poll_count = 0
    while not operation.done:
        poll_count += 1
        print(f"Waiting for video generation... ({poll_count * 10}s)")
        await asyncio.sleep(10)
        operation = await client.aio.operations.get(operation)

    # Save video
    video = operation.response.generated_videos[0].video
    video.save(output_file)

    print(f"Video saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate videos using Google Veo 3.1"
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
        "-a", "--aspect-ratio",
        type=str,
        default="16:9",
        choices=SUPPORTED_ASPECT_RATIOS,
        help="Aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=8,
        choices=SUPPORTED_DURATIONS,
        help="Duration in seconds (default: 8)",
    )
    parser.add_argument(
        "-r", "--resolution",
        type=str,
        default="720p",
        choices=SUPPORTED_RESOLUTIONS,
        help="Resolution (default: 720p). Note: 1080p only with 8s + 16:9",
    )
    parser.add_argument(
        "-n", "--negative-prompt",
        type=str,
        default=None,
        help="Content to avoid generating",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for reproducibility (0-4294967295)",
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
            model_id=args.model,
            aspect_ratio=args.aspect_ratio,
            duration=args.duration,
            resolution=args.resolution,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
