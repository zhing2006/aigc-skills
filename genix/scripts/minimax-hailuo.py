"""
MiniMax Hailuo (MiniMax-H3) - Text/Image/Multi-modal Reference to Video Generation

Generate 2K video with native synchronized audio using the MiniMax video
generation V2 API (Hailuo-03). The API is asynchronous: create a task, then poll
until the video is ready. Three modes are supported, auto-detected from the
inputs you provide:

  Text-to-Video (t2va)        prompt only; --ratio is required and cannot be 'adaptive'
  Image-to-Video (i2va)       --first-frame and/or --last-frame (1-2 images)
  Reference-to-Video (r2va)   --ref-image / --ref-video / --ref-audio; refer to them
                              in the prompt as 参考图1 / 参考视频1 / 音色参考音频1

A non-empty text prompt is required in *every* mode. First/last frame mode and
multi-modal reference mode are mutually exclusive.

Subcommands:
  generate  Create a video generation task and wait for the result (default)
  get       Query a single video generation task by ID
  list      List recent video generation tasks (last 7 days only)
  delete    Cancel a queued task, or delete a task in a terminal state

Supported model: MiniMax-H3
Supported resolution: 2K (the only value the API accepts)
Supported ratios: adaptive (default), 21:9, 16:9, 4:3, 1:1, 3:4, 9:16
Supported durations: 4-15 seconds (integer, default 5)
"""

import argparse
import asyncio
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


SUPPORTED_MODELS = ["MiniMax-H3"]
DEFAULT_MODEL = "MiniMax-H3"

# The V2 API exposes a single resolution tier. The older V1 endpoints (720P /
# 768P / 1080P) are a separate API family and are not covered by this script.
SUPPORTED_RESOLUTIONS = ["2K"]
DEFAULT_RESOLUTION = "2K"

