"""
Volcengine Seedance 2.5 / 2.0 - Text/Image/Audio/Multi-modal to Video Generation

Subcommands:
  generate  Create a video generation task (default)
  get       Get a single video generation task
  list      List video generation tasks
  delete    Delete a video generation task

Supported models (resolutions | duration | max ref images/videos/audios):
  - doubao-seedance-2-5-260628 (default):  480p, 720p                | 4-30s | 30/10/10
  - doubao-seedance-2-0-260128 (full):     480p, 720p, 1080p, 4k     | 4-15s | 9/3/3
  - doubao-seedance-2-0-fast-260128:       480p, 720p                | 4-15s | 9/3/3
  - doubao-seedance-2-0-mini-260615:       480p, 720p                | 4-15s | 9/3/3
Supported ratios: 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive
  - Seedance 2.5 forces `adaptive` for first-frame / first+last-frame tasks; the
    output ratio follows the first frame.
Durations accept -1 to let the model pick a length.

Seedance 2.5 only:
  - mov output (--output-format mov) for high colour-precision editing pipelines
  - audio-only input (--ref-audio with no reference image or video)
  - 30-second coherent single-pass output
"""

import argparse
import asyncio
import base64
import mimetypes
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from volcenginesdkarkruntime import Ark


MODEL_SEEDANCE_2_5 = "doubao-seedance-2-5-260628"

SUPPORTED_MODELS = [
    MODEL_SEEDANCE_2_5,
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-2-0-mini-260615",
]
SUPPORTED_RESOLUTIONS = ["480p", "720p", "1080p", "4k"]
# Per-model resolution support. Seedance 2.5 and the 2.0 fast/mini variants top out
# at 720p; 1080p and 4k are exclusive to the full 2.0 model.
RESOLUTION_SUPPORT = {
    MODEL_SEEDANCE_2_5: ["480p", "720p"],
    "doubao-seedance-2-0-260128": ["480p", "720p", "1080p", "4k"],
    "doubao-seedance-2-0-fast-260128": ["480p", "720p"],
    "doubao-seedance-2-0-mini-260615": ["480p", "720p"],
}
SUPPORTED_RATIOS = ["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"]
SUPPORTED_STATUSES = ["queued", "running", "succeeded", "failed", "cancelled", "expired"]
# Statuses that end a task without producing a video. Polling must stop on these.
TERMINAL_FAILURE_STATUSES = {"failed", "cancelled", "expired"}
DEFAULT_MODEL = MODEL_SEEDANCE_2_5
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
POLL_INTERVAL = 10

# Seedance 2.5 generates up to 30 coherent seconds; the 2.0 series stops at 15.
DURATION_RANGE = {MODEL_SEEDANCE_2_5: (4, 30)}
DEFAULT_DURATION_RANGE = (4, 15)

# Per-request reference-asset counts. `seconds` is the combined video/audio duration
# cap the API enforces — reported in error messages, not checked locally (the script
# never decodes media).
MEDIA_LIMITS = {
    MODEL_SEEDANCE_2_5: {"images": 30, "videos": 10, "audios": 10, "seconds": 30},
}
DEFAULT_MEDIA_LIMITS = {"images": 9, "videos": 3, "audios": 3, "seconds": 15}

# Seedance 2.5 exclusives.
AUDIO_ONLY_MODELS = {MODEL_SEEDANCE_2_5}
OUTPUT_FORMAT_MODELS = {MODEL_SEEDANCE_2_5}
ADAPTIVE_ONLY_FRAME_MODELS = {MODEL_SEEDANCE_2_5}
SUPPORTED_OUTPUT_FORMATS = ["mp4", "mov"]

PRIORITY_RANGE = (0, 9)
EXPIRES_AFTER_RANGE = (3600, 259200)


def duration_range(model: str) -> tuple[int, int]:
    """Return the (min, max) duration in seconds allowed for a model."""
    return DURATION_RANGE.get(model, DEFAULT_DURATION_RANGE)


def media_limits(model: str) -> dict[str, int]:
    """Return the reference-asset limits for a model."""
    return MEDIA_LIMITS.get(model, DEFAULT_MEDIA_LIMITS)


