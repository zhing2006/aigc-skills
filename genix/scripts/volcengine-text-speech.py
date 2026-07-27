"""
Volcengine TTS - Streaming Text-to-Speech (Seed-TTS 2.0)

Synthesize speech from text using Volcengine Doubao Seed-TTS via the
HTTP chunked unidirectional streaming API.
Supported voices: official 2.0 voices (e.g. zh_female_vv_uranus_bigtts)
                  and cloned voices (S_xxxxxxxx, auto-routed to seed-icl-2.0)
Supported formats: MP3, WAV, PCM, OGG_OPUS
Delivery control: voice instructions (context_texts), dialects, pitch,
                  CoT voice tags (cloned expressive voices only)
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
# Cloned-voice model versions: the standard model has lower latency but silently
# drops voice instructions and CoT tags; the expressive model supports both.
CLONE_MODEL_STANDARD = "seed-tts-2.0-standard"
CLONE_MODEL_EXPRESSIVE = "seed-tts-2.0-expressive"
CLONE_MODELS = [CLONE_MODEL_STANDARD, CLONE_MODEL_EXPRESSIVE]
END_CODE = 20000000

SUPPORTED_FORMATS = ["mp3", "wav", "pcm", "ogg_opus"]
SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 24000, 32000, 44100, 48000]
SUPPORTED_LANGUAGES = [
    "zh-cn", "en", "ja", "es-mx", "id", "pt-br", "pt", "ko", "it", "de", "fr",
    "th", "vi", "ru", "fil", "ms", "ar", "pl", "tr", "sv",
]
SUPPORTED_DIALECTS = ["sichuan", "shaanxi", "dongbei"]
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
    """Detect the resource ID from the speaker ID prefix.

    Cloned voices use an ``S_`` ID or the lowercase ``icl_`` ID returned by the
    voice query API; official catalog voices (including the uppercase
    ``ICL_uranus_*_tob`` role-play family) stay on the TTS 2.0 resource.
    """
    if speaker.startswith("S_") or speaker.startswith("icl_"):
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
    cot_tags: bool = False,
    dialect: str | None = None,
    pitch: int = 0,
    section_id: str | None = None,
    tone_fidelity: bool = False,
    ssml: bool = False,
    silence_duration: int | None = None,
    explicit_language: str | None = None,
    keep_markdown: bool = False,
    strip_emoji: bool = False,
    filter_parenthesis: bool = False,
    latex: bool = False,
    latex_v2: bool = False,
    watermark: bool = False,
) -> tuple[bytes, list[dict], dict]:
    """
    Synthesize speech from text using Volcengine streaming TTS.

    Args:
        text: Text to synthesize
        speaker: Voice ID (official voice or cloned S_ voice)
        model: Cloned-voice model version (auto-selected when not set)
        resource_id: X-Api-Resource-Id override (auto-detected from speaker)
        audio_format: Output format (mp3/wav/pcm/ogg_opus)
        sample_rate: Audio sample rate in Hz
        bit_rate: MP3 bit rate in bps
        speech_rate: Speed, -50 (0.5x) to 100 (2.0x)
        loudness_rate: Loudness, -50 (0.5x) to 100 (2.0x)
        enable_subtitle: Return word-level timestamps
        instructions: Voice instructions (context_texts); only the first is used
        cot_tags: Parse <cot text=...>...</cot> tags (cloned expressive voices only)
        dialect: Dialect (sichuan/shaanxi/dongbei), needs a dialect-capable voice
        pitch: Pitch shift, -12 to 12
        section_id: Shared ID that carries context across successive requests
        tone_fidelity: Restore the training prompt's timbre/style (cloned voices)
        ssml: Parse text as SSML markup
        silence_duration: Trailing silence in ms (0-30000)
        explicit_language: Only read the specified language
        keep_markdown: Do not strip Markdown syntax before reading
        strip_emoji: Strip emoji instead of reading them
        filter_parenthesis: Skip text inside parentheses
        latex: Read LaTeX formulas
        latex_v2: Use the stronger LaTeX parser (implies latex)
        watermark: Add an audible AIGC watermark at the end

    Returns:
        Tuple of (audio bytes, sentence timestamps, usage info)
    """
    api_key = get_api_key()

    if resource_id is None:
        resource_id = detect_resource_id(speaker)

    is_clone_voice = resource_id == RESOURCE_ID_CLONE
    needs_expressive = bool(instructions) or cot_tags
    if model is None and is_clone_voice:
        model = CLONE_MODEL_EXPRESSIVE if needs_expressive else CLONE_MODEL_STANDARD

    if model and not is_clone_voice:
        print("Warning: --model only applies to cloned voices; official 2.0 voices ignore it.",
              file=sys.stderr)
    if is_clone_voice and needs_expressive and model == CLONE_MODEL_STANDARD:
        print(f"Warning: {CLONE_MODEL_STANDARD} drops voice instructions and CoT tags; "
              f"use -m {CLONE_MODEL_EXPRESSIVE} to keep them.", file=sys.stderr)
    if cot_tags and not is_clone_voice:
        print("Warning: CoT voice tags only work with Voice Clone 2.0 expressive voices; "
              "official 2.0 voices ignore them (use -I instructions instead).", file=sys.stderr)
    if tone_fidelity and not is_clone_voice:
        print("Warning: --tone-fidelity only applies to Voice Clone 2.0 voices.", file=sys.stderr)
    if instructions and len(instructions) > 1:
        print("Warning: only the first voice instruction takes effect.", file=sys.stderr)

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

    additions: dict = {}
    if silence_duration is not None:
        additions["silence_duration"] = silence_duration
    if filter_parenthesis:
        additions["max_length_to_filter_parenthesis"] = 100
    if not keep_markdown:
        additions["disable_markdown_filter"] = True
    if strip_emoji:
        additions["disable_emoji_filter"] = True
    if latex or latex_v2:
        additions["enable_latex_tn"] = True
    if latex_v2:
        additions["latex_parser"] = "v2"
    if explicit_language:
        additions["explicit_language"] = explicit_language
    if dialect:
        additions["explicit_dialect"] = dialect
    if watermark:
        additions["aigc_watermark"] = True
    if pitch:
        additions["post_process"] = {"pitch": pitch}
    if instructions:
        additions["context_texts"] = instructions
    if section_id:
        additions["section_id"] = section_id
    if cot_tags:
        additions["use_tag_parser"] = True
    if tone_fidelity:
        additions["tone_fidelity"] = True
    if additions:
        # additions must be a JSON-encoded string, not an object
        req_params["additions"] = json.dumps(additions, ensure_ascii=False)

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
    if instructions:
        print(f"Instruction: {instructions[0]}")
    if dialect:
        print(f"Dialect: {dialect}")
    if pitch:
        print(f"Pitch: {pitch:+d}")
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
        help="Text to synthesize (or use -i for file input)",
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
        choices=CLONE_MODELS,
        help="Cloned-voice model version (default: auto, "
             f"{CLONE_MODEL_EXPRESSIVE} when -I/--cot-tags is used, else {CLONE_MODEL_STANDARD})",
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
        help="Voice instruction (context_texts), e.g. \"用特别痛心的语气说话\"; only the first takes effect",
    )
    parser.add_argument(
        "--cot-tags",
        action="store_true",
        help="Parse <cot text=急促难耐>...</cot> voice tags (cloned expressive voices only)",
    )
    parser.add_argument(
        "--dialect",
        type=str,
        default=None,
        choices=SUPPORTED_DIALECTS,
        help="Dialect; requires a dialect-capable voice (e.g. zh_female_vv_uranus_bigtts)",
    )
    parser.add_argument(
        "--pitch",
        type=int,
        default=0,
        help="Pitch shift, -12 to 12 (default: 0)",
    )
    parser.add_argument(
        "--section-id",
        type=str,
        default=None,
        help="Shared ID that carries context across successive calls (max 30 turns / 10 min)",
    )
    parser.add_argument(
        "--tone-fidelity",
        action="store_true",
        help="Restore the training prompt's timbre and style (cloned voices, same language only)",
    )
    parser.add_argument(
        "--ssml",
        action="store_true",
        help="Parse the text as SSML markup (2.0 models support <phoneme> only)",
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
        "--strip-emoji",
        action="store_true",
        help="Strip emoji instead of reading them out",
    )
    parser.add_argument(
        "--filter-parenthesis",
        action="store_true",
        help="Skip text inside parentheses instead of reading it",
    )
    parser.add_argument(
        "--latex",
        action="store_true",
        help="Read LaTeX formulas (education scenarios)",
    )
    parser.add_argument(
        "--latex-v2",
        action="store_true",
        help="Use the stronger LaTeX parser (implies --latex, higher latency)",
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

    if args.pitch < -12 or args.pitch > 12:
        print("Error: Pitch must be between -12 and 12", file=sys.stderr)
        sys.exit(1)

    if args.latex_v2 and args.keep_markdown:
        print("Error: --latex-v2 requires Markdown filtering; drop --keep-markdown", file=sys.stderr)
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
            cot_tags=args.cot_tags,
            dialect=args.dialect,
            pitch=args.pitch,
            section_id=args.section_id,
            tone_fidelity=args.tone_fidelity,
            ssml=args.ssml,
            silence_duration=args.silence_duration,
            explicit_language=args.explicit_language,
            keep_markdown=args.keep_markdown,
            strip_emoji=args.strip_emoji,
            filter_parenthesis=args.filter_parenthesis,
            latex=args.latex,
            latex_v2=args.latex_v2,
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
