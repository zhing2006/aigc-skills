"""
Volcengine TTS - Streaming Text-to-Speech (Seed-TTS 2.0)

Synthesize speech from text using Volcengine Doubao Seed-TTS via the
HTTP chunked unidirectional streaming API.
Supported voices: official 2.0 voices (e.g. zh_female_vv_uranus_bigtts)
                  and cloned voices (S_xxxxxxxx, auto-routed to seed-icl-2.0)
Supported formats: MP3, WAV, PCM, OGG_OPUS
"""

import argparse
import asyncio
import base64
import json
import os
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://openspeech.bytedance.com"
RESOURCE_ID_OFFICIAL = "seed-tts-2.0"  # Doubao Seed-TTS 2.0 official voices
RESOURCE_ID_CLONE = "seed-icl-2.0"     # Voice Clone 2.0 voices (S_ prefix)
CLONE_DEFAULT_MODEL = "seed-tts-2.0-standard"
END_CODE = 20000000

SUPPORTED_FORMATS = ["mp3", "wav", "pcm", "ogg_opus"]
SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 24000, 32000, 44100, 48000]
SUPPORTED_LANGUAGES = [
    "zh-cn", "en", "ja", "es-mx", "id", "pt-br", "pt", "ko", "de", "fr",
    "th", "vi", "ru", "fil", "ms", "ar",
]
DEFAULT_VOICE = "zh_female_vv_uranus_bigtts"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000


def get_api_key() -> str:
    """Get Volcengine speech API key from environment."""
    api_key = os.environ.get("VOLCENGINE_TTS_API_KEY")
    if not api_key:
        raise ValueError("VOLCENGINE_TTS_API_KEY environment variable is not set")
    return api_key


def get_base_url() -> str:
    """Get the OpenSpeech base URL from environment."""
    return os.environ.get("VOLCENGINE_TTS_BASE", DEFAULT_BASE_URL).rstrip("/")


def detect_resource_id(speaker: str) -> str:
    """Detect the resource ID from the speaker ID prefix."""
    if speaker.startswith("S_"):
        return RESOURCE_ID_CLONE
    return RESOURCE_ID_OFFICIAL


async def iter_json_events(response: aiohttp.ClientResponse) -> AsyncIterator[dict]:
    """Yield JSON objects from a chunked NDJSON-style response stream."""
    decoder = json.JSONDecoder()
    buffer = ""
    async for chunk in response.content.iter_any():
        buffer += chunk.decode("utf-8")
        while True:
            stripped = buffer.lstrip()
            if not stripped:
                buffer = ""
                break
            try:
                obj, index = decoder.raw_decode(stripped)
            except json.JSONDecodeError:
                # Incomplete JSON object, wait for the next chunk
                buffer = stripped
                break
            buffer = stripped[index:]
            yield obj


