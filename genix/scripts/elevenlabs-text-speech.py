"""
ElevenLabs Text-to-Speech - Text to Speech Generation

Supported models: eleven_v4, eleven_v4_turbo, eleven_v3,
                  eleven_multilingual_v2, eleven_flash_v2_5
Supported output formats: MP3, PCM, Opus
Features: Voice search, voice settings (stability, similarity, speed, style),
          previous-text context, language selection
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from elevenlabs.client import AsyncElevenLabs
from elevenlabs.types import VoiceSettings


SUPPORTED_MODELS = [
    "eleven_v4",
    "eleven_v4_turbo",
    "eleven_v3",
    "eleven_multilingual_v2",
    "eleven_flash_v2_5",
]
V4_MODELS = {"eleven_v4", "eleven_v4_turbo"}
MODEL_CHARACTER_LIMITS = {
    "eleven_v4": 10_000,
    "eleven_v4_turbo": 10_000,
    "eleven_v3": 5_000,
    "eleven_multilingual_v2": 10_000,
    "eleven_flash_v2_5": 40_000,
}
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
DEFAULT_MODEL = "eleven_v4"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel
DEFAULT_VOICE_NAME = "Rachel"


async def search_voice(client: AsyncElevenLabs, query: str) -> tuple[str, str] | None:
    """
    Search for a voice by description and return the first matching voice.

    Searches in two places:
    1. User's own voices (via voices.search)
    2. Voice Library (via voices.get_shared)

    Args:
        client: ElevenLabs async client
        query: Search query (e.g., "British male", "female narrator")

    Returns:
        Tuple of (voice_id, voice_name) or None if not found
    """
    # First, search user's own voices
    result = await client.voices.search(search=query, page_size=1)
    if result.voices and len(result.voices) > 0:
        voice = result.voices[0]
        return (voice.voice_id, voice.name)

    # If not found, search Voice Library
    shared_result = await client.voices.get_shared(search=query, page_size=1)
    if shared_result.voices and len(shared_result.voices) > 0:
        voice = shared_result.voices[0]
        return (voice.voice_id, voice.name)

    return None


async def generate_speech(
    text: str,
    voice_id: str | None = None,
    voice_search: str | None = None,
    model_id: str = DEFAULT_MODEL,
    output_format: str = "mp3_44100_128",
    stability: float | None = None,
    similarity_boost: float | None = None,
    speed: float | None = None,
    output_path: str | None = None,
    previous_text: str | None = None,
    style: float | None = None,
    language_code: str | None = None,
) -> Path:
    """
    Generate speech using ElevenLabs Text-to-Speech API.

    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use (optional)
        voice_search: Search query to find a voice (optional)
        model_id: Model to use for generation
        output_format: Audio output format
        stability: Voice stability (0-1)
        similarity_boost: Voice similarity (0-1)
        speed: Speech speed (0.7-1.2, unsupported by v4 models)
        output_path: Output file path (optional)
        previous_text: Preceding text for continuity; not spoken in this request
        style: Voice style exaggeration (0-1, unsupported by v4 models)
        language_code: Language code (e.g., en, zh; unsupported by multilingual_v2)

    Returns:
        Path to the generated audio file
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {SUPPORTED_MODELS}")

    if not text.strip():
        raise ValueError("Text must not be empty")
    character_limit = MODEL_CHARACTER_LIMITS[model_id]
    if len(text) > character_limit:
        raise ValueError(
            f"Text exceeds the {character_limit:,}-character limit for {model_id}. "
            "Split it into shorter requests."
        )

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}. Supported: {SUPPORTED_OUTPUT_FORMATS}")

    if stability is not None:
        if not 0 <= stability <= 1:
            raise ValueError("Stability must be between 0 and 1")
        # For eleven_v3, snap to nearest valid value (0.0, 0.5, 1.0)
        if model_id == "eleven_v3":
            valid_values = [0.0, 0.5, 1.0]
            original = stability
            stability = min(valid_values, key=lambda x: abs(x - stability))
            if original != stability:
                labels = {0.0: "Creative", 0.5: "Natural", 1.0: "Robust"}
                print(f"Note: Stability {original} adjusted to {stability} ({labels[stability]}) for eleven_v3")

    if similarity_boost is not None and not 0 <= similarity_boost <= 1:
        raise ValueError("Similarity boost must be between 0 and 1")

    if style is not None:
        if model_id in V4_MODELS:
            raise ValueError(
                f"{model_id} does not support --style. Use audio tags to guide delivery, "
                "or select --model eleven_multilingual_v2 for style exaggeration."
            )
        if not 0 <= style <= 1:
            raise ValueError("Style must be between 0 and 1")

    if language_code is not None:
        language_code = language_code.strip().lower()
        if not language_code:
            raise ValueError("Language code must not be empty")
        if model_id == "eleven_multilingual_v2":
            raise ValueError(
                "eleven_multilingual_v2 does not support --language-code. "
                "Omit it for automatic language detection, or select --model eleven_v4."
            )

    if speed is not None:
        if model_id in V4_MODELS:
            raise ValueError(
                f"{model_id} does not support --speed. Use audio tags and punctuation "
                "to guide pacing, or select --model eleven_multilingual_v2 for speed control."
            )
        if not 0.7 <= speed <= 1.2:
            raise ValueError("Speed must be between 0.7 and 1.2")

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

    client = AsyncElevenLabs(api_key=api_key)

    # Determine voice to use
    voice_name = DEFAULT_VOICE_NAME
    if voice_id:
        # Use provided voice_id directly
        pass
    elif voice_search:
        # Search for voice
        print(f"Searching for voice: {voice_search}...")
        result = await search_voice(client, voice_search)
        if result:
            voice_id, voice_name = result
            print(f"Found voice: {voice_name} ({voice_id})")
        else:
            print(f"No voice found for '{voice_search}', using default voice: {DEFAULT_VOICE_NAME}")
            voice_id = DEFAULT_VOICE_ID
    else:
        # Use default voice
        voice_id = DEFAULT_VOICE_ID

    # Build voice settings if any provided
    voice_settings = None
    if any(value is not None for value in (stability, similarity_boost, speed, style)):
        settings = {
            "stability": stability if stability is not None else 0.5,
            "similarity_boost": similarity_boost if similarity_boost is not None else 0.75,
        }
        # V4 accepts stability and similarity only; even a default speed is unsupported.
        if model_id not in V4_MODELS:
            settings["speed"] = speed if speed is not None else 1.0
        if style is not None:
            settings["style"] = style
        voice_settings = VoiceSettings(**settings)

    # Determine file extension from format
    if output_format.startswith("mp3"):
        ext = ".mp3"
    elif output_format.startswith("pcm"):
        ext = ".wav"
    elif output_format.startswith("opus"):
        ext = ".opus"
    else:
        ext = ".mp3"

    output_file = Path(output_path) if output_path else Path(f"generated_speech{ext}")

    # Print generation info
    text_preview = text[:50] + "..." if len(text) > 50 else text
    print(f"Text: {text_preview}")
    print(f"Generating speech (voice: {voice_name}, model: {model_id}, format: {output_format})...")

    # Generate speech
    request_fields = {}
    if previous_text is not None:
        request_fields["previous_text"] = previous_text
    if language_code is not None:
        request_fields["language_code"] = language_code
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
        voice_settings=voice_settings,
        **request_fields,
    )

    # Write audio to file
    async with aiofiles.open(output_file, "wb") as f:
        async for chunk in audio:
            await f.write(chunk)

    print(f"Speech saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate speech using ElevenLabs Text-to-Speech API"
    )
    parser.add_argument(
        "text",
        type=str,
        help="Text to convert to speech",
    )
    parser.add_argument(
        "-v", "--voice-id",
        type=str,
        default=None,
        help=f"Voice ID to use (default: {DEFAULT_VOICE_ID} - {DEFAULT_VOICE_NAME})",
    )
    parser.add_argument(
        "-s", "--voice-search",
        type=str,
        default=None,
        help="Search query to find a voice (e.g., 'British male', 'female narrator')",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        default="mp3_44100_128",
        choices=SUPPORTED_OUTPUT_FORMATS,
        help="Output audio format (default: mp3_44100_128)",
    )
    parser.add_argument(
        "--stability",
        type=float,
        default=None,
        help="Voice stability (0-1, higher = more consistent)",
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=None,
        help="Voice similarity boost (0-1)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="Speech speed for v3/v2 models only (0.7-1.2, default: 1.0); unsupported by v4",
    )
    parser.add_argument(
        "--previous-text",
        type=str,
        default=None,
        help="Preceding text for speech continuity (context only, not spoken)",
    )
    parser.add_argument(
        "--style",
        type=float,
        default=None,
        help="Voice style exaggeration (0-1); unsupported by v4",
    )
    parser.add_argument(
        "--language-code",
        type=str,
        default=None,
        help="Language code (e.g., en, zh); unsupported by eleven_multilingual_v2",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: generated_speech.<ext>)",
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.voice_id and args.voice_search:
        print("Warning: Both --voice-id and --voice-search provided, using --voice-id", file=sys.stderr)

    try:
        await generate_speech(
            text=args.text,
            voice_id=args.voice_id,
            voice_search=args.voice_search,
            model_id=args.model,
            output_format=args.format,
            stability=args.stability,
            similarity_boost=args.similarity,
            speed=args.speed,
            output_path=args.output,
            previous_text=args.previous_text,
            style=args.style,
            language_code=args.language_code,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
