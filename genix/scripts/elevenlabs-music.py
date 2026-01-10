"""
ElevenLabs Music - Text to Music Generation

Supported duration: 10-300 seconds (10s - 5min)
Supported output formats: MP3, PCM, Opus
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from elevenlabs.client import AsyncElevenLabs


SUPPORTED_MODELS = [
    "music_v1",
]
SUPPORTED_OUTPUT_FORMATS = [
    "mp3_22050_32",
    "mp3_44100_64",
    "mp3_44100_128",
    "mp3_44100_192",
    "pcm_16000",
    "pcm_22050",
    "pcm_44100",
    "pcm_48000",
    "opus_48000_64",
    "opus_48000_128",
    "opus_48000_192",
]
DEFAULT_MODEL = "music_v1"
MIN_DURATION = 10  # seconds
MAX_DURATION = 300  # seconds (5 minutes)


async def generate_music(
    prompt: str,
    model_id: str = DEFAULT_MODEL,
    duration: int = 30,
    instrumental: bool = False,
    output_format: str = "mp3_44100_128",
    output_path: str | None = None,
) -> Path:
    """
    Generate music using ElevenLabs Music API.

    Args:
        prompt: Text description of the music to generate
        model_id: Model ID for music generation
        duration: Duration in seconds (10-300)
        instrumental: Force instrumental (no vocals)
        output_format: Audio output format
        output_path: Output file path (optional)

    Returns:
        Path to the generated audio file
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {SUPPORTED_MODELS}")

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}. Supported: {SUPPORTED_OUTPUT_FORMATS}")

    if duration < MIN_DURATION or duration > MAX_DURATION:
        raise ValueError(f"Duration must be between {MIN_DURATION} and {MAX_DURATION} seconds")

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

    client = AsyncElevenLabs(api_key=api_key)

    # Determine file extension from format
    if output_format.startswith("mp3"):
        ext = ".mp3"
    elif output_format.startswith("pcm"):
        ext = ".wav"
    elif output_format.startswith("opus"):
        ext = ".opus"
    else:
        ext = ".mp3"

    output_file = Path(output_path) if output_path else Path(f"generated_music{ext}")

    # Print generation info
    print(f"Prompt: {prompt}")
    instrumental_str = ", instrumental" if instrumental else ""
    print(f"Generating music ({duration}s, model: {model_id}, format: {output_format}{instrumental_str})...")

    # Generate music (returns async generator directly, not awaitable)
    audio = client.music.compose(
        prompt=prompt,
        model_id=model_id,
        music_length_ms=duration * 1000,
        force_instrumental=instrumental,
        output_format=output_format,
    )

    # Write audio to file
    async with aiofiles.open(output_file, "wb") as f:
        async for chunk in audio:
            await f.write(chunk)

    print(f"Music saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate music using ElevenLabs Music API"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text description of the music to generate",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"Model for music generation (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=30,
        help=f"Duration in seconds ({MIN_DURATION}-{MAX_DURATION}, default: 30)",
    )
    parser.add_argument(
        "-i", "--instrumental",
        action="store_true",
        help="Force instrumental (no vocals)",
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        default="mp3_44100_128",
        choices=SUPPORTED_OUTPUT_FORMATS,
        help="Output audio format (default: mp3_44100_128)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: generated_music.<ext>)",
    )

    args = parser.parse_args()

    try:
        await generate_music(
            prompt=args.prompt,
            model_id=args.model,
            duration=args.duration,
            instrumental=args.instrumental,
            output_format=args.format,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())
