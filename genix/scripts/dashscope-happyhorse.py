"""
DashScope HappyHorse - Text-to-Video Generation

Generate physically realistic, smoothly-moving video from a text prompt using
Alibaba Bailian (DashScope) HappyHorse. The native API is asynchronous:
create a task, then poll until the video is ready.

Subcommands:
  generate  Create a video generation task and wait for the result (default)
  get       Query a single video generation task by ID

Supported models: happyhorse-1.1-t2v, happyhorse-1.0-t2v
Supported resolutions: 720P, 1080P (default)
Supported ratios: 16:9 (default), 9:16, 1:1, 4:3, 3:4, 4:5, 5:4, 9:21, 21:9
Supported durations: 3-15 seconds (default 5)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


SUPPORTED_MODELS = [
    "happyhorse-1.1-t2v",
    "happyhorse-1.0-t2v",
]
SUPPORTED_RESOLUTIONS = ["720P", "1080P"]
SUPPORTED_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "4:5", "5:4", "9:21", "21:9"]
DEFAULT_MODEL = "happyhorse-1.1-t2v"
DEFAULT_RESOLUTION = "1080P"
DEFAULT_RATIO = "16:9"
DEFAULT_DURATION = 5

# Native (non-OpenAI-compatible) async API host. Override via DASHSCOPE_VIDEO_BASE_URL
# to target another region or a business-space domain, e.g.:
#   https://dashscope-intl.aliyuncs.com                (Singapore)
#   https://dashscope-us.aliyuncs.com                  (US, Virginia)
#   https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com (Beijing business space)
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"

POLL_INTERVAL = 15  # seconds; the docs recommend ~15s between polls


def get_api_key() -> str:
    """Get DashScope API key from environment."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    return api_key


