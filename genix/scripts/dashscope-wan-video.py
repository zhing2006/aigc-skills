"""
DashScope Wan 3.0 - All-in-One Reference Video Generation

Generate video with Alibaba Bailian (DashScope) Wan 3.0, a single all-in-one
model that covers text-to-video, first/last-frame video, multi-modal reference
video, and — uniquely — document-to-video and webpage-to-video. Output is up to
30 seconds at a fixed 30fps. The native API is asynchronous: create a task,
then poll until the video is ready.

Modes are auto-detected from the inputs you provide:

  Text-to-Video (t2v)        prompt only
  First Frame                --first-frame IMAGE
  Last Frame                 --last-frame IMAGE
  First + Last Frame         --first-frame IMAGE --last-frame IMAGE
  Reference                  --ref-image / --ref-video / --ref-audio (refer to
                             them in the prompt as 图1 / 视频1 / 音频1)
  Document-to-Video          --file URL   (pptx / pdf / docx / xlsx / md ...)
  Webpage-to-Video           --link URL

Frame inputs (--first-frame / --last-frame) and reference inputs
(--ref-* / --file / --link) are mutually exclusive; --file and --link cannot be
combined either. Only images may be passed as local files (they are base64
encoded); video, audio and document inputs must already be a URL.

Subcommands:
  generate  Create a video generation task and wait for the result (default)
  get       Query a single video generation task by ID

Models:
  wan3.0-video        standard (default)
  wan3.0-video-prime  high-speed; matches the standard model's capabilities with
                      significantly faster end-to-end generation

Supported resolutions: 480P, 720P, 1080P (default)
Supported ratios: adaptive (default), 16:9, 4:3, 1:1, 3:4, 9:16
Supported durations: 2-30 seconds (default 5), or -1 for auto duration
"""

import argparse
import asyncio
import base64
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import aiofiles
import aiohttp
from dotenv import load_dotenv


MODEL_STANDARD = "wan3.0-video"
MODEL_PRIME = "wan3.0-video-prime"
SUPPORTED_MODELS = [MODEL_STANDARD, MODEL_PRIME]
DEFAULT_MODEL = MODEL_STANDARD

SUPPORTED_RESOLUTIONS = ["480P", "720P", "1080P"]
SUPPORTED_RATIOS = ["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16"]

DEFAULT_RESOLUTION = "1080P"
DEFAULT_RATIO = "adaptive"
DEFAULT_DURATION = 5

# Duration is 2-30s, or -1 to let the model pick a length. With reference video
# input the API also enforces "input video total + output <= 30s"; only a lower
# bound of that is checkable locally (see generate_video) since the script never
# decodes media.
DURATION_RANGE = (2, 30)
AUTO_DURATION = -1
MAX_TOTAL_SECONDS = 30
OUTPUT_FPS = 30  # fixed by the model; not a parameter

MAX_SEED = 2147483647

# Native (non-OpenAI-compatible) async API host. Beijing business-space domains
# look like https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com — set
# DASHSCOPE_WORKSPACE_ID and that URL is built for you. Other regions can be
# reached by setting DASHSCOPE_VIDEO_BASE_URL, optionally with a {WorkspaceId}
# placeholder, e.g.:
#   https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com   (Singapore)
#   https://{WorkspaceId}.ap-northeast-1.maas.aliyuncs.com   (Japan, Tokyo)
#   https://{WorkspaceId}.eu-central-1.maas.aliyuncs.com     (Germany, Frankfurt)
#   https://{WorkspaceId}.us-east-1.maas.aliyuncs.com        (US, Virginia)
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"
WORKSPACE_BASE_TEMPLATE = "https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com"
WORKSPACE_PLACEHOLDER = "{WorkspaceId}"
COMPATIBLE_MODE_SUFFIX = "/compatible-mode/v1"

POLL_INTERVAL = 15  # seconds; the docs recommend ~15s between polls

# Task statuses. Note DashScope spells it CANCELED with one L, unlike the
# Volcengine and MiniMax scripts — a mismatch here would poll forever.
PENDING_STATUSES = ("PENDING", "RUNNING")
TERMINAL_FAILURE_STATUSES = ("CANCELED", "UNKNOWN")

