"""
Volcengine Voice Design - Create Voices from Text or Image Prompts

Supported actions: create (default), status
Prompt types: text description (e.g. "女性，语速中等偏快，语调低沉有力")
              or an image (local file or URL, image takes priority)
Supported languages: cn, en
"""

import argparse
import asyncio
import base64
import os
import sys
import uuid
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://openspeech.bytedance.com"
LANGUAGE_MAP = {"cn": 0, "en": 1}
STATUS_NAMES = {0: "NotFound", 1: "Training", 2: "Success", 3: "Failed", 4: "Active"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_PROMPT_LENGTH = 200
MAX_PREVIEW_TEXT_LENGTH = 300

SUBCOMMANDS = {"create", "status"}


def get_api_key() -> str:
    """Get Volcengine speech API key from environment."""
    api_key = os.environ.get("VOLCENGINE_TTS_API_KEY")
    if not api_key:
        raise ValueError("VOLCENGINE_TTS_API_KEY environment variable is not set")
    return api_key


def get_base_url() -> str:
    """Get the OpenSpeech base URL from environment."""
    return os.environ.get("VOLCENGINE_TTS_BASE", DEFAULT_BASE_URL).rstrip("/")


async def openspeech_post(path: str, body: dict, timeout: int = 300) -> dict:
    """POST to the OpenSpeech voice design API."""
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": get_api_key(),
        "X-Api-Request-Id": str(uuid.uuid4()),
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{get_base_url()}/api/v3/tts/{path}",
            headers=headers,
            json=body,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as response:
            logid = response.headers.get("X-Tt-Logid", "")
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text} [logid={logid}]")
            return await response.json()


