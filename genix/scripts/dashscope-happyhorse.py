"""
DashScope HappyHorse - Video Generation (Text / Image / Reference / Edit)

Generate physically realistic, smoothly-moving video using Alibaba Bailian
(DashScope) HappyHorse. The native API is asynchronous: create a task, then
poll until the video is ready. Four modes are supported, auto-detected from
the inputs you provide:

  Text-to-Video (t2v)        prompt only
  Image-to-Video (i2v)       --first-frame IMAGE  (prompt optional)
  Reference-to-Video (r2v)   --ref-image IMAGE ... (1-9, reference the images
                             in the prompt as [Image 1], [Image 2], ...)
  Video Edit (video-edit)    --video URL [--ref-image IMAGE ...] (0-5 refs)

Subcommands:
  generate  Create a video generation task and wait for the result (default)
  get       Query a single video generation task by ID

Models (suffix matches the mode; --version selects 1.1 or 1.0):
  happyhorse-1.1-t2v / happyhorse-1.0-t2v
  happyhorse-1.1-i2v / happyhorse-1.0-i2v
  happyhorse-1.1-r2v / happyhorse-1.0-r2v
  happyhorse-1.0-video-edit            (video edit is 1.0 only)

Supported resolutions: 720P, 1080P (default)
Supported ratios (t2v/r2v only): 16:9 (default), 9:16, 1:1, 4:3, 3:4, 4:5, 5:4, 9:21, 21:9
Supported durations (t2v/i2v/r2v): 3-15 seconds (default 5); video-edit follows the source
"""

import argparse
import asyncio
import base64
import mimetypes
import os
import sys
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


# Model groups by mode. The suffix encodes the mode; the middle token is the version.
T2V_MODELS = ["happyhorse-1.1-t2v", "happyhorse-1.0-t2v"]
I2V_MODELS = ["happyhorse-1.1-i2v", "happyhorse-1.0-i2v"]
R2V_MODELS = ["happyhorse-1.1-r2v", "happyhorse-1.0-r2v"]
EDIT_MODELS = ["happyhorse-1.0-video-edit"]
SUPPORTED_MODELS = T2V_MODELS + I2V_MODELS + R2V_MODELS + EDIT_MODELS

SUPPORTED_VERSIONS = ["1.1", "1.0"]
SUPPORTED_RESOLUTIONS = ["720P", "1080P"]
SUPPORTED_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "4:5", "5:4", "9:21", "21:9"]
SUPPORTED_AUDIO_SETTINGS = ["auto", "origin"]  # video-edit only

DEFAULT_VERSION = "1.1"
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

# Reference-image / first-frame count limits per mode
MAX_REF_IMAGES = {"r2v": 9, "video-edit": 5}
MIN_REF_IMAGES = {"r2v": 1, "video-edit": 0}


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