# Per-request reference-asset counts. `*_SECONDS` is the combined duration cap the
# API enforces — reported in help text and error messages, not checked locally.
MAX_REF_IMAGES = 10
MAX_REF_VIDEOS = 5
MAX_REF_AUDIOS = 5
MAX_REF_VIDEO_SECONDS = 15
MAX_REF_AUDIO_SECONDS = 15

# Prompt over this length is truncated server-side rather than rejected.
MAX_PROMPT_CHARS = 20000

# Only images may be inlined as base64. Video / audio / document inputs must be a
# public http(s) URL or an OSS temporary URL.
URL_PREFIXES = ("http://", "https://", "oss://")
IMAGE_PASSTHROUGH_PREFIXES = URL_PREFIXES + ("data:",)

# Explicit allowlist rather than mimetypes.guess_type, which would silently label
# an unsupported file as image/png and defer the failure to the API.
IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",  # must have no alpha channel (not checkable without PIL)
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}
MAX_IMAGE_BYTES = 20 * 1024 * 1024

SUPPORTED_FILE_EXTENSIONS = [
    ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".pdf", ".txt", ".key", ".pages", ".numbers", ".md",
]

# Format / size envelope quoted back in the "must be a URL" errors.
REMOTE_ONLY_HINTS = {
    "video": f"mp4/mov, 1-{MAX_REF_VIDEO_SECONDS}s each and <={MAX_REF_VIDEO_SECONDS}s "
             "combined, <=100MB, sides 240-4096px, aspect <=8:1",
    "audio": f"wav/mp3, 1-{MAX_REF_AUDIO_SECONDS}s each and <={MAX_REF_AUDIO_SECONDS}s "
             "combined, <=15MB",
    "document": "docx/doc/xlsx/xls/pptx/ppt/pdf/txt/key/pages/numbers/md, <=100MB, <=50 pages",
}


def get_api_key() -> str:
    """Get DashScope API key from environment."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    return api_key


def get_base_url() -> str:
    """Resolve the native async API host (no trailing slash).

    Resolution order:
      1. DASHSCOPE_VIDEO_BASE_URL, when it names a host other than the public
         default (a {WorkspaceId} placeholder in it is substituted from
         DASHSCOPE_WORKSPACE_ID)
      2. the Beijing business-space domain, if DASHSCOPE_WORKSPACE_ID is set
      3. https://dashscope.aliyuncs.com

    `.env.template` ships DASHSCOPE_VIDEO_BASE_URL pre-filled with the public
    default, so that value must not shadow DASHSCOPE_WORKSPACE_ID — only a host
    the user actually changed takes precedence.
    """
    workspace_id = os.environ.get("DASHSCOPE_WORKSPACE_ID", "").strip()
    base = os.environ.get("DASHSCOPE_VIDEO_BASE_URL", "").strip().rstrip("/")

    # Guard against a base that already carries an API path. /compatible-mode/v1 is a
    # different API surface with no async video-synthesis endpoint, and /api/v1 is the
    # half-path the docs display. Both are stripped first so a base that reduces to the
    # public default still falls through to the workspace host.
    for suffix in (COMPATIBLE_MODE_SUFFIX, "/api/v1"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break

    if base in ("", DEFAULT_BASE_URL):
        base = WORKSPACE_BASE_TEMPLATE if workspace_id else DEFAULT_BASE_URL

    if WORKSPACE_PLACEHOLDER in base:
        if not workspace_id:
            raise ValueError(
                f"DASHSCOPE_VIDEO_BASE_URL contains a {WORKSPACE_PLACEHOLDER} placeholder "
                "but DASHSCOPE_WORKSPACE_ID is not set"
            )
        base = base.replace(WORKSPACE_PLACEHOLDER, workspace_id)

    return base


def create_task_url(base: str) -> str:
    return f"{base}/api/v1/services/aigc/video-generation/video-synthesis"


def query_task_url(base: str, task_id: str) -> str:
    return f"{base}/api/v1/tasks/{task_id}"


def normalize_resolution(value: str) -> str:
    """Accept 480p/720p/1080p in any case; canonicalize to uppercase 'P'."""
    return value.upper()


def format_api_error(action: str, status: int, data: dict, text: str) -> str:
    """Build an error message from DashScope's {code, message, request_id} body."""
    code = data.get("code") or status
    message = data.get("message") or (text.strip() or f"HTTP {status}")
    request_id = data.get("request_id")
    suffix = f" [request_id: {request_id}]" if request_id else ""
    return f"Failed to {action} ({code}): {message}{suffix}"