async def download_demo_audio(url: str, output_path: Path) -> None:
    """Download the demo audio (URL is valid for one hour)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            if response.status != 200:
                raise RuntimeError(f"Demo audio download failed ({response.status})")
            audio_bytes = await response.read()
    async with aiofiles.open(output_path, "wb") as f:
        await f.write(audio_bytes)
    print(f"Demo audio saved to: {output_path}")


def print_voice_status(data: dict) -> None:
    """Print the voice status fields."""
    status = data.get("status")
    print(f"Speaker ID: {data.get('speaker_id', '')}")
    print(f"Status: {status} ({STATUS_NAMES.get(status, 'Unknown')})")
    if data.get("available_training_times") is not None:
        print(f"Remaining design/training times: {data['available_training_times']}")
    if status in (2, 4):
        print("The voice is ready for TTS synthesis (use volcengine-text-speech.py).")


async def design_voice(
    speaker_id: str,
    preview_text: str,
    text_prompt: str | None = None,
    image_file: str | None = None,
    image_url: str | None = None,
    language: str = "cn",
) -> dict:
    """
    Design a voice from a text description or an image prompt.

    Args:
        speaker_id: Purchased speaker ID (S_xxx)
        preview_text: Demo text to synthesize with the designed voice (max 300 chars)
        text_prompt: Voice description (max 200 chars)
        image_file: Local image file used as the prompt (max 10MB)
        image_url: Downloadable image URL used as the prompt
        language: Voice language (cn/en)

    Returns:
        API response dictionary
    """
    if not text_prompt and not image_file and not image_url:
        raise ValueError("At least one of text_prompt, --image, or --image-url is required")

    if text_prompt and len(text_prompt) > MAX_TEXT_PROMPT_LENGTH:
        raise ValueError(f"text_prompt must be at most {MAX_TEXT_PROMPT_LENGTH} characters")

    if len(preview_text) > MAX_PREVIEW_TEXT_LENGTH:
        raise ValueError(f"preview_text must be at most {MAX_PREVIEW_TEXT_LENGTH} characters")

    if language not in LANGUAGE_MAP:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(LANGUAGE_MAP.keys())}")

    prompt: dict = {}
    if text_prompt:
        prompt["text_prompt"] = text_prompt

    image_prompt: dict = {}
    if image_file:
        file_path = Path(image_file)
        if not file_path.exists():
            raise ValueError(f"Image file not found: {image_file}")
        file_size = file_path.stat().st_size
        if file_size > MAX_IMAGE_SIZE:
            raise ValueError(f"Image file too large: {file_size / 1024 / 1024:.1f}MB. Maximum: 10MB")
        print(f"Reading image file: {file_path}")
        async with aiofiles.open(file_path, "rb") as f:
            image_bytes = await f.read()
        image_prompt["image_bytes"] = base64.b64encode(image_bytes).decode()
    if image_url:
        image_prompt["image_url"] = image_url
    if image_prompt:
        prompt["image_prompt"] = image_prompt
        if text_prompt:
            print("Note: the image prompt takes priority over the text prompt.")

    body = {
        "speaker_id": speaker_id,
        "text": preview_text,
        "prompt": prompt,
        "language": LANGUAGE_MAP[language],
    }

    if text_prompt:
        print(f"Text prompt: {text_prompt}")
    print(f"Preview text: {preview_text}")
    print(f"Speaker ID: {speaker_id}, Language: {language}")
    print("Designing voice...")

    return await openspeech_post("voice_design", body)


async def get_voice_status(speaker_id: str) -> dict:
    """Query the status of a voice."""
    print(f"Querying voice: {speaker_id}...")
    return await openspeech_post("get_voice", {"speaker_id": speaker_id}, timeout=60)


async def main():
    # Default to "create" if first arg is not a known subcommand
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "create")

    parser = argparse.ArgumentParser(
        description="Design custom voices using Volcengine Voice Design"
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    # Create subcommand
    create_parser = subparsers.add_parser("create", help="Design a voice from a text or image prompt")
    create_parser.add_argument(
        "text_prompt",
        type=str,
        nargs="?",
        default=None,
        help="Voice description, e.g. \"女性，语速中等偏快，语调低沉有力\" (max 200 chars)",
    )
    create_parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Local image file used as the prompt (max 10MB, takes priority over text)",
    )
    create_parser.add_argument(
        "--image-url",
        type=str,
        default=None,
        help="Downloadable image URL used as the prompt",
    )
    create_parser.add_argument(
        "-s", "--speaker-id",
        type=str,
        required=True,
        help="Purchased speaker ID (S_xxx)",
    )
    create_parser.add_argument(
        "-t", "--preview-text",
        type=str,
        required=True,
        help="Demo text to preview the designed voice (max 300 chars)",
    )
    create_parser.add_argument(
        "-l", "--language",
        type=str,
        default="cn",
        choices=list(LANGUAGE_MAP.keys()),
        help="Voice language (default: cn)",
    )
    create_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Demo audio output path (default: <speaker_id>_demo.mp3)",
    )

    # Status subcommand
    status_parser = subparsers.add_parser("status", help="Query the status of a voice")
    status_parser.add_argument("speaker_id", type=str, help="Speaker ID to query")
    status_parser.add_argument(
        "--download-demo",
        action="store_true",
        help="Download the demo audio if available",
    )
    status_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Demo audio output path (default: <speaker_id>_demo.mp3)",
    )

    args = parser.parse_args()

    try:
        if args.action == "create":
            data = await design_voice(
                speaker_id=args.speaker_id,
                preview_text=args.preview_text,
                text_prompt=args.text_prompt,
                image_file=args.image,
                image_url=args.image_url,
                language=args.language,
            )
            print()
            print_voice_status(data)
            demo_url = data.get("demo_audio")
            if demo_url:
                output_path = Path(args.output) if args.output else Path(f"{args.speaker_id}_demo.mp3")
                await download_demo_audio(demo_url, output_path)
            else:
                print("No demo audio returned; query later with the status action.")
        elif args.action == "status":
            data = await get_voice_status(args.speaker_id)
            print()
            print_voice_status(data)
            demo_url = data.get("demo_audio")
            if demo_url:
                if args.download_demo:
                    output_path = Path(args.output) if args.output else Path(f"{args.speaker_id}_demo.mp3")
                    await download_demo_audio(demo_url, output_path)
                else:
                    print(f"Demo audio URL (valid for 1 hour): {demo_url}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
