"""
DashScope Voice Design - Custom AI Voice Creation

Supported actions: create, list, query, delete
Supported languages: zh, en, de, it, pt, es, ja, ko, fr, ru
Supported output formats: MP3, WAV, PCM, Opus
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
SUPPORTED_SAMPLE_RATES = [8000, 16000, 24000, 48000]
SUPPORTED_FORMATS = ["mp3", "wav", "pcm", "opus"]
SUPPORTED_TARGET_MODELS = [
    "qwen3-tts-vd-realtime-2025-12-16",
]
DEFAULT_MODEL = "qwen-voice-design"
DEFAULT_TARGET_MODEL = "qwen3-tts-vd-realtime-2025-12-16"
DEFAULT_LANGUAGE = "zh"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_FORMAT = "wav"
API_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization"


def get_api_key() -> str:
    """Get DashScope API key from environment."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    return api_key


async def create_voice(
    voice_prompt: str,
    preview_text: str,
    preferred_name: str | None = None,
    target_model: str = DEFAULT_TARGET_MODEL,
    language: str = DEFAULT_LANGUAGE,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    response_format: str = DEFAULT_FORMAT,
    output_path: str | None = None,
) -> tuple[str, Path | None]:
    """
    Create a custom voice using DashScope Qwen Voice Design API.

    Args:
        voice_prompt: Description of the desired voice (max 2048 chars)
        preview_text: Text to preview the voice (max 1024 chars)
        preferred_name: Preferred name for the voice (optional)
        target_model: Target TTS model for synthesis
        language: Voice language (zh/en/de/it/pt/es/ja/ko/fr/ru)
        sample_rate: Audio sample rate
        response_format: Audio format (mp3/wav/pcm/opus)
        output_path: Path to save preview audio (optional)

    Returns:
        Tuple of (voice_name, preview_audio_path or None)
    """
    if len(voice_prompt) > 2048:
        raise ValueError("voice_prompt must be at most 2048 characters")

    if len(preview_text) > 1024:
        raise ValueError("preview_text must be at most 1024 characters")

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}. Supported: {SUPPORTED_LANGUAGES}")

    if sample_rate not in SUPPORTED_SAMPLE_RATES:
        raise ValueError(f"Unsupported sample rate: {sample_rate}. Supported: {SUPPORTED_SAMPLE_RATES}")

    if response_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {response_format}. Supported: {SUPPORTED_FORMATS}")

    if preferred_name is not None:
        if len(preferred_name) > 16:
            raise ValueError("preferred_name must be at most 16 characters")
        if not preferred_name.replace("_", "").isalnum():
            raise ValueError("preferred_name must contain only letters, numbers, and underscores")

    if target_model not in SUPPORTED_TARGET_MODELS:
        raise ValueError(f"Unsupported target model: {target_model}. Supported: {SUPPORTED_TARGET_MODELS}")

    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    input_data = {
        "action": "create",
        "target_model": target_model,
        "voice_prompt": voice_prompt,
        "preview_text": preview_text,
        "language": language,
    }

    if preferred_name:
        input_data["preferred_name"] = preferred_name

    payload = {
        "model": DEFAULT_MODEL,
        "input": input_data,
        "parameters": {
            "sample_rate": sample_rate,
            "response_format": response_format,
        },
    }

    prompt_preview = voice_prompt[:50] + "..." if len(voice_prompt) > 50 else voice_prompt
    print(f"Voice prompt: {prompt_preview}")
    print(f"Preview text: {preview_text}")
    print(f"Language: {language}, Sample rate: {sample_rate}, Format: {response_format}")
    print("Creating custom voice...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text}")

            data = await response.json()

    output = data.get("output", {})
    voice_name = output.get("voice")
    preview_audio_data = output.get("preview_audio", {}).get("data")

    if not voice_name:
        raise RuntimeError(f"API did not return a voice name. Response: {data}")

    print(f"Voice created: {voice_name}")

    preview_path = None
    if preview_audio_data:
        audio_bytes = base64.b64decode(preview_audio_data)

        if output_path:
            preview_path = Path(output_path)
        else:
            ext = f".{response_format}" if response_format != "pcm" else ".pcm"
            preview_path = Path(f"{voice_name}_preview{ext}")

        async with aiofiles.open(preview_path, "wb") as f:
            await f.write(audio_bytes)
        print(f"Preview audio saved to: {preview_path}")

    return voice_name, preview_path


