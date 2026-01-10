"""
ElevenLabs Sound Effects - Text to Sound Effect Generation

Supported models: eleven_text_to_sound_v1, eleven_text_to_sound_v2
Supported duration: 0.5-30 seconds
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
    "eleven_text_to_sound_v1",
    "eleven_text_to_sound_v2",
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
]
DEFAULT_MODEL = "eleven_text_to_sound_v2"
MIN_DURATION = 0.5
MAX_DURATION = 30.0
DEFAULT_PROMPT_INFLUENCE = 0.3


async def generate_sound_effect(
    text: str,
    model_id: str = DEFAULT_MODEL,
    duration: float | None = None,
    prompt_influence: float = DEFAULT_PROMPT_INFLUENCE,
    loop: bool = False,
    output_format: str = "mp3_44100_128",
    output_path: str | None = None,
) -> Path:
    """
    Generate a sound effect using ElevenLabs Text-to-Sound Effects API.

    Args:
        text: Text description of the sound effect
        model_id: Model ID for sound generation
        duration: Duration in seconds (0.5-30, None for auto)
        prompt_influence: How closely to follow the prompt (0-1)
        loop: Create a seamless looping sound (v2 model only)
        output_format: Audio output format
        output_path: Output file path (optional)

    Returns:
        Path to the generated audio file
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {SUPPORTED_MODELS}")

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}. Supported: {SUPPORTED_OUTPUT_FORMATS}")

    if duration is not None:
        if duration < MIN_DURATION or duration > MAX_DURATION:
            raise ValueError(f"Duration must be between {MIN_DURATION} and {MAX_DURATION} seconds")

    if prompt_influence < 0 or prompt_influence > 1:
        raise ValueError("Prompt influence must be between 0 and 1")

    if loop and model_id != "eleven_text_to_sound_v2":
        raise ValueError("Loop parameter is only supported with eleven_text_to_sound_v2 model")

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

    output_file = Path(output_path) if output_path else Path(f"generated_sound{ext}")

    # Print generation info
    print(f"Prompt: {text}")
    duration_str = f"{duration}s" if duration else "auto"
    loop_str = ", loop" if loop else ""
    print(f"Generating sound effect (model: {model_id}, duration: {duration_str}, format: {output_format}{loop_str})...")

    # Generate sound effect (returns async generator directly, not awaitable)
    audio = client.text_to_sound_effects.convert(
        text=text,
        model_id=model_id,
        duration_seconds=duration,
        prompt_influence=prompt_influence,
        loop=loop,
        output_format=output_format,
    )

    # Write audio to file
    async with aiofiles.open(output_file, "wb") as f:
        async for chunk in audio:
            await f.write(chunk)

    print(f"Sound effect saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate sound effects using ElevenLabs Text-to-Sound Effects API"
    )
    parser.add_argument(
        "text",
        type=str,
        help="Text description of the sound effect",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"Model for sound generation (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-d", "--duration",
        type=float,
        default=None,
        help=f"Duration in seconds ({MIN_DURATION}-{MAX_DURATION}, default: auto)",
    )
    parser.add_argument(
        "-p", "--prompt-influence",
        type=float,
        default=DEFAULT_PROMPT_INFLUENCE,
        help=f"How closely to follow the prompt (0-1, default: {DEFAULT_PROMPT_INFLUENCE})",
    )
    parser.add_argument(
        "-l", "--loop",
        action="store_true",
        help="Create a seamless looping sound (v2 model only)",
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
        help="Output file path (default: generated_sound.<ext>)",
    )

    args = parser.parse_args()

    try:
        await generate_sound_effect(
            text=args.text,
            model_id=args.model,
            duration=args.duration,
            prompt_influence=args.prompt_influence,
            loop=args.loop,
            output_format=args.format,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())