SUPPORTED_RATIOS = ["adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
DEFAULT_RATIO = "adaptive"
DEFAULT_T2V_RATIO = "16:9"  # text-to-video must pick a concrete ratio

DEFAULT_DURATION = 5
MIN_DURATION = 4
MAX_DURATION = 15

SUPPORTED_STATUSES = ["queued", "running", "succeeded", "failed", "cancelled", "expired"]

DEFAULT_BASE_URL = "https://api.minimaxi.com"

POLL_INTERVAL = 10  # seconds; the docs recommend ~10s between polls

MAX_PROMPT_CHARS = 7000

# Reference asset counts (multi-modal reference mode)
MAX_REF_IMAGES = 9
MAX_REF_VIDEOS = 3
MAX_REF_AUDIOS = 3
MAX_REF_ASSETS = 12  # combined cap across images + videos + audio

# Request body cap. Base64 inflates payloads by ~33%, so large media should be
# passed as a public URL or an mm_file:// reference instead.
MAX_BODY_BYTES = 64 * 1024 * 1024

# Per-media-kind limits and the extensions the API accepts. MIME types are mapped
# explicitly so the generated data URI does not depend on the OS mimetypes registry.
MEDIA_SPECS = {
    "image": {
        "max_bytes": 30 * 1024 * 1024,
        "mime_types": {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".heic": "image/heic",
            ".heif": "image/heif",
        },
    },
    "video": {
        "max_bytes": 50 * 1024 * 1024,
        "mime_types": {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
        },
    },
    "audio": {
        "max_bytes": 15 * 1024 * 1024,
        "mime_types": {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
        },
    },
}

# URL forms the API accepts as-is: public URLs, data URIs, and mm_file://{file_id}
# references to files already on the MiniMax platform.
PASSTHROUGH_PREFIXES = ("http://", "https://", "data:", "mm_file://")


def get_api_key() -> str:
    """Get MiniMax API key from environment."""
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY environment variable is not set")
    return api_key


def get_base_url() -> str:
    """Resolve the API host (no trailing slash)."""
    return os.environ.get("MINIMAX_API_BASE", DEFAULT_BASE_URL).rstrip("/")


def create_task_url(base: str) -> str:
    return f"{base}/v2/video_generation"


def query_task_url(base: str, task_id: str) -> str:
    return f"{base}/v2/query/video_generation/{task_id}"


def list_tasks_url(base: str) -> str:
    return f"{base}/v2/query/video_generation"


def delete_task_url(base: str, task_id: str) -> str:
    return f"{base}/v2/video_generation/{task_id}"


def normalize_resolution(value: str) -> str:
    """Accept 2k in any case; canonicalize to uppercase '2K'."""
    return value.upper()


def format_timestamp(ts: int | None) -> str:
    """Format a Unix timestamp to human-readable string."""
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def validate_local_media(media_path: str, kind: str) -> str | None:
    """Check a local media file and return its MIME type. Pass-through URLs return None."""
    if media_path.startswith(PASSTHROUGH_PREFIXES):
        return None

    spec = MEDIA_SPECS[kind]
    path = Path(media_path)
    if not path.exists():
        raise FileNotFoundError(f"{kind.capitalize()} file not found: {media_path}")

    suffix = path.suffix.lower()
    mime_type = spec["mime_types"].get(suffix)
    if not mime_type:
        supported = sorted(spec["mime_types"])
        raise ValueError(f"Unsupported {kind} format '{suffix}': {media_path}. Supported: {supported}")

    size = path.stat().st_size
    if size > spec["max_bytes"]:
        raise ValueError(
            f"{kind.capitalize()} file is {size / 1024 / 1024:.1f}MB, over the "
            f"{spec['max_bytes'] // 1024 // 1024}MB limit: {media_path}. "
            "Pass a public URL or an mm_file://{file_id} reference instead."
        )

    return mime_type


def encode_media_base64(media_path: str, kind: str) -> str:
    """Encode a local media file to a base64 data URI per the API format."""
    mime_type = validate_local_media(media_path, kind)

    with open(media_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def resolve_media_url(path_or_url: str, kind: str) -> str:
    """Resolve a media path or URL. Local files are base64-encoded."""
    if path_or_url.startswith(PASSTHROUGH_PREFIXES):
        return path_or_url
    return encode_media_base64(path_or_url, kind)


def resolve_image_url(path_or_url: str) -> str:
    return resolve_media_url(path_or_url, "image")


def resolve_video_url(path_or_url: str) -> str:
    return resolve_media_url(path_or_url, "video")


def resolve_audio_url(path_or_url: str) -> str:
    return resolve_media_url(path_or_url, "audio")


def detect_mode(first_frame, last_frame, ref_images, ref_videos, ref_audios) -> str:
    """Determine the generation mode from the provided inputs."""
    if ref_images or ref_videos or ref_audios:
        return "r2va"
    if first_frame or last_frame:
        return "i2va"
    return "t2va"


def resolve_ratio(mode: str, ratio: str | None) -> str:
    """Apply the per-mode aspect ratio rules."""
    if mode == "t2va":
        if ratio is None:
            return DEFAULT_T2V_RATIO
        if ratio == "adaptive":
            concrete = [r for r in SUPPORTED_RATIOS if r != "adaptive"]
            raise ValueError(
                f"Text-to-video requires a concrete aspect ratio; 'adaptive' is not allowed. Supported: {concrete}"
            )
        return ratio
    if mode == "i2va":
        # The aspect ratio is derived from the input image; the API ignores anything else.
        if ratio is not None and ratio != "adaptive":
            print(f"Note: --ratio {ratio} is ignored for image-to-video; the ratio follows the input image")
        return "adaptive"
    return ratio or DEFAULT_RATIO


def format_api_error(action: str, status: int, data: dict, text: str) -> str:
    """Build an error message from MiniMax's OpenAI-style error body."""
    error = data.get("error") or {}
    code = error.get("http_code") or status
    message = error.get("message") or (text.strip() or f"HTTP {status}")
    request_id = data.get("request_id")
    suffix = f" [request_id: {request_id}]" if request_id else ""
    return f"Failed to {action} ({code}): {message}{suffix}"


async def request_json(session, method: str, url: str, action: str, **kwargs) -> dict:
    """Send a request and return the parsed JSON body, raising on API errors."""
    async with session.request(method, url, **kwargs) as resp:
        text = await resp.text()
        try:
            data = json.loads(text) if text.strip() else {}
        except json.JSONDecodeError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        # Errors normally carry a real HTTP status, but guard against a 200 + error body.
        if resp.status != 200 or data.get("type") == "error":
            raise Exception(format_api_error(action, resp.status, data, text))
        return data


# ──────────────────────────── generate ────────────────────────────


async def generate_video(
    prompt: str | None = None,
    first_frame: str | None = None,
    last_frame: str | None = None,
    ref_images: list[str] | None = None,
    ref_videos: list[str] | None = None,
    ref_audios: list[str] | None = None,
    model: str = DEFAULT_MODEL,
    resolution: str = DEFAULT_RESOLUTION,
    ratio: str | None = None,
    duration: int = DEFAULT_DURATION,
    watermark: bool = False,
    output_path: str | None = None,
) -> Path:
    """Generate a video using MiniMax Hailuo (t2va / i2va / r2va)."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if ratio is not None and ratio not in SUPPORTED_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio}. Supported: {SUPPORTED_RATIOS}")

    if duration < MIN_DURATION or duration > MAX_DURATION:
        raise ValueError(f"Duration must be an integer between {MIN_DURATION} and {MAX_DURATION} seconds")

    mode = detect_mode(first_frame, last_frame, ref_images, ref_videos, ref_audios)

    # ── Cross-input validation ──
    if (first_frame or last_frame) and (ref_images or ref_videos or ref_audios):
        raise ValueError(
            "Image-to-video (--first-frame / --last-frame) and multi-modal reference "
            "(--ref-image / --ref-video / --ref-audio) are mutually exclusive"
        )

    # Unlike some providers, the API rejects any request without a non-empty text item.
    if not prompt or not prompt.strip():
        raise ValueError("A non-empty text prompt is required in every mode")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"Prompt is {len(prompt)} characters; the limit is {MAX_PROMPT_CHARS}")

    if ref_audios and not (ref_images or ref_videos):
        raise ValueError("--ref-audio cannot be used alone; add at least one --ref-image or --ref-video")

    if ref_images and len(ref_images) > MAX_REF_IMAGES:
        raise ValueError(f"At most {MAX_REF_IMAGES} --ref-image inputs are allowed (got {len(ref_images)})")
    if ref_videos and len(ref_videos) > MAX_REF_VIDEOS:
        raise ValueError(f"At most {MAX_REF_VIDEOS} --ref-video inputs are allowed (got {len(ref_videos)})")
    if ref_audios and len(ref_audios) > MAX_REF_AUDIOS:
        raise ValueError(f"At most {MAX_REF_AUDIOS} --ref-audio inputs are allowed (got {len(ref_audios)})")

    ref_total = len(ref_images or []) + len(ref_videos or []) + len(ref_audios or [])
    if ref_total > MAX_REF_ASSETS:
        raise ValueError(f"At most {MAX_REF_ASSETS} reference assets in total are allowed (got {ref_total})")

    # Check local media (existence / format / size) before touching the network.
    for kind, inputs in (
        ("image", [p for p in (first_frame, last_frame) if p] + list(ref_images or [])),
        ("video", list(ref_videos or [])),
        ("audio", list(ref_audios or [])),
    ):
        for media in inputs:
            validate_local_media(media, kind)

    ratio = resolve_ratio(mode, ratio)

    api_key = get_api_key()
    base = get_base_url()

    # ── Build the multi-modal content array ──
    content: list[dict] = [{"type": "text", "text": prompt}]

    if first_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": resolve_image_url(first_frame)},
            "role": "first_frame",
        })

    if last_frame:
        # A last frame on its own is a valid mode; it does not require a first frame.
        content.append({
            "type": "image_url",
            "image_url": {"url": resolve_image_url(last_frame)},
            "role": "last_frame",
        })

    for img in ref_images or []:
        content.append({
            "type": "image_url",
            "image_url": {"url": resolve_image_url(img)},
            "role": "reference_image",
        })

    for vid in ref_videos or []:
        content.append({
            "type": "video_url",
            "video_url": {"url": resolve_video_url(vid)},
            "role": "reference_video",
        })

    for aud in ref_audios or []:
        content.append({
            "type": "audio_url",
            "audio_url": {"url": resolve_audio_url(aud)},
            "role": "reference_audio",
        })

    payload = {
        "model": model,
        "content": content,
        "resolution": resolution,
        "duration": duration,
        "ratio": ratio,
    }
    if watermark:
        payload["aigc_watermark"] = True

    body_bytes = len(json.dumps(payload).encode("utf-8"))
    if body_bytes > MAX_BODY_BYTES:
        raise ValueError(
            f"Request body is {body_bytes / 1024 / 1024:.1f}MB, over the "
            f"{MAX_BODY_BYTES // 1024 // 1024}MB limit. Base64 inflates media by ~33% — "
            "pass large files as a public URL or an mm_file://{file_id} reference instead."
        )

    output_file = Path(output_path) if output_path else Path("generated_video.mp4")

    mode_label = {
        "t2va": "Text-to-Video",
        "i2va": "Image-to-Video",
        "r2va": "Multi-modal Reference",
    }[mode]
    print(f"Prompt: {prompt}")
    print(
        f"Generating video ({mode_label}, {ratio}, {duration}s, {resolution}, "
        f"watermark={watermark}, model: {model})..."
    )

    async with aiohttp.ClientSession() as session:
        # ── Step 1: create the async task ──
        create_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = await request_json(
            session, "POST", create_task_url(base), "create task",
            headers=create_headers, json=payload,
        )
        task_id = data.get("task_id")
        if not task_id:
            raise Exception(f"No task_id returned: {data}")
        print(f"Task created: {task_id}")

        # ── Step 2: poll until the task finishes ──
        query_headers = {"Authorization": f"Bearer {api_key}"}
        poll_count = 0
        video_url = None
        while True:
            data = await request_json(
                session, "GET", query_task_url(base, task_id), "query task",
                headers=query_headers,
            )
            task = data.get("task") or {}
            status = task.get("status")

            if status == "succeeded":
                print("Task succeeded!")
                video_url = (task.get("content") or {}).get("url")
                break
            elif status == "failed":
                error = task.get("error") or {}
                code = error.get("code", "Unknown")
                message = error.get("message", "Unknown error")
                raise Exception(f"Video generation failed ({code}): {message}")
            elif status in ("cancelled", "expired"):
                raise Exception(f"Task ended with status: {status}")
            elif status not in ("queued", "running"):
                raise Exception(f"Unexpected task status: {status}")
            else:
                poll_count += 1
                print(f"Status: {status}, waiting... ({poll_count * POLL_INTERVAL}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

        if not video_url:
            raise Exception("No video URL found in task result")

        # ── Step 3: download the result (the URL expires, so fetch it now) ──
        print("Downloading video...")
        async with session.get(video_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download video: HTTP {resp.status}")
            async with aiofiles.open(output_file, "wb") as f:
                await f.write(await resp.read())

    print(f"Video saved to: {output_file}")

    return output_file


# ──────────────────────────── get ────────────────────────────


def print_task(task: dict) -> None:
    """Print task details."""
    content = task.get("content") or {}
    usage = task.get("usage") or {}
    error = task.get("error") or {}

    print(f"  ID:         {task.get('id', '-')}")
    print(f"  Model:      {task.get('model', '-')}")
    print(f"  Status:     {task.get('status', '-')}")
    print(f"  Duration:   {task.get('duration', '-')}s")
    print(f"  Ratio:      {task.get('ratio', '-')}")
    print(f"  Resolution: {task.get('resolution', '-')}")
    if task.get("task_type"):
        print(f"  Task Type:  {task['task_type']}")
    print(f"  Created:    {format_timestamp(task.get('created_at'))}")
    print(f"  Updated:    {format_timestamp(task.get('updated_at'))}")
    if usage:
        print(
            f"  Usage:      {usage.get('total_seconds', 0)}s billed "
            f"({usage.get('input_seconds', 0)}s input + {usage.get('output_seconds', 0)}s output, "
            f"{usage.get('input_image_count', 0)} image(s))"
        )
    if content.get("url"):
        print(f"  Video URL:  {content['url']}")
    if error:
        print(f"  Error:      {error.get('code', 'Unknown')}: {error.get('message', '')}")


async def get_task(task_id: str) -> None:
    """Query a single video generation task and print its details."""
    api_key = get_api_key()
    base = get_base_url()
    headers = {"Authorization": f"Bearer {api_key}"}

    async with aiohttp.ClientSession() as session:
        data = await request_json(
            session, "GET", query_task_url(base, task_id), "query task", headers=headers
        )

    print_task(data.get("task") or {})


# ──────────────────────────── list ────────────────────────────


async def list_tasks(
    status: str | None = None,
    model: str | None = None,
    task_ids: list[str] | None = None,
    task_type: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> None:
    """List video generation tasks from the last 7 days."""
    if status and status not in SUPPORTED_STATUSES:
        raise ValueError(f"Unsupported status: {status}. Supported: {SUPPORTED_STATUSES}")

    api_key = get_api_key()
    base = get_base_url()
    headers = {"Authorization": f"Bearer {api_key}"}

    # A list of tuples (rather than a dict) lets filter.task_ids repeat.
    params = [("page_num", str(page_num)), ("page_size", str(page_size))]
    if status:
        params.append(("filter.status", status))
    if model:
        params.append(("filter.model", model))
    if task_type:
        params.append(("filter.task_type", task_type))
    for tid in task_ids or []:
        params.append(("filter.task_ids", tid))

    async with aiohttp.ClientSession() as session:
        data = await request_json(
            session, "GET", list_tasks_url(base), "list tasks", headers=headers, params=params
        )

    items = data.get("items") or []
    print(f"Total tasks: {data.get('total', len(items))}")
    print(f"Page {page_num}, showing {len(items)} tasks")
    print("-" * 100)

    for task in items:
        print_task(task)
        print("-" * 100)


# ──────────────────────────── delete ────────────────────────────


async def delete_task(task_id: str) -> None:
    """Cancel a queued task, or delete a task that is already in a terminal state."""
    api_key = get_api_key()
    base = get_base_url()
    headers = {"Authorization": f"Bearer {api_key}"}

    async with aiohttp.ClientSession() as session:
        data = await request_json(
            session, "DELETE", delete_task_url(base, task_id),
            "cancel or delete task", headers=headers,
        )

    print(
        f"Task {data.get('task_id', task_id)}: "
        f"action={data.get('action', '-')}, status={data.get('status', '-')}"
    )


# ──────────────────────────── CLI ────────────────────────────


SUBCOMMANDS = {"generate", "get", "list", "delete"}


async def main():
    # Default to "generate" if the first arg is not a known subcommand
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "generate")

    parser = argparse.ArgumentParser(
        description="MiniMax Hailuo (MiniMax-H3) Video Generation (text / image / multi-modal reference)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── generate ──
    gen_parser = subparsers.add_parser("generate", help="Generate a video (default)")
    gen_parser.add_argument(
        "prompt", type=str, nargs="?", default=None,
        help="Text prompt (required in every mode; for multi-modal reference, "
             "refer to inputs as 参考图1, 参考视频1, 音色参考音频1, ...)",
    )
    gen_parser.add_argument(
        "-i", "--first-frame", type=str, default=None,
        help="First frame image path/URL -> Image-to-Video",
    )
    gen_parser.add_argument(
        "--last-frame", type=str, default=None,
        help="Last frame image path/URL (usable on its own or with --first-frame)",
    )
    gen_parser.add_argument(
        "--ref-image", type=str, action="append", default=None,
        help="Reference image path/URL (repeatable, max 9) -> Multi-modal Reference",
    )
    gen_parser.add_argument(
        "--ref-video", type=str, action="append", default=None,
        help="Reference video path/URL (repeatable, max 3, 2-15s each and <=15s total)",
    )
    gen_parser.add_argument(
        "--ref-audio", type=str, action="append", default=None,
        help="Reference audio path/URL (repeatable, max 3, requires ref image/video)",
    )
    gen_parser.add_argument(
        "-m", "--model", type=str, default=DEFAULT_MODEL, choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    gen_parser.add_argument(
        "-r", "--resolution", type=normalize_resolution, default=DEFAULT_RESOLUTION,
        choices=SUPPORTED_RESOLUTIONS,
        help=f"Video resolution (default: {DEFAULT_RESOLUTION}; the only value the API accepts)",
    )
    gen_parser.add_argument(
        "-a", "--ratio", type=str, default=None, choices=SUPPORTED_RATIOS,
        help=f"Aspect ratio. Text-to-video requires a concrete value (default: {DEFAULT_T2V_RATIO}); "
             "image-to-video always follows the input image; multi-modal reference defaults to adaptive",
    )
    gen_parser.add_argument(
        "-d", "--duration", type=int, default=DEFAULT_DURATION,
        help=f"Duration in seconds, {MIN_DURATION}-{MAX_DURATION} (default: {DEFAULT_DURATION})",
    )
    gen_parser.add_argument(
        "--watermark", action="store_true",
        help="Add the AIGC identification watermark (default: off)",
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

    # ── list ──
    list_parser = subparsers.add_parser("list", help="List video generation tasks (last 7 days)")
    list_parser.add_argument(
        "-s", "--status", type=str, default=None, choices=SUPPORTED_STATUSES,
        help="Filter by status",
    )
    list_parser.add_argument(
        "-m", "--model", type=str, default=None,
        help="Filter by model name",
    )
    list_parser.add_argument(
        "--task-ids", type=str, nargs="+", default=None,
        help="Filter by specific task IDs",
    )
    list_parser.add_argument(
        "--task-type", type=str, default=None,
        help="Filter by task type (e.g. generation)",
    )
    list_parser.add_argument(
        "-p", "--page", type=int, default=1,
        help="Page number (default: 1)",
    )
    list_parser.add_argument(
        "-n", "--page-size", type=int, default=10,
        help="Page size (default: 10)",
    )

    # ── delete ──
    del_parser = subparsers.add_parser(
        "delete", help="Cancel a queued task, or delete a task in a terminal state"
    )
    del_parser.add_argument(
        "task_id", type=str,
        help="Task ID to cancel or delete",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "generate":
            if not args.prompt:
                gen_parser.error("A text prompt is required in every mode")
            await generate_video(
                prompt=args.prompt,
                first_frame=args.first_frame,
                last_frame=args.last_frame,
                ref_images=args.ref_image,
                ref_videos=args.ref_video,
                ref_audios=args.ref_audio,
                model=args.model,
                resolution=args.resolution,
                ratio=args.ratio,
                duration=args.duration,
                watermark=args.watermark,
                output_path=args.output,
            )
        elif args.command == "get":
            await get_task(args.task_id)
        elif args.command == "list":
            await list_tasks(
                status=args.status,
                model=args.model,
                task_ids=args.task_ids,
                task_type=args.task_type,
                page_num=args.page,
                page_size=args.page_size,
            )
        elif args.command == "delete":
            await delete_task(args.task_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