async def synthesize_speech(
    text: str,
    speaker: str = DEFAULT_VOICE,
    model: str | None = None,
    resource_id: str | None = None,
    audio_format: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    bit_rate: int | None = None,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    enable_subtitle: bool = False,
    instructions: list[str] | None = None,
    ssml: bool = False,
    silence_duration: int | None = None,
    explicit_language: str | None = None,
    keep_markdown: bool = False,
    watermark: bool = False,
) -> tuple[bytes, list[dict], dict]:
    """
    Synthesize speech from text using Volcengine streaming TTS.

    Args:
        text: Text to synthesize (may contain [voice tags] before sentences)
        speaker: Voice ID (official voice or cloned S_ voice)
        model: Model version (auto: seed-tts-2.0-standard for cloned voices)
        resource_id: X-Api-Resource-Id override (auto-detected from speaker)
        audio_format: Output format (mp3/wav/pcm/ogg_opus)
        sample_rate: Audio sample rate in Hz
        bit_rate: MP3 bit rate in bps
        speech_rate: Speed, -50 (0.5x) to 100 (2.0x)
        loudness_rate: Loudness, -50 (0.5x) to 100 (2.0x)
        enable_subtitle: Return word-level timestamps
        instructions: Voice instructions (context_texts), official voices only
        ssml: Parse text as SSML markup
        silence_duration: Trailing silence in ms (0-30000)
        explicit_language: Only read the specified language
        keep_markdown: Do not strip Markdown syntax before reading
        watermark: Add an audible AIGC watermark at the end

    Returns:
        Tuple of (audio bytes, sentence timestamps, usage info)
    """
    api_key = get_api_key()

    if resource_id is None:
        resource_id = detect_resource_id(speaker)

    is_clone_voice = resource_id == RESOURCE_ID_CLONE
    if model is None and is_clone_voice:
        model = CLONE_DEFAULT_MODEL

    audio_params: dict = {
        "format": audio_format,
        "sample_rate": sample_rate,
        "speech_rate": speech_rate,
        "loudness_rate": loudness_rate,
    }
    if bit_rate is not None:
        audio_params["bit_rate"] = bit_rate
    if enable_subtitle:
        audio_params["enable_subtitle"] = True

    req_params: dict = {
        "text": text,
        "speaker": speaker,
        "audio_params": audio_params,
    }
    if model:
        req_params["model"] = model
    if ssml:
        req_params["ssml"] = text

    if instructions:
        if is_clone_voice:
            print("Warning: voice instructions (context_texts) are not supported "
                  "by cloned voices; ignoring them.", file=sys.stderr)
        else:
            req_params["context_texts"] = instructions

    additions: dict = {}
    if silence_duration is not None:
        additions["silence_duration"] = silence_duration
    if explicit_language:
        additions["explicit_language"] = explicit_language
    if not keep_markdown:
        additions["disable_markdown_filter"] = True
    if watermark:
        additions["aigc_watermark"] = True
    if additions:
        # additions must be a JSON-encoded string, not an object
        req_params["additions"] = json.dumps(additions)

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": str(uuid.uuid4()),
    }
    payload = {"req_params": req_params}

    print(f"Voice: {speaker}")
    print(f"Resource ID: {resource_id}" + (f", Model: {model}" if model else ""))
    print(f"Format: {audio_format}, Sample rate: {sample_rate}Hz")
    print("Synthesizing speech...")

    audio_parts: list[bytes] = []
    sentences: list[dict] = []
    usage: dict = {}
    finished = False

    endpoint = f"{get_base_url()}/api/v3/tts/unidirectional"
    timeout = aiohttp.ClientTimeout(total=600, sock_read=60)
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, headers=headers, json=payload, timeout=timeout) as response:
            logid = response.headers.get("X-Tt-Logid", "")
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"API request failed ({response.status}): {error_text} [logid={logid}]")

            async for event in iter_json_events(response):
                code = event.get("code", 0)
                if code == 0:
                    if event.get("data"):
                        audio_parts.append(base64.b64decode(event["data"]))
                    if event.get("sentence"):
                        sentences.append(event["sentence"])
                elif code == END_CODE:
                    usage = event.get("usage") or {}
                    finished = True
                    break
                else:
                    message = event.get("message", "Unknown error")
                    raise RuntimeError(f"TTS failed ({code}): {message} [logid={logid}]")

    if not audio_parts:
        raise RuntimeError("No audio data received from TTS")

    if not finished:
        print("Warning: stream ended without a completion event; audio may be truncated.", file=sys.stderr)

    return b"".join(audio_parts), sentences, usage