def get_client() -> Ark:
    """Create and return an Ark client."""
    api_key = os.environ.get("VOLCENGINE_API_KEY")
    if not api_key:
        raise ValueError("VOLCENGINE_API_KEY environment variable is not set")
    base_url = os.environ.get("VOLCENGINE_API_BASE", DEFAULT_BASE_URL)
    return Ark(api_key=api_key, base_url=base_url)


def encode_image_base64(image_path: str) -> str:
    """Encode a local image file to base64 data URI."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    fmt = mime_type.split("/")[1].lower()

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:image/{fmt};base64,{encoded}"


def encode_audio_base64(audio_path: str) -> str:
    """Encode a local audio file to base64 data URI."""
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    mime_type = mimetypes.guess_type(str(path))[0] or "audio/wav"
    fmt = mime_type.split("/")[1].lower()

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:audio/{fmt};base64,{encoded}"


def resolve_image_url(path_or_url: str) -> str:
    """Resolve an image path or URL. Local files are base64-encoded."""
    if path_or_url.startswith(("http://", "https://", "data:", "asset://")):
        return path_or_url
    return encode_image_base64(path_or_url)


def resolve_audio_url(path_or_url: str) -> str:
    """Resolve an audio path or URL. Local files are base64-encoded."""
    if path_or_url.startswith(("http://", "https://", "data:", "asset://")):
        return path_or_url
    return encode_audio_base64(path_or_url)


def format_timestamp(ts: int | None) -> str:
    """Format a Unix timestamp to human-readable string."""
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ──────────────────────────── generate ────────────────────────────


async def generate_video(
    prompt: str | None = None,
    first_frame: str | None = None,
    last_frame: str | None = None,
    ref_images: list[str] | None = None,
    ref_videos: list[str] | None = None,
    ref_audios: list[str] | None = None,
    model: str = DEFAULT_MODEL,
    resolution: str = "720p",
    ratio: str | None = None,
    duration: int = 5,
    generate_audio: bool = True,
    watermark: bool = False,
    web_search: bool = False,
    return_last_frame: bool = False,
    output_format: str | None = None,
    priority: int | None = None,
    expires_after: int | None = None,
    output_path: str | None = None,
) -> Path:
    """Generate a video using Volcengine Seedance 2.5 / 2.0."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    allowed_resolutions = RESOLUTION_SUPPORT.get(model, SUPPORTED_RESOLUTIONS)
    if resolution not in allowed_resolutions:
        raise ValueError(
            f"Model {model} does not support resolution '{resolution}'. "
            f"Supported: {allowed_resolutions}"
        )

    if ratio is not None and ratio not in SUPPORTED_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio}. Supported: {SUPPORTED_RATIOS}")

    # Seedance 2.5 always matches the output ratio to the first frame, so an explicit
    # ratio is rejected by the API rather than ignored.
    if model in ADAPTIVE_ONLY_FRAME_MODELS and first_frame and ratio not in (None, "adaptive"):
        raise ValueError(
            f"Model {model} only supports ratio 'adaptive' for first-frame / "
            f"first+last-frame tasks; the output follows the first frame's ratio"
        )
    effective_ratio = ratio or "adaptive"

    min_duration, max_duration = duration_range(model)
    if duration != -1 and not min_duration <= duration <= max_duration:
        raise ValueError(
            f"Model {model} requires duration {min_duration}-{max_duration} seconds, "
            f"or -1 for auto"
        )

    if output_format is not None:
        if output_format not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(
                f"Unsupported output format: {output_format}. "
                f"Supported: {SUPPORTED_OUTPUT_FORMATS}"
            )
        if model not in OUTPUT_FORMAT_MODELS:
            raise ValueError(
                f"Model {model} does not support --output-format. "
                f"Supported models: {sorted(OUTPUT_FORMAT_MODELS)}"
            )

    if priority is not None and not PRIORITY_RANGE[0] <= priority <= PRIORITY_RANGE[1]:
        raise ValueError(
            f"Priority must be {PRIORITY_RANGE[0]}-{PRIORITY_RANGE[1]} (higher jumps the queue)"
        )

    if expires_after is not None and not (
        EXPIRES_AFTER_RANGE[0] <= expires_after <= EXPIRES_AFTER_RANGE[1]
    ):
        raise ValueError(
            f"Expires-after must be {EXPIRES_AFTER_RANGE[0]}-{EXPIRES_AFTER_RANGE[1]} seconds"
        )

    if last_frame and not first_frame:
        raise ValueError("Last frame requires first frame to be set")

    # First-frame, first+last-frame and multi-modal reference are three distinct task
    # types server-side and cannot be combined.
    if first_frame and (ref_images or ref_videos):
        raise ValueError(
            "First/last frame mode and multi-modal reference mode are mutually exclusive"
        )

    limits = media_limits(model)
    for kind, items in (("images", ref_images), ("videos", ref_videos), ("audios", ref_audios)):
        if items and len(items) > limits[kind]:
            raise ValueError(
                f"Model {model} accepts at most {limits[kind]} reference {kind} "
                f"(got {len(items)}). Combined reference video/audio duration must also "
                f"stay within {limits['seconds']}s."
            )

    client = get_client()

    # Build content array
    content = []

    if prompt:
        content.append({"type": "text", "text": prompt})

    if first_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": resolve_image_url(first_frame)},
            "role": "first_frame",
        })

    if last_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": resolve_image_url(last_frame)},
            "role": "last_frame",
        })

    if ref_images:
        for img in ref_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": resolve_image_url(img)},
                "role": "reference_image",
            })

    if ref_videos:
        for vid in ref_videos:
            content.append({
                "type": "video_url",
                "video_url": {"url": vid},
                "role": "reference_video",
            })

    if ref_audios:
        if not ref_images and not ref_videos and model not in AUDIO_ONLY_MODELS:
            raise ValueError(
                f"Model {model} requires at least one reference image or video alongside "
                f"reference audio. Audio-only input: {sorted(AUDIO_ONLY_MODELS)}"
            )
        for aud in ref_audios:
            content.append({
                "type": "audio_url",
                "audio_url": {"url": resolve_audio_url(aud)},
                "role": "reference_audio",
            })

    if not content:
        raise ValueError("At least a text prompt or input media is required")

    # Build request kwargs
    create_kwargs = {
        "model": model,
        "content": content,
        "resolution": resolution,
        "ratio": effective_ratio,
        "duration": duration,
        "generate_audio": generate_audio,
        "watermark": watermark,
    }

    if return_last_frame:
        create_kwargs["return_last_frame"] = True

    if web_search:
        create_kwargs["tools"] = [{"type": "web_search"}]

    if expires_after is not None:
        create_kwargs["execution_expires_after"] = expires_after

    # `output_format` and `priority` are absent from the installed Ark SDK's create()
    # signature, so they travel in extra_body, which the client merges into the JSON
    # body. Move them to named arguments once the SDK exposes them.
    extra_body = {}
    if output_format is not None:
        extra_body["output_format"] = output_format
    if priority is not None:
        extra_body["priority"] = priority
    if extra_body:
        create_kwargs["extra_body"] = extra_body

    if output_path:
        output_file = Path(output_path)
    else:
        output_file = Path(f"generated_video.{output_format or 'mp4'}")

    # Determine mode
    if first_frame and last_frame:
        mode = "First+Last Frame to Video"
    elif first_frame:
        mode = "First Frame to Video"
    elif ref_images or ref_videos:
        mode = "Multi-modal Reference to Video"
    elif ref_audios:
        mode = "Audio Reference to Video"
    else:
        mode = "Text-to-Video"

    print(f"Prompt: {prompt or '(none)'}")
    print(
        f"Generating video ({mode}, {effective_ratio}, {duration}s, {resolution}, "
        f"{output_format or 'mp4'}, audio={generate_audio}, model: {model})..."
    )

    # Create task
    result = client.content_generation.tasks.create(**create_kwargs)
    task_id = result.id
    print(f"Task created: {task_id}")

    # Poll until completion
    poll_count = 0
    while True:
        task = client.content_generation.tasks.get(task_id=task_id)
        status = task.status

        if status == "succeeded":
            print("Task succeeded!")
            break
        elif status in TERMINAL_FAILURE_STATUSES:
            error_msg = getattr(task, "error", None) or "Unknown error"
            raise Exception(f"Video generation {status}: {error_msg}")
        else:
            poll_count += 1
            print(f"Status: {status}, waiting... ({poll_count * POLL_INTERVAL}s elapsed)")
            await asyncio.sleep(POLL_INTERVAL)

    # Download video from result
    video_url = None
    if hasattr(task, "content") and task.content:
        video_url = task.content.video_url

    if not video_url:
        raise Exception("No video URL found in task result")

    print("Downloading video...")
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download video: HTTP {resp.status}")
            async with aiofiles.open(output_file, "wb") as f:
                await f.write(await resp.read())

        print(f"Video saved to: {output_file}")

        # Save the last frame image when requested (useful for chaining clips)
        last_frame_url = None
        if hasattr(task, "content") and task.content:
            last_frame_url = getattr(task.content, "last_frame_url", None)
        if return_last_frame and last_frame_url:
            frame_file = output_file.with_name(f"{output_file.stem}_last_frame.png")
            async with session.get(last_frame_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(frame_file, "wb") as f:
                        await f.write(await resp.read())
                    print(f"Last frame saved to: {frame_file}")

    return output_file


# ──────────────────────────── get ────────────────────────────


def print_task(task) -> None:
    """Print task details."""
    video_url = ""
    last_frame_url = ""
    if hasattr(task, "content") and task.content:
        video_url = getattr(task.content, "video_url", "") or ""
        last_frame_url = getattr(task.content, "last_frame_url", "") or ""

    print(f"  ID:         {task.id}")
    print(f"  Model:      {task.model}")
    print(f"  Status:     {task.status}")
    print(f"  Duration:   {task.duration}s")
    print(f"  Ratio:      {task.ratio}")
    print(f"  Resolution: {task.resolution}")
    print(f"  Created:    {format_timestamp(task.created_at)}")
    print(f"  Updated:    {format_timestamp(task.updated_at)}")
    if video_url:
        print(f"  Video URL:  {video_url}")
    if last_frame_url:
        print(f"  Last Frame: {last_frame_url}")
    if hasattr(task, "error") and task.error:
        print(f"  Error:      {task.error}")


def get_task(task_id: str) -> None:
    """Get a single video generation task."""
    client = get_client()
    task = client.content_generation.tasks.get(task_id=task_id)
    print_task(task)


# ──────────────────────────── list ────────────────────────────


def list_tasks(
    status: str | None = None,
    model: str | None = None,
    task_ids: list[str] | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> None:
    """List video generation tasks."""
    client = get_client()

    kwargs = {
        "page_num": page_num,
        "page_size": page_size,
    }
    if status:
        kwargs["status"] = status
    if model:
        kwargs["model"] = model
    if task_ids:
        kwargs["task_ids"] = task_ids

    result = client.content_generation.tasks.list(**kwargs)

    print(f"Total tasks: {result.total}")
    print(f"Page {page_num}, showing {len(result.items)} tasks")
    print("-" * 100)

    for task in result.items:
        print_task(task)
        print("-" * 100)


# ──────────────────────────── delete ────────────────────────────


def delete_task(task_id: str) -> None:
    """Delete a video generation task."""
    client = get_client()
    client.content_generation.tasks.delete(task_id=task_id)
    print(f"Task deleted: {task_id}")


# ──────────────────────────── CLI ────────────────────────────


SUBCOMMANDS = {"generate", "get", "list", "delete"}
HELP_FLAGS = {"-h", "--help"}


async def main():
    # Default to "generate" if first arg is not a known subcommand. Options are
    # included so a prompt-less invocation still reaches generate, e.g. audio-only
    # (`--ref-audio bgm.mp3`) or first-frame-only (`-i cat.png`).
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS and sys.argv[1] not in HELP_FLAGS:
        sys.argv.insert(1, "generate")

    parser = argparse.ArgumentParser(
        description="Volcengine Seedance 2.5 / 2.0 Video Generation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── generate ──
    gen_parser = subparsers.add_parser("generate", help="Generate a video (default)")
    gen_parser.add_argument(
        "prompt", type=str, nargs="?", default=None,
        help="Text prompt for video generation",
    )
    gen_parser.add_argument(
        "-i", "--first-frame", type=str, default=None,
        help="First frame image path/URL for image-to-video",
    )
    gen_parser.add_argument(
        "--last-frame", type=str, default=None,
        help="Last frame image path/URL (requires --first-frame)",
    )
    gen_parser.add_argument(
        "--ref-image", type=str, action="append", default=None,
        help="Reference image path/URL (repeatable; max 30 for Seedance 2.5, 9 for 2.0)",
    )
    gen_parser.add_argument(
        "--ref-video", type=str, action="append", default=None,
        help="Reference video URL (repeatable; max 10 for Seedance 2.5, 3 for 2.0)",
    )
    gen_parser.add_argument(
        "--ref-audio", type=str, action="append", default=None,
        help="Reference audio path/URL (repeatable; max 10 for Seedance 2.5, 3 for 2.0). "
             "Seedance 2.5 accepts audio alone; 2.0 also needs a ref image or video.",
    )
    gen_parser.add_argument(
        "-m", "--model", type=str, default=DEFAULT_MODEL, choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    gen_parser.add_argument(
        "-r", "--resolution", type=str, default="720p", choices=SUPPORTED_RESOLUTIONS,
        help="Video resolution (default: 720p). Seedance 2.5 and the 2.0 fast/mini "
             "variants support 480p/720p only; 1080p and 4k require "
             "doubao-seedance-2-0-260128.",
    )
    gen_parser.add_argument(
        "-a", "--ratio", type=str, default=None, choices=SUPPORTED_RATIOS,
        help="Aspect ratio (default: adaptive). Seedance 2.5 forces adaptive for "
             "first-frame/first+last-frame and video edit/extend tasks.",
    )
    gen_parser.add_argument(
        "-d", "--duration", type=int, default=5,
        help="Duration in seconds (default: 5). Seedance 2.5: 4-30; 2.0 series: 4-15; "
             "-1 lets the model choose. Seedance 2.5 video-edit tasks require -1.",
    )
    gen_parser.add_argument(
        "--no-audio", action="store_true",
        help="Disable audio generation (default: audio enabled)",
    )
    gen_parser.add_argument(
        "--watermark", action="store_true",
        help="Add watermark to video",
    )
    gen_parser.add_argument(
        "--web-search", action="store_true",
        help="Enable web search enhancement (text-to-video only)",
    )
    gen_parser.add_argument(
        "--return-last-frame", action="store_true",
        help="Also save the video's last frame as a PNG (for chaining clips)",
    )
    gen_parser.add_argument(
        "--output-format", type=str, default=None, choices=SUPPORTED_OUTPUT_FORMATS,
        help="Container/encoding of the generated video (Seedance 2.5 only, default mp4). "
             "mov keeps higher colour precision for editing/compositing pipelines.",
    )
    gen_parser.add_argument(
        "--priority", type=int, default=None,
        help="Queue priority 0-9; higher jumps ahead of lower-priority queued tasks "
             "on the same endpoint",
    )
    gen_parser.add_argument(
        "--expires-after", type=int, default=None,
        help="Seconds after creation before an unfinished task is marked expired "
             "(3600-259200, default 48h)",
    )
    gen_parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output file path (default: generated_video.<output-format>)",
    )

    # ── get ──
    get_parser = subparsers.add_parser("get", help="Get a single task by ID")
    get_parser.add_argument(
        "task_id", type=str,
        help="Task ID to query",
    )

    # ── list ──
    list_parser = subparsers.add_parser("list", help="List video generation tasks")
    list_parser.add_argument(
        "-s", "--status", type=str, default=None, choices=SUPPORTED_STATUSES,
        help="Filter by status",
    )
    list_parser.add_argument(
        "-m", "--model", type=str, default=None,
        help="Filter by model ID",
    )
    list_parser.add_argument(
        "--task-ids", type=str, nargs="+", default=None,
        help="Filter by specific task IDs",
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
    del_parser = subparsers.add_parser("delete", help="Delete a video generation task")
    del_parser.add_argument(
        "task_id", type=str,
        help="Task ID to delete",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "generate":
            if not any(
                (args.prompt, args.first_frame, args.ref_image, args.ref_video, args.ref_audio)
            ):
                gen_parser.error(
                    "At least a prompt, --first-frame, --ref-image, --ref-video, "
                    "or --ref-audio is required"
                )
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
                generate_audio=not args.no_audio,
                watermark=args.watermark,
                web_search=args.web_search,
                return_last_frame=args.return_last_frame,
                output_format=args.output_format,
                priority=args.priority,
                expires_after=args.expires_after,
                output_path=args.output,
            )
        elif args.command == "get":
            get_task(args.task_id)
        elif args.command == "list":
            list_tasks(
                status=args.status,
                model=args.model,
                task_ids=args.task_ids,
                page_num=args.page,
                page_size=args.page_size,
            )
        elif args.command == "delete":
            delete_task(args.task_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