async def request_json(session, method: str, url: str, action: str, **kwargs) -> dict:
    """Send a request and return the parsed JSON body, raising on API errors.

    Reads the body as text first so a non-JSON response (a gateway's HTML 502 page)
    becomes a readable error instead of an aiohttp ContentTypeError.
    """
    async with session.request(method, url, **kwargs) as resp:
        text = await resp.text()
        try:
            data = json.loads(text) if text.strip() else {}
        except json.JSONDecodeError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        if resp.status != 200:
            raise Exception(format_api_error(action, resp.status, data, text))
        return data


def encode_image_base64(image_path: str) -> str:
    """Validate and encode a local image file as a base64 data URI."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type = IMAGE_MIME_TYPES.get(path.suffix.lower())
    if not mime_type:
        supported = ", ".join(sorted(IMAGE_MIME_TYPES))
        raise ValueError(
            f"Unsupported image format '{path.suffix or '(none)'}': {image_path}. "
            f"Supported: {supported} (PNG must have no alpha channel)"
        )

    size = path.stat().st_size
    if size > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is {size / 1024 / 1024:.1f}MB, over the "
            f"{MAX_IMAGE_BYTES // 1024 // 1024}MB limit: {image_path}. "
            "Pass a public http(s) URL or an oss:// temporary URL instead."
        )

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def resolve_image_url(path_or_url: str) -> str:
    """Resolve an image path or URL. Local files are base64-encoded."""
    if path_or_url.startswith(IMAGE_PASSTHROUGH_PREFIXES):
        if path_or_url.startswith("data:") and not path_or_url.startswith("data:image/"):
            raise ValueError(f"Only image data URIs are accepted here: {path_or_url[:40]}...")
        return path_or_url
    return encode_image_base64(path_or_url)


def require_remote_url(value: str, option: str, kind: str) -> str:
    """Reject anything but a public http(s) URL or an OSS temporary URL.

    Wan 3.0 accepts base64 only for images. Video, audio and document inputs must
    already live at a URL, so a local path has to be uploaded first.
    """
    if value.startswith(URL_PREFIXES):
        return value
    if value.startswith("data:"):
        raise ValueError(
            f"{option} does not accept base64 data URIs — Wan 3.0 only inlines images. "
            f"Upload the {kind} and pass its public http(s) URL or OSS temporary URL "
            f"({REMOTE_ONLY_HINTS[kind]})."
        )
    raise ValueError(
        f"{option} must be a public http(s) URL or an OSS temporary URL "
        f"(oss://dashscope-instant/...), not a local path: {value}. "
        f"Upload the {kind} to public storage first ({REMOTE_ONLY_HINTS[kind]})."
    )


def require_public_link(url: str) -> str:
    """A webpage reference has to be an http(s) URL — oss:// makes no sense here."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(
            f"--link must be a public http(s) webpage URL needing no login: {url}"
        )
    return url


def check_file_extension(url: str) -> None:
    """Reject a document URL whose extension is discernible and unsupported."""
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix and suffix not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError(
            f"Unsupported document type '{suffix}'. Supported: "
            f"{', '.join(SUPPORTED_FILE_EXTENSIONS)}"
        )


def detect_mode(
    first_frame: str | None,
    last_frame: str | None,
    ref_images: list[str] | None,
    ref_videos: list[str] | None,
    ref_audios: list[str] | None,
    file: str | None,
    link: str | None,
) -> str:
    """Determine the generation mode from the provided inputs.

    Document and webpage inputs win over plain reference assets because they are the
    content source, while reference images alongside them only steer the look. All
    three legally coexist in one request — the mode is a reporting label, and the
    hard exclusivity rule (frame group vs reference group) is checked separately.
    """
    if link:
        return "link"
    if file:
        return "file"
    if ref_images or ref_videos or ref_audios:
        return "reference"
    if first_frame and last_frame:
        return "first-last-frame"
    if last_frame:
        return "last-frame"
    if first_frame:
        return "first-frame"
    return "t2v"


