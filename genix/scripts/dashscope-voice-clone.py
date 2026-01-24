"""
DashScope Voice Clone - Clone Voice from Audio

Supported actions: create, list, delete
Supported audio formats: WAV (16bit), MP3, M4A
Supported languages: zh, en, de, it, pt, es, ja, ko, fr, ru
"""

import argparse
import asyncio
import base64
import os
import sys
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


SUPPORTED_LANGUAGES = ["zh", "en", "de", "it", "pt", "es", "ja", "ko", "fr", "ru"]
SUPPORTED_AUDIO_FORMATS = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
}
SUPPORTED_TARGET_MODELS = [
    "qwen3-tts-vc-realtime-2026-01-15",
    "qwen3-tts-vc-realtime-2025-11-27",
]
DEFAULT_MODEL = "qwen-voice-enrollment"
DEFAULT_TARGET_MODEL = "qwen3-tts-vc-realtime-2026-01-15"
API_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def get_api_key() -> str:
    """Get DashScope API key from environment."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    return api_key


def get_mime_type(file_path: Path) -> str:
    """Get MIME type from file extension."""
    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {ext}. Supported: {list(SUPPORTED_AUDIO_FORMATS.keys())}")
    return SUPPORTED_AUDIO_FORMATS[ext]


async def create_voice(
    audio_file: str,
    preferred_name: str,
    target_model: str = DEFAULT_TARGET_MODEL,
    language: str | None = None,
    text: str | None = None,
) -> str:
    """
    Create a cloned voice from an audio file.

    Args:
        audio_file: Path to the audio file (WAV/MP3/M4A)
        preferred_name: Preferred name for the voice (max 16 chars, alphanumeric/underscore)
        target_model: Target TTS model for synthesis
        language: Audio language (optional)
        text: Transcript of the audio (optional, for validation)

    Returns:
        Voice name/ID
    """
    file_path = Path(audio_file)

    if not file_path.exists():
        raise ValueError(f"Audio file not found: {audio_file}")

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"Audio file too large: {file_size / 1024 / 1024:.1f}MB. Maximum: 10MB")

    mime_type = get_mime_type(file_path)

    if len(preferred_name) > 16:
        raise ValueError("preferred_name must be at most 16 characters")
    if not preferred_name.replace("_", "").isalnum():
        raise ValueError("preferred_name must contain only letters, numbers, and underscores")

    if target_model not in SUPPORTED_TARGET_MODELS:
        raise ValueError(f"Unsupported target model: {target_model}. Supported: {SUPPORTED_TARGET_MODELS}")

    if language is not None and language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}. Supported: {SUPPORTED_LANGUAGES}")

    api_key = get_api_key()

    # Read and encode audio file
    print(f"Reading audio file: {file_path}")
    async with aiofiles.open(file_path, "rb") as f:
        audio_bytes = await f.read()

    base64_audio = base64.b64encode(audio_bytes).decode()
    data_uri = f"data:{mime_type};base64,{base64_audio}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    input_data = {
        "action": "create",
        "target_model": target_model,
        "preferred_name": preferred_name,
        "audio": {"data": data_uri},
    }

    if language:
        input_data["language"] = language

    if text:
        input_data["text"] = text

    payload = {
        "model": DEFAULT_MODEL,
        "input": input_data,
    }

    print(f"Preferred name: {preferred_name}")
    print(f"Target model: {target_model}")
    if language:
        print(f"Language: {language}")
    print("Creating cloned voice...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text}")

            data = await response.json()

    output = data.get("output", {})
    voice_name = output.get("voice")

    if not voice_name:
        raise RuntimeError(f"API did not return a voice name. Response: {data}")

    print(f"Voice created: {voice_name}")

    return voice_name


async def list_voices(
    page_index: int = 0,
    page_size: int = 10,
) -> list[dict]:
    """
    List all cloned voices created by the user.

    Args:
        page_index: Page index (0-based)
        page_size: Number of items per page

    Returns:
        List of voice information dictionaries
    """
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEFAULT_MODEL,
        "input": {
            "action": "list",
            "page_index": page_index,
            "page_size": page_size,
        },
    }

    print(f"Fetching cloned voices (page {page_index + 1}, size {page_size})...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text}")

            data = await response.json()

    output = data.get("output", {})
    voices = output.get("voice_list", [])
    total_count = output.get("total_count", 0)

    print(f"Found {total_count} cloned voice(s) (showing {len(voices)} on this page)")
    print()

    for voice in voices:
        voice_name = voice.get("voice", "Unknown")
        target_model = voice.get("target_model", "")
        created = voice.get("gmt_create", "")
        print(f"  Voice: {voice_name}")
        print(f"  Target model: {target_model}")
        print(f"  Created: {created}")
        print()

    return voices


async def delete_voice(voice_name: str) -> bool:
    """
    Delete a specific voice.

    Args:
        voice_name: Name of the voice to delete

    Returns:
        True if deletion was successful
    """
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEFAULT_MODEL,
        "input": {
            "action": "delete",
            "voice": voice_name,
        },
    }

    print(f"Deleting voice: {voice_name}...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text}")

            data = await response.json()

    deleted_voice = data.get("output", {}).get("voice", voice_name)
    print(f"Voice deleted: {deleted_voice}")

    return True


async def main():
    parser = argparse.ArgumentParser(
        description="Clone voices from audio using DashScope Qwen Voice Clone API"
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    # Create subcommand
    create_parser = subparsers.add_parser("create", help="Create a cloned voice from audio")
    create_parser.add_argument(
        "audio_file",
        type=str,
        help="Path to the audio file (WAV/MP3/M4A, 10-60 seconds, <10MB)",
    )
    create_parser.add_argument(
        "-n", "--name",
        type=str,
        required=True,
        help="Preferred name for the voice (max 16 chars, alphanumeric/underscore only)",
    )
    create_parser.add_argument(
        "-l", "--language",
        type=str,
        default=None,
        choices=SUPPORTED_LANGUAGES,
        help="Audio language (optional)",
    )
    create_parser.add_argument(
        "-t", "--text",
        type=str,
        default=None,
        help="Transcript of the audio (optional, for validation)",
    )
    create_parser.add_argument(
        "--target-model",
        type=str,
        default=DEFAULT_TARGET_MODEL,
        choices=SUPPORTED_TARGET_MODELS,
        help=f"Target TTS model (default: {DEFAULT_TARGET_MODEL})",
    )

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List all cloned voices")
    list_parser.add_argument(
        "--page-index",
        type=int,
        default=0,
        help="Page index, 0-based (default: 0)",
    )
    list_parser.add_argument(
        "--page-size",
        type=int,
        default=10,
        help="Number of items per page (default: 10)",
    )

    # Delete subcommand
    delete_parser = subparsers.add_parser("delete", help="Delete a specific voice")
    delete_parser.add_argument(
        "voice_name",
        type=str,
        help="Name of the voice to delete",
    )

    args = parser.parse_args()

    try:
        if args.action == "create":
            voice_name = await create_voice(
                audio_file=args.audio_file,
                preferred_name=args.name,
                target_model=args.target_model,
                language=args.language,
                text=args.text,
            )
            print()
            print(f"Voice ID for TTS: {voice_name}")
            print(f"Target model: {args.target_model}")
        elif args.action == "list":
            await list_voices(
                page_index=args.page_index,
                page_size=args.page_size,
            )
        elif args.action == "delete":
            await delete_voice(args.voice_name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