async def list_voices(
    page_index: int = 0,
    page_size: int = 10,
) -> list[dict]:
    """
    List all custom voices created by the user.

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

    print(f"Fetching custom voices (page {page_index + 1}, size {page_size})...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text}")

            data = await response.json()

    output = data.get("output", {})
    voices = output.get("voice_list", [])
    total_count = output.get("total_count", 0)

    print(f"Found {total_count} custom voice(s) (showing {len(voices)} on this page)")
    print()

    for voice in voices:
        voice_name = voice.get("voice", "Unknown")
        voice_prompt = voice.get("voice_prompt", "No description")
        language = voice.get("language", "")
        created = voice.get("gmt_create", "")
        prompt_preview = voice_prompt[:60] + "..." if len(voice_prompt) > 60 else voice_prompt
        print(f"  Voice: {voice_name}")
        print(f"  Description: {prompt_preview}")
        print(f"  Language: {language}, Created: {created}")
        print()

    return voices


async def query_voice(voice_name: str) -> dict:
    """
    Query details of a specific voice.

    Args:
        voice_name: Name of the voice to query

    Returns:
        Voice information dictionary
    """
    api_key = get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEFAULT_MODEL,
        "input": {
            "action": "query",
            "voice": voice_name,
        },
    }

    print(f"Querying voice: {voice_name}...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_ENDPOINT, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text}")

            data = await response.json()

    output = data.get("output", {})

    voice = output.get("voice", voice_name)
    voice_prompt = output.get("voice_prompt", "No description")
    preview_text = output.get("preview_text", "")
    language = output.get("language", "")
    target_model = output.get("target_model", "")
    created = output.get("gmt_create", "")
    modified = output.get("gmt_modified", "")

    print()
    print(f"Voice: {voice}")
    print(f"Description: {voice_prompt}")
    print(f"Preview text: {preview_text}")
    print(f"Language: {language}")
    print(f"Target model: {target_model}")
    print(f"Created: {created}")
    print(f"Modified: {modified}")

    return output


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
        description="Create and manage custom voices using DashScope Qwen Voice Design API"
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    # Create subcommand
    create_parser = subparsers.add_parser("create", help="Create a new custom voice")
    create_parser.add_argument(
        "voice_prompt",
        type=str,
        help="Description of the desired voice (max 2048 chars)",
    )
    create_parser.add_argument(
        "-t", "--preview-text",
        type=str,
        required=True,
        help="Text to preview the voice (max 1024 chars)",
    )
    create_parser.add_argument(
        "-n", "--name",
        type=str,
        default=None,
        help="Preferred name for the voice (max 16 chars, alphanumeric and underscore only)",
    )
    create_parser.add_argument(
        "-l", "--language",
        type=str,
        default=DEFAULT_LANGUAGE,
        choices=SUPPORTED_LANGUAGES,
        help=f"Voice language (default: {DEFAULT_LANGUAGE})",
    )
    create_parser.add_argument(
        "-r", "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        choices=SUPPORTED_SAMPLE_RATES,
        help=f"Audio sample rate in Hz (default: {DEFAULT_SAMPLE_RATE})",
    )
    create_parser.add_argument(
        "-f", "--format",
        type=str,
        default=DEFAULT_FORMAT,
        choices=SUPPORTED_FORMATS,
        help=f"Audio format (default: {DEFAULT_FORMAT})",
    )
    create_parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path for preview audio",
    )
    create_parser.add_argument(
        "--target-model",
        type=str,
        default=DEFAULT_TARGET_MODEL,
        choices=SUPPORTED_TARGET_MODELS,
        help=f"Target TTS model (default: {DEFAULT_TARGET_MODEL})",
    )

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List all custom voices")
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

    # Query subcommand
    query_parser = subparsers.add_parser("query", help="Query details of a specific voice")
    query_parser.add_argument(
        "voice_name",
        type=str,
        help="Name of the voice to query",
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
            voice_name, preview_path = await create_voice(
                voice_prompt=args.voice_prompt,
                preview_text=args.preview_text,
                preferred_name=args.name,
                target_model=args.target_model,
                language=args.language,
                sample_rate=args.sample_rate,
                response_format=args.format,
                output_path=args.output,
            )
            print()
            print(f"Voice ID for TTS: {voice_name}")
            print(f"Target model: {args.target_model}")
        elif args.action == "list":
            await list_voices(
                page_index=args.page_index,
                page_size=args.page_size,
            )
        elif args.action == "query":
            await query_voice(args.voice_name)
        elif args.action == "delete":
            await delete_voice(args.voice_name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