MODE_LABELS = {
    "t2v": "Text-to-Video",
    "first-frame": "First Frame",
    "last-frame": "Last Frame",
    "first-last-frame": "First + Last Frame",
    "reference": "Reference (all-in-one)",
    "file": "Document-to-Video",
    "link": "Webpage-to-Video",
}


def describe_inputs(ref_images, ref_videos, ref_audios, file, link) -> str:
    """Summarize the reference assets for the log line, e.g. '2 images, 1 audio'."""
    parts = []
    for count, noun in (
        (len(ref_images or []), "image"),
        (len(ref_videos or []), "video"),
        (len(ref_audios or []), "audio"),
    ):
        if count:
            parts.append(f"{count} {noun}" + ("s" if count > 1 and noun != "audio" else ""))
    if file:
        parts.append("1 document")
    if link:
        parts.append("1 webpage")
    return ", ".join(parts)


# ──────────────────────────── generate ────────────────────────────


async def generate_video(
    prompt: str | None = None,
    first_frame: str | None = None,
    last_frame: str | None = None,
    ref_images: list[str] | None = None,
    ref_videos: list[str] | None = None,
    ref_audios: list[str] | None = None,
    file: str | None = None,
    link: str | None = None,
    model: str = DEFAULT_MODEL,
    resolution: str = DEFAULT_RESOLUTION,
    ratio: str = DEFAULT_RATIO,
    duration: int = DEFAULT_DURATION,
    audio: bool = True,
    prompt_extend: bool = True,
    watermark: bool = False,
    seed: int | None = None,
    output_path: str | None = None,
) -> Path:
    """Generate a video using DashScope Wan 3.0 (all-in-one reference model)."""
    mode = detect_mode(first_frame, last_frame, ref_images, ref_videos, ref_audios, file, link)

    # ── Scalar parameter validation (cheap checks before any file is read) ──
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    if resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}. Supported: {SUPPORTED_RESOLUTIONS}")

    if ratio not in SUPPORTED_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio}. Supported: {SUPPORTED_RATIOS}")

    if duration != AUTO_DURATION and not (DURATION_RANGE[0] <= duration <= DURATION_RANGE[1]):
        raise ValueError(
            f"Duration must be an integer between {DURATION_RANGE[0]} and {DURATION_RANGE[1]} "
            f"seconds, or {AUTO_DURATION} for auto duration"
        )

    if seed is not None and (seed < 0 or seed > MAX_SEED):
        raise ValueError(f"Seed must be between 0 and {MAX_SEED}")

    # ── Cross-input validation ──
    has_frames = bool(first_frame or last_frame)
    has_references = bool(ref_images or ref_videos or ref_audios or file or link)
    if has_frames and has_references:
        raise ValueError(
            "--first-frame/--last-frame cannot be combined with --ref-image/--ref-video/"
            "--ref-audio/--file/--link; the API treats them as mutually exclusive input groups"
        )
    if file and link:
        raise ValueError("--file and --link are mutually exclusive (at most one, and not both)")

    if not prompt and not (has_frames or has_references):
        raise ValueError("Either a prompt or at least one media input is required")

    if ref_images and len(ref_images) > MAX_REF_IMAGES:
        raise ValueError(
            f"At most {MAX_REF_IMAGES} --ref-image inputs are allowed (got {len(ref_images)})"
        )
    if ref_videos and len(ref_videos) > MAX_REF_VIDEOS:
        raise ValueError(
            f"At most {MAX_REF_VIDEOS} --ref-video inputs are allowed (got {len(ref_videos)}); "
            f"each 1-{MAX_REF_VIDEO_SECONDS}s and {MAX_REF_VIDEO_SECONDS}s combined"
        )
    if ref_audios and len(ref_audios) > MAX_REF_AUDIOS:
        raise ValueError(
            f"At most {MAX_REF_AUDIOS} --ref-audio inputs are allowed (got {len(ref_audios)}); "
            f"each 1-{MAX_REF_AUDIO_SECONDS}s and {MAX_REF_AUDIO_SECONDS}s combined"
        )

    # With reference video input the API caps input video total + output at 30s. The real
    # input durations are unknown here, but each clip is at least 1s by API rule, so N
    # clips consume at least N seconds of the budget — a bound that never false-positives.
    n_videos = len(ref_videos or [])
    if n_videos and duration != AUTO_DURATION:
        max_output = MAX_TOTAL_SECONDS - n_videos
        if duration > max_output:
            raise ValueError(
                f"With {n_videos} reference video(s) the API caps input video total + output "
                f"duration at {MAX_TOTAL_SECONDS}s, so --duration cannot exceed {max_output}s "
                f"here (each clip is at least 1s). Pass {AUTO_DURATION} for auto duration, or "
                "lower --duration; the exact ceiling depends on the real input durations, "
                "which this script does not decode."
            )

    if prompt and len(prompt) > MAX_PROMPT_CHARS:
        print(
            f"Note: prompt is {len(prompt)} characters; the API truncates beyond "
            f"{MAX_PROMPT_CHARS}."
        )

    api_key = get_api_key()
    base = get_base_url()

    # ── Build input.media ──
    # Grouped by type so 图N / 视频N / 音频N map to the Nth --ref-image / --ref-video /
    # --ref-audio regardless of how the flags were interleaved on the command line.
    input_obj: dict = {}
    if prompt:
        input_obj["prompt"] = prompt

    media = []
    if first_frame:
        media.append({"type": "first_frame", "url": resolve_image_url(first_frame)})
    if last_frame:
        media.append({"type": "last_frame", "url": resolve_image_url(last_frame)})
    for img in (ref_images or []):
        media.append({"type": "reference_image", "url": resolve_image_url(img)})
    for vid in (ref_videos or []):
        media.append(
            {"type": "reference_video", "url": require_remote_url(vid, "--ref-video", "video")}
        )
    for aud in (ref_audios or []):
        media.append(
            {"type": "reference_audio", "url": require_remote_url(aud, "--ref-audio", "audio")}
        )
    if file:
        file_url = require_remote_url(file, "--file", "document")
        check_file_extension(file_url)
        media.append({"type": "file", "url": file_url})
    if link:
        media.append({"type": "link", "url": require_public_link(link)})
    if media:
        input_obj["media"] = media

    # ── Build parameters ──
    # Every knob has a CLI-resolved value, so all are sent explicitly: the request then
    # matches the log line exactly and does not drift with server-side default changes.
    parameters: dict = {
        "resolution": resolution,
        "ratio": ratio,
        "duration": duration,  # -1 is a legal value (auto duration)
        "audio": audio,
        "prompt_extend": prompt_extend,
        "watermark": watermark,
    }
    if seed is not None:
        parameters["seed"] = seed

    payload = {"model": model, "input": input_obj, "parameters": parameters}

    output_file = Path(output_path) if output_path else Path("generated_video.mp4")

    duration_label = "auto duration" if duration == AUTO_DURATION else f"{duration}s"
    inputs_label = describe_inputs(ref_images, ref_videos, ref_audios, file, link)
    print(f"Prompt: {prompt or '(none)'}")
    print(
        f"Generating video ({MODE_LABELS[mode]}"
        + (f": {inputs_label}" if inputs_label else "")
        + f", {resolution}, {ratio}, {duration_label}, audio={audio}, model: {model})..."
    )

    async with aiohttp.ClientSession() as session:
        # ── Step 1: create the async task ──
        data = await request_json(
            session, "POST", create_task_url(base), "create task",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            json=payload,
        )

        task_id = (data.get("output") or {}).get("task_id")
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

            output = data.get("output") or {}
            status = output.get("task_status")

            if status == "SUCCEEDED":
                print("Task succeeded!")
                video_url = output.get("video_url")
                break
            elif status == "FAILED":
                code = output.get("code", "Unknown")
                message = output.get("message", "Unknown error")
                raise Exception(f"Video generation failed ({code}): {message}")
            elif status in TERMINAL_FAILURE_STATUSES:
                raise Exception(f"Task ended with status: {status}")
            elif status not in PENDING_STATUSES:
                # Never poll forever on a status the API did not document.
                raise Exception(f"Unexpected task status: {status}")
            else:
                poll_count += 1
                print(f"Status: {status}, waiting... ({poll_count * POLL_INTERVAL}s elapsed)")
                await asyncio.sleep(POLL_INTERVAL)

        if not video_url:
            raise Exception("No video URL found in task result")

        # ── Step 3: download the result (link valid for 24h) ──
        # Streamed: 30s of 1080p30 is well past the point of buffering a whole file.
        print("Downloading video...")
        async with session.get(video_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download video: HTTP {resp.status}")
            async with aiofiles.open(output_file, "wb") as f:
                async for chunk in resp.content.iter_chunked(1 << 20):
                    await f.write(chunk)

    print(f"Video saved to: {output_file}")

    return output_file


# ──────────────────────────── get ────────────────────────────


def print_task(data: dict, fallback_task_id: str = "-") -> None:
    """Print task details."""
    output = data.get("output") or {}
    usage = data.get("usage") or {}

    print(f"  ID:         {output.get('task_id', fallback_task_id)}")
    print(f"  Status:     {output.get('task_status', '-')}")
    if output.get("submit_time"):
        print(f"  Submitted:  {output['submit_time']}")
    if output.get("scheduled_time"):
        print(f"  Scheduled:  {output['scheduled_time']}")
    if output.get("end_time"):
        print(f"  Ended:      {output['end_time']}")
    if usage.get("SR"):
        print(f"  Resolution: {usage['SR']}")
    if usage.get("ratio"):
        print(f"  Ratio:      {usage['ratio']}")
    if usage.get("fps") is not None:
        print(f"  FPS:        {usage['fps']}")
    if usage.get("duration") is not None:
        print(f"  Duration:   {usage['duration']}s")
    # Only worth a line when a video was actually fed in (0.0 means there was none).
    if usage.get("input_video_duration"):
        print(
            f"  Video I/O:  {usage['input_video_duration']}s in -> "
            f"{usage.get('output_video_duration', '-')}s out"
        )
    if output.get("orig_prompt"):
        print(f"  Prompt:     {output['orig_prompt']}")
    if output.get("video_url"):
        print(f"  Video URL:  {output['video_url']}")
    if output.get("code"):
        print(f"  Error:      {output.get('code')}: {output.get('message', '')}")
    if data.get("request_id"):
        print(f"  Request ID: {data['request_id']}")


async def get_task(task_id: str) -> None:
    """Query a single video generation task and print its details."""
    api_key = get_api_key()
    base = get_base_url()

    async with aiohttp.ClientSession() as session:
        data = await request_json(
            session, "GET", query_task_url(base, task_id), "query task",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    print_task(data, fallback_task_id=task_id)


# ──────────────────────────── CLI ────────────────────────────


SUBCOMMANDS = {"generate", "get"}
HELP_FLAGS = {"-h", "--help"}


async def main():
    # Default to "generate" if the first arg is not a known subcommand. Options must be
    # allowed through, because Wan 3.0 accepts a prompt-less request — `--link https://…`
    # or `-i first.png` alone is valid, so a startswith("-") guard would break them.
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS and sys.argv[1] not in HELP_FLAGS:
        sys.argv.insert(1, "generate")

    parser = argparse.ArgumentParser(
        description="DashScope Wan 3.0 All-in-One Reference Video Generation "
                    "(text / frame / reference / document / webpage)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── generate ──
    gen_parser = subparsers.add_parser("generate", help="Generate a video (default)")
    gen_parser.add_argument(
        "prompt", type=str, nargs="?", default=None,
        help=f"Text prompt (optional when media is supplied; <={MAX_PROMPT_CHARS} characters, "
             "the API truncates beyond that). In reference mode, address the assets in "
             "Chinese as 图1/图2, 视频1, 音频1 — images, videos and audios are numbered "
             "separately, each in the order its flag was repeated",
    )
    gen_parser.add_argument(
        "-i", "--first-frame", type=str, default=None,
        help="First frame image path/URL (used strictly as frame 1). Cannot be combined "
             "with any --ref-* / --file / --link input",
    )
    gen_parser.add_argument(
        "--last-frame", type=str, default=None,
        help="Last frame image path/URL (used strictly as the final frame). Usable alone "
             "or together with --first-frame",
    )
    gen_parser.add_argument(
        "--ref-image", type=str, action="append", default=None,
        help=f"Reference image path/URL (repeatable, up to {MAX_REF_IMAGES}) -> 图1, 图2, ...",
    )
    gen_parser.add_argument(
        "--ref-video", type=str, action="append", default=None,
        help=f"Reference video URL (repeatable, up to {MAX_REF_VIDEOS}; each 1-"
             f"{MAX_REF_VIDEO_SECONDS}s and {MAX_REF_VIDEO_SECONDS}s combined) -> 视频1, ... "
             "URL-only: no base64 and no local paths",
    )
    gen_parser.add_argument(
        "--ref-audio", type=str, action="append", default=None,
        help=f"Reference audio URL (repeatable, up to {MAX_REF_AUDIOS}; each 1-"
             f"{MAX_REF_AUDIO_SECONDS}s and {MAX_REF_AUDIO_SECONDS}s combined) -> 音频1, ... "
             "URL-only: no base64 and no local paths",
    )
    gen_parser.add_argument(
        "--file", type=str, default=None,
        help="Document URL -> Document-to-Video (pptx/pdf/docx/xlsx/md/..., <=50 pages, "
             "<=100MB). URL-only. Mutually exclusive with --link",
    )
    gen_parser.add_argument(
        "--link", type=str, default=None,
        help="Public webpage URL -> Webpage-to-Video (no login required). "
             "Mutually exclusive with --file",
    )
    gen_parser.add_argument(
        "-m", "--model", type=str, default=DEFAULT_MODEL, choices=SUPPORTED_MODELS,
        help=f"Model ID (default: {DEFAULT_MODEL}). {MODEL_PRIME} matches the standard "
             "model's capabilities with markedly faster end-to-end generation",
    )
    gen_parser.add_argument(
        "--prime", action="store_true",
        help=f"Shorthand for -m {MODEL_PRIME}",
    )
    gen_parser.add_argument(
        "-r", "--resolution", type=normalize_resolution, default=DEFAULT_RESOLUTION,
        choices=SUPPORTED_RESOLUTIONS,
        help=f"Video resolution (default: {DEFAULT_RESOLUTION}; lowercase accepted)",
    )
    gen_parser.add_argument(
        "-a", "--ratio", type=str, default=DEFAULT_RATIO, choices=SUPPORTED_RATIOS,
        help=f"Aspect ratio (default: {DEFAULT_RATIO}, recommended from the input media and "
             "intent). Keep 'adaptive' when supplying frames so the output does not fight "
             "the frame's own ratio",
    )
    gen_parser.add_argument(
        "-d", "--duration", type=int, default=DEFAULT_DURATION,
        help=f"Duration in seconds, {DURATION_RANGE[0]}-{DURATION_RANGE[1]} (default: "
             f"{DEFAULT_DURATION}), or {AUTO_DURATION} to let the model choose. With "
             f"reference video input, input video total + output must stay "
             f"<={MAX_TOTAL_SECONDS}s",
    )
    gen_parser.add_argument(
        "--no-audio", action="store_true",
        help="Generate a silent video (audio is included by default, same price)",
    )
    gen_parser.add_argument(
        "--no-prompt-extend", action="store_true",
        help="Disable LLM prompt rewriting (on by default; it helps short prompts a lot but "
             "adds latency). Pair with --seed when you need repeatability",
    )
    gen_parser.add_argument(
        "--watermark", action="store_true",
        help="Add the AI-generated identification watermark (off by default)",
    )
    gen_parser.add_argument(
        "--seed", type=int, default=None,
        help=f"Random seed 0-{MAX_SEED} for reproducibility",
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
            if not any([
                args.prompt, args.first_frame, args.last_frame, args.ref_image,
                args.ref_video, args.ref_audio, args.file, args.link,
            ]):
                gen_parser.error(
                    "At least a prompt or one media input (--first-frame / --last-frame / "
                    "--ref-image / --ref-video / --ref-audio / --file / --link) is required"
                )
            await generate_video(
                prompt=args.prompt,
                first_frame=args.first_frame,
                last_frame=args.last_frame,
                ref_images=args.ref_image,
                ref_videos=args.ref_video,
                ref_audios=args.ref_audio,
                file=args.file,
                link=args.link,
                model=MODEL_PRIME if args.prime else args.model,
                resolution=args.resolution,
                ratio=args.ratio,
                duration=args.duration,
                audio=not args.no_audio,
                prompt_extend=not args.no_prompt_extend,
                watermark=args.watermark,
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