def get_base_url() -> str:
    """Resolve the native async API host (no trailing slash)."""
    base = os.environ.get("DASHSCOPE_VIDEO_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    # Guard against accidentally pointing at the OpenAI-compatible base, which is a
    # different API surface that does not expose the async video-synthesis endpoint.
    if base.endswith("/compatible-mode/v1"):
        base = base[: -len("/compatible-mode/v1")]
    return base


def create_task_url(base: str) -> str:
    return f"{base}/api/v1/services/aigc/video-generation/video-synthesis"


def query_task_url(base: str, task_id: str) -> str:
    return f"{base}/api/v1/tasks/{task_id}"


def normalize_resolution(value: str) -> str:
    """Accept 720p/1080p in any case; canonicalize to uppercase 'P'."""
    return value.upper()


# ──────────────────────────── generate ────────────────────────────


async def generate_video(
    prompt: str,
    model: str = DEFAULT_MODEL,
    resolution: str = DEFAULT_RESOLUTION,
    ratio: str = DEFAULT_RATIO,
    duration: int = DEFAULT_DURATION,
    watermark: bool = True,
    seed: int | None = None,
    output_path: str | None = None,
) -> Path:
    """Generate a video using DashScope HappyHorse text-to-video."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if ratio not in SUPPORTED_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio}. Supported: {SUPPORTED_RATIOS}")

    if duration < 3 or duration > 15:
        raise ValueError("Duration must be an integer between 3 and 15 seconds")

    if seed is not None and (seed < 0 or seed > 2147483647):
        raise ValueError("Seed must be between 0 and 2147483647")

    if not prompt:
        raise ValueError("A text prompt is required")

    api_key = get_api_key()
    base = get_base_url()

    parameters = {
        "resolution": resolution,
        "ratio": ratio,
        "duration": duration,
        "watermark": watermark,
    }
    if seed is not None:
        parameters["seed"] = seed

    payload = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": parameters,
    }

    output_file = Path(output_path) if output_path else Path("generated_video.mp4")

    print(f"Prompt: {prompt}")
    print(f"Generating video (Text-to-Video, {ratio}, {duration}s, {resolution}, "
          f"watermark={watermark}, model: {model})...")

    async with aiohttp.ClientSession() as session:
        # ── Step 1: create the async task ──
        create_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        async with session.post(
            create_task_url(base), headers=create_headers, json=payload
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                code = data.get("code", resp.status)
                message = data.get("message", await resp.text())
                raise Exception(f"Failed to create task ({code}): {message}")

        output = data.get("output", {})
        task_id = output.get("task_id")
        if not task_id:
            raise Exception(f"No task_id returned: {data}")
        print(f"Task created: {task_id}")

        # ── Step 2: poll until the task finishes ──
        query_headers = {"Authorization": f"Bearer {api_key}"}
        poll_count = 0
        video_url = None
        while True:
            async with session.get(
                query_task_url(base, task_id), headers=query_headers
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    code = data.get("code", resp.status)
                    message = data.get("message", await resp.text())
                    raise Exception(f"Failed to query task ({code}): {message}")

            output = data.get("output", {})
            status = output.get("task_status")

            if status == "SUCCEEDED":
                print("Task succeeded!")
                video_url = output.get("video_url")
                break
            elif status == "FAILED":
                code = output.get("code", "Unknown")
                message = output.get("message", "Unknown error")
                raise Exception(f"Video generation failed ({code}): {message}")
            elif status in ("CANCELED", "UNKNOWN"):
                raise Exception(f"Task ended with status: {status}")
            else:
                # PENDING / RUNNING
                poll_count += 1
                print(f"Status: {status}, waiting... ({poll_count * POLL_INTERVAL}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

        if not video_url:
            raise Exception("No video URL found in task result")

        # ── Step 3: download the result (link valid for 24h) ──
        print("Downloading video...")
        async with session.get(video_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download video: HTTP {resp.status}")
            async with aiofiles.open(output_file, "wb") as f:
                await f.write(await resp.read())

    print(f"Video saved to: {output_file}")

    return output_file


# ──────────────────────────── get ────────────────────────────


async def get_task(task_id: str) -> None:
    """Query a single video generation task and print its details."""
    api_key = get_api_key()
    base = get_base_url()
    headers = {"Authorization": f"Bearer {api_key}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            query_task_url(base, task_id), headers=headers
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                code = data.get("code", resp.status)
                message = data.get("message", await resp.text())
                raise Exception(f"Failed to query task ({code}): {message}")

    output = data.get("output", {})
    usage = data.get("usage", {})

    print(f"  ID:         {output.get('task_id', task_id)}")
    print(f"  Status:     {output.get('task_status', '-')}")
    if output.get("submit_time"):
        print(f"  Submitted:  {output['submit_time']}")
    if output.get("end_time"):
        print(f"  Ended:      {output['end_time']}")
    if usage.get("SR"):
        print(f"  Resolution: {usage['SR']}")
    if usage.get("ratio"):
        print(f"  Ratio:      {usage['ratio']}")
    if usage.get("duration"):
        print(f"  Duration:   {usage['duration']}s")
    if output.get("orig_prompt"):
        print(f"  Prompt:     {output['orig_prompt']}")
    if output.get("video_url"):
        print(f"  Video URL:  {output['video_url']}")
    if output.get("code"):
        print(f"  Error:      {output.get('code')}: {output.get('message', '')}")


# ──────────────────────────── CLI ────────────────────────────


SUBCOMMANDS = {"generate", "get"}


async def main():
    # Default to "generate" if the first arg is not a known subcommand
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "generate")

    parser = argparse.ArgumentParser(
        description="DashScope HappyHorse Text-to-Video Generation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── generate ──
    gen_parser = subparsers.add_parser("generate", help="Generate a video (default)")
    gen_parser.add_argument(
        "prompt", type=str,
        help="Text prompt describing the video to generate",
    )
    gen_parser.add_argument(
        "-m", "--model", type=str, default=DEFAULT_MODEL, choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    gen_parser.add_argument(
        "-r", "--resolution", type=normalize_resolution, default=DEFAULT_RESOLUTION,
        choices=SUPPORTED_RESOLUTIONS,
        help=f"Video resolution (default: {DEFAULT_RESOLUTION})",
    )
    gen_parser.add_argument(
        "-a", "--ratio", type=str, default=DEFAULT_RATIO, choices=SUPPORTED_RATIOS,
        help=f"Aspect ratio (default: {DEFAULT_RATIO})",
    )
    gen_parser.add_argument(
        "-d", "--duration", type=int, default=DEFAULT_DURATION,
        help=f"Duration in seconds, 3-15 (default: {DEFAULT_DURATION})",
    )
    gen_parser.add_argument(
        "--no-watermark", action="store_true",
        help="Disable the 'Happy Horse' watermark (API adds it by default)",
    )
    gen_parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed 0-2147483647 for reproducibility",
    )
    gen_parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output file path (default: generated_video.mp4)",
    )

    # ── get ──
    get_parser = subparsers.add_parser("get", help="Get a single task by ID")
    get_parser.add_argument(
        "task_id", type=str,
        help="Task ID to query",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "generate":
            await generate_video(
                prompt=args.prompt,
                model=args.model,
                resolution=args.resolution,
                ratio=args.ratio,
                duration=args.duration,
                watermark=not args.no_watermark,
                seed=args.seed,
                output_path=args.output,
            )
        elif args.command == "get":
            await get_task(args.task_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