def encode_image_base64(image_path: str) -> str:
    """Encode a local image file to a base64 data URI per the API format."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def resolve_image_url(path_or_url: str) -> str:
    """Resolve an image path or URL. Local files are base64-encoded."""
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    return encode_image_base64(path_or_url)


def derive_model(mode: str, version: str) -> str:
    """Build the model ID from the detected mode and version selector."""
    if mode == "video-edit":
        return "happyhorse-1.0-video-edit"  # video edit is 1.0 only
    return f"happyhorse-{version}-{mode}"


def detect_mode(first_frame, ref_images, video) -> str:
    """Determine the generation mode from the provided inputs."""
    if video:
        return "video-edit"
    if first_frame:
        return "i2v"
    if ref_images:
        return "r2v"
    return "t2v"


# ──────────────────────────── generate ────────────────────────────


async def generate_video(
    prompt: str | None = None,
    first_frame: str | None = None,
    ref_images: list[str] | None = None,
    video: str | None = None,
    model: str | None = None,
    version: str = DEFAULT_VERSION,
    resolution: str = DEFAULT_RESOLUTION,
    ratio: str = DEFAULT_RATIO,
    duration: int = DEFAULT_DURATION,
    audio_setting: str | None = None,
    watermark: bool = True,
    seed: int | None = None,
    output_path: str | None = None,
) -> Path:
    """Generate a video using DashScope HappyHorse (t2v / i2v / r2v / video-edit)."""
    mode = detect_mode(first_frame, ref_images, video)

    # ── Cross-input validation ──
    if first_frame and ref_images:
        raise ValueError("--first-frame and --ref-image are mutually exclusive")
    if video and first_frame:
        raise ValueError("--first-frame is not used for video editing (use --ref-image)")

    if mode == "i2v":
        # prompt is optional for image-to-video
        pass
    elif not prompt:
        raise ValueError(f"A text prompt is required for {mode}")

    if mode == "r2v":
        n = len(ref_images)
        if n < MIN_REF_IMAGES["r2v"] or n > MAX_REF_IMAGES["r2v"]:
            raise ValueError("Reference-to-video requires 1 to 9 --ref-image inputs")
    if mode == "video-edit":
        if not (video.startswith("http://") or video.startswith("https://")):
            raise ValueError("--video must be a public http(s) URL (base64/local not supported)")
        n = len(ref_images) if ref_images else 0
        if n > MAX_REF_IMAGES["video-edit"]:
            raise ValueError("Video edit accepts at most 5 --ref-image inputs")

    if model is None:
        model = derive_model(mode, version)
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if ratio not in SUPPORTED_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio}. Supported: {SUPPORTED_RATIOS}")

    if duration < 3 or duration > 15:
        raise ValueError("Duration must be an integer between 3 and 15 seconds")

    if audio_setting is not None and audio_setting not in SUPPORTED_AUDIO_SETTINGS:
        raise ValueError(f"Unsupported audio_setting: {audio_setting}. Supported: {SUPPORTED_AUDIO_SETTINGS}")

    if seed is not None and (seed < 0 or seed > 2147483647):
        raise ValueError("Seed must be between 0 and 2147483647")

    api_key = get_api_key()
    base = get_base_url()

    # ── Build input.media by mode ──
    input_obj: dict = {}
    if prompt:
        input_obj["prompt"] = prompt

    media = []
    if mode == "i2v":
        media.append({"type": "first_frame", "url": resolve_image_url(first_frame)})
    elif mode == "r2v":
        for img in ref_images:
            media.append({"type": "reference_image", "url": resolve_image_url(img)})
    elif mode == "video-edit":
        media.append({"type": "video", "url": video})
        for img in (ref_images or []):
            media.append({"type": "reference_image", "url": resolve_image_url(img)})
    if media:
        input_obj["media"] = media

    # ── Build parameters by mode (only send what the mode accepts) ──
    parameters: dict = {"resolution": resolution, "watermark": watermark}
    if mode in ("t2v", "r2v"):
        parameters["ratio"] = ratio  # i2v follows the first frame; video-edit follows the source
    if mode in ("t2v", "i2v", "r2v"):
        parameters["duration"] = duration  # video-edit duration follows the source video
    if mode == "video-edit" and audio_setting:
        parameters["audio_setting"] = audio_setting
    if seed is not None:
        parameters["seed"] = seed

    payload = {"model": model, "input": input_obj, "parameters": parameters}

    output_file = Path(output_path) if output_path else Path("generated_video.mp4")

    mode_label = {
        "t2v": "Text-to-Video",
        "i2v": "Image-to-Video (first frame)",
        "r2v": "Reference-to-Video",
        "video-edit": "Video Edit",
    }[mode]
    print(f"Prompt: {prompt or '(none)'}")
    print(f"Generating video ({mode_label}, {resolution}, watermark={watermark}, model: {model})...")

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
        description="DashScope HappyHorse Video Generation (text / image / reference / edit)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── generate ──
    gen_parser = subparsers.add_parser("generate", help="Generate a video (default)")
    gen_parser.add_argument(
        "prompt", type=str, nargs="?", default=None,
        help="Text prompt (required except for image-to-video; "
             "for reference-to-video, refer to images as [Image 1], [Image 2], ...)",
    )
    gen_parser.add_argument(
        "-i", "--first-frame", type=str, default=None,
        help="First frame image path/URL -> Image-to-Video (i2v)",
    )
    gen_parser.add_argument(
        "--ref-image", type=str, action="append", default=None,
        help="Reference image path/URL (repeatable). 1-9 -> Reference-to-Video; "
             "with --video, 0-5 reference images for editing",
    )
    gen_parser.add_argument(
        "--video", type=str, default=None,
        help="Source video public URL -> Video Edit (video-edit)",
    )
    gen_parser.add_argument(
        "--version", type=str, default=DEFAULT_VERSION, choices=SUPPORTED_VERSIONS,
        help=f"Model version (default: {DEFAULT_VERSION}); video-edit is always 1.0",
    )
    gen_parser.add_argument(
        "-m", "--model", type=str, default=None, choices=SUPPORTED_MODELS,
        help="Explicit model ID (overrides mode/version derivation)",
    )
    gen_parser.add_argument(
        "-r", "--resolution", type=normalize_resolution, default=DEFAULT_RESOLUTION,
        choices=SUPPORTED_RESOLUTIONS,
        help=f"Video resolution (default: {DEFAULT_RESOLUTION})",
    )
    gen_parser.add_argument(
        "-a", "--ratio", type=str, default=DEFAULT_RATIO, choices=SUPPORTED_RATIOS,
        help=f"Aspect ratio (default: {DEFAULT_RATIO}); t2v/r2v only, ignored otherwise",
    )
    gen_parser.add_argument(
        "-d", "--duration", type=int, default=DEFAULT_DURATION,
        help=f"Duration in seconds, 3-15 (default: {DEFAULT_DURATION}); "
             "ignored for video-edit (follows the source)",
    )
    gen_parser.add_argument(
        "--audio-setting", type=str, default=None, choices=SUPPORTED_AUDIO_SETTINGS,
        help="Video-edit only: 'auto' (model decides) or 'origin' (keep source audio)",
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
            if not args.prompt and not args.first_frame and not args.ref_image and not args.video:
                gen_parser.error("At least a prompt, --first-frame, --ref-image, or --video is required")
            await generate_video(
                prompt=args.prompt,
                first_frame=args.first_frame,
                ref_images=args.ref_image,
                video=args.video,
                model=args.model,
                version=args.version,
                resolution=args.resolution,
                ratio=args.ratio,
                duration=args.duration,
                audio_setting=args.audio_setting,
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