async def main():
    parser = argparse.ArgumentParser(
        description="Synthesize speech from text using Volcengine Doubao Seed-TTS 2.0"
    )

    parser.add_argument(
        "text",
        type=str,
        nargs="?",
        help="Text to synthesize; may contain [voice tags] before sentences (or use -i for file input)",
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=None,
        help="Input text file path",
    )
    parser.add_argument(
        "-v", "--voice",
        type=str,
        default=DEFAULT_VOICE,
        help=f"Voice ID; S_ prefix means a cloned voice (default: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help=f"Model version (default: auto, {CLONE_DEFAULT_MODEL} for cloned voices)",
    )
    parser.add_argument(
        "--resource-id",
        type=str,
        default=None,
        choices=[RESOURCE_ID_OFFICIAL, RESOURCE_ID_CLONE],
        help="Override the auto-detected X-Api-Resource-Id",
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        default=DEFAULT_FORMAT,
        choices=SUPPORTED_FORMATS,
        help=f"Output audio format (default: {DEFAULT_FORMAT})",
    )
    parser.add_argument(
        "-r", "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        choices=SUPPORTED_SAMPLE_RATES,
        help=f"Sample rate in Hz (default: {DEFAULT_SAMPLE_RATE})",
    )
    parser.add_argument(
        "--bit-rate",
        type=int,
        default=None,
        help="MP3 bit rate in bps, 64000-160000 (mp3 only)",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=0,
        help="Speech rate, -50 (0.5x) to 100 (2.0x) (default: 0)",
    )
    parser.add_argument(
        "--loudness",
        type=int,
        default=0,
        help="Loudness rate, -50 (0.5x) to 100 (2.0x) (default: 0)",
    )
    parser.add_argument(
        "-I", "--instruction",
        action="append",
        default=None,
        help="Voice instruction (context_texts), e.g. \"用特别痛心的语气说话\"; repeatable; official voices only",
    )
    parser.add_argument(
        "--ssml",
        action="store_true",
        help="Parse the text as SSML markup",
    )
    parser.add_argument(
        "--subtitle",
        action="store_true",
        help="Save word-level timestamps to <output>.json (Chinese/English only)",
    )
    parser.add_argument(
        "--silence-duration",
        type=int,
        default=None,
        help="Trailing silence in ms, 0-30000",
    )
    parser.add_argument(
        "--explicit-language",
        type=str,
        default=None,
        choices=SUPPORTED_LANGUAGES,
        help="Only read the specified language",
    )
    parser.add_argument(
        "--keep-markdown",
        action="store_true",
        help="Read Markdown syntax literally instead of stripping it",
    )
    parser.add_argument(
        "--watermark",
        action="store_true",
        help="Add an audible AIGC watermark at the end of the audio",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: tts_output.<format>)",
    )

    args = parser.parse_args()

    # Get text from argument or file
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        async with aiofiles.open(input_path, "r", encoding="utf-8") as f:
            text = await f.read()
    elif args.text:
        text = args.text
    else:
        print("Error: Either text argument or -i/--input is required", file=sys.stderr)
        sys.exit(1)

    # Validate parameters
    if args.speed < -50 or args.speed > 100:
        print("Error: Speed must be between -50 and 100", file=sys.stderr)
        sys.exit(1)

    if args.loudness < -50 or args.loudness > 100:
        print("Error: Loudness must be between -50 and 100", file=sys.stderr)
        sys.exit(1)

    if args.silence_duration is not None and (args.silence_duration < 0 or args.silence_duration > 30000):
        print("Error: Silence duration must be between 0 and 30000", file=sys.stderr)
        sys.exit(1)

    try:
        audio_data, sentences, usage = await synthesize_speech(
            text=text,
            speaker=args.voice,
            model=args.model,
            resource_id=args.resource_id,
            audio_format=args.format,
            sample_rate=args.sample_rate,
            bit_rate=args.bit_rate,
            speech_rate=args.speed,
            loudness_rate=args.loudness,
            enable_subtitle=args.subtitle,
            instructions=args.instruction,
            ssml=args.ssml,
            silence_duration=args.silence_duration,
            explicit_language=args.explicit_language,
            keep_markdown=args.keep_markdown,
            watermark=args.watermark,
        )

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            ext = "ogg" if args.format == "ogg_opus" else args.format
            output_path = Path(f"tts_output.{ext}")

        # Save audio file
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(audio_data)

        print(f"Audio saved to: {output_path}")
        print(f"Size: {len(audio_data) / 1024:.1f} KB")

        if args.subtitle and sentences:
            subtitle_path = output_path.with_suffix(output_path.suffix + ".json")
            async with aiofiles.open(subtitle_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(sentences, ensure_ascii=False, indent=2))
            print(f"Subtitles saved to: {subtitle_path}")

        if usage.get("text_words"):
            print(f"Billed characters: {usage['text_words']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
