"""
DashScope TTS - WebSocket Text-to-Speech

Synthesize speech from text using DashScope Qwen TTS with system or custom
voices. The current Qwen-Audio-TTS models use the tts_v2 WebSocket protocol;
older Qwen3 realtime models remain supported through their legacy protocol.
"""

import argparse
import asyncio
import base64
import os
import struct
import sys
import threading
from pathlib import Path

import aiofiles
from dotenv import load_dotenv

# Import DashScope SDK for WebSocket TTS
try:
    import dashscope
    from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback
    from dashscope.audio.tts_v2 import (
        AudioFormat as TTSV2AudioFormat,
        ResultCallback as TTSV2ResultCallback,
        SpeechSynthesizer as TTSV2SpeechSynthesizer,
    )
except ImportError:
    print("Error: dashscope package not installed. Run: uv add dashscope", file=sys.stderr)
    sys.exit(1)


TTS_V2_MODELS = [
    "qwen-audio-3.0-tts-flash",
    "qwen-audio-3.0-tts-plus",
]

LEGACY_MODELS = [
    "qwen3-tts-flash-realtime",
    "qwen3-tts-flash-realtime-2025-11-27",
    "qwen-tts-realtime",
    "qwen-tts-realtime-latest",
    # Voice Design model
    "qwen3-tts-vd-realtime-2025-12-16",
    # Voice Clone models
    "qwen3-tts-vc-realtime-2026-01-15",
    "qwen3-tts-vc-realtime-2025-11-27",
]
SUPPORTED_MODELS = TTS_V2_MODELS + LEGACY_MODELS
DEFAULT_MODEL = "qwen-audio-3.0-tts-flash"
DEFAULT_VOICE = "Cherry"
DEFAULT_FORMAT = "wav"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_TTS_V2_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

SUPPORTED_FORMATS = ["pcm", "wav", "mp3", "opus"]
SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 24000, 44100, 48000]
SUPPORTED_LANGUAGE_HINTS = ["zh", "en"]
DEFAULT_VOICES = {
    "qwen-audio-3.0-tts-flash": "longanhuan_v3.6",
    "qwen-audio-3.0-tts-plus": "longanlingxin",
}

# System voices (common ones)
SYSTEM_VOICES = [
    "Cherry", "Serena", "Ethan", "Chelsie", "Momo", "Vivian", "Moon", "Maia",
    "Kai", "Nofish", "Bella", "Jennifer", "Ryan", "Katerina", "Aiden",
    "Eldric Sage", "Mia", "Mochi", "Bellona", "Vincent", "Bunny", "Neil",
    "Elias", "Arthur", "Nini", "Ebona", "Seren", "Pip", "Stella", "Bodega",
    "Sonrisa", "Alek", "Dolce", "Sohee", "Ono Anna", "Lenn", "Emilien",
    "Andre", "Radio Gol", "Jada", "Dylan", "Li", "Marcus", "Roy", "Peter",
    "Sunny", "Eric", "Rocky", "Kiki",
]


def get_api_key() -> str:
    """Get DashScope API key from environment."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")
    return api_key


def get_tts_v2_ws_url() -> str:
    """Get the WebSocket endpoint for the current Qwen-Audio-TTS API."""
    return os.environ.get("DASHSCOPE_TTS_WS_URL", DEFAULT_TTS_V2_WS_URL).rstrip("/")


def default_voice_for_model(model: str) -> str:
    """Return a sensible system voice for a model family."""
    return DEFAULT_VOICES.get(model, "Cherry")


def get_tts_v2_audio_format(audio_format: str, sample_rate: int):
    """Map CLI audio settings to the SDK enum when a matching value exists.

    The SDK enum omits a few combinations that the service accepts. Those
    combinations use DEFAULT plus explicit request parameters below.
    """
    prefix = {
        "wav": "WAV",
        "mp3": "MP3",
        "pcm": "PCM",
        "opus": "OGG_OPUS",
    }[audio_format]
    suffix = f"{sample_rate}HZ_MONO_16BIT"
    if audio_format == "mp3":
        bitrate = 128 if sample_rate in (8000, 16000) else 256
        suffix = f"{sample_rate}HZ_MONO_{bitrate}KBPS"
    elif audio_format == "opus":
        opus_rate = {8000: "8", 16000: "16", 24000: "24", 48000: "48"}.get(sample_rate)
        if opus_rate is None:
            return TTSV2AudioFormat.DEFAULT
        suffix = f"{opus_rate}KHZ_MONO_32KBPS"
    try:
        return getattr(TTSV2AudioFormat, f"{prefix}_{suffix}")
    except AttributeError:
        return TTSV2AudioFormat.DEFAULT


def finalize_wav_header(audio_data: bytes) -> bytes:
    """Replace streaming RIFF/data size placeholders with actual byte counts."""
    if len(audio_data) < 12 or audio_data[:4] != b"RIFF" or audio_data[8:12] != b"WAVE":
        return audio_data

    result = bytearray(audio_data)
    struct.pack_into("<I", result, 4, len(result) - 8)

    offset = 12
    while offset + 8 <= len(result):
        chunk_id = bytes(result[offset:offset + 4])
        if chunk_id == b"data":
            struct.pack_into("<I", result, offset + 4, len(result) - offset - 8)
            break

        chunk_size = struct.unpack_from("<I", result, offset + 4)[0]
        next_offset = offset + 8 + chunk_size + (chunk_size % 2)
        if next_offset <= offset or next_offset > len(result):
            break
        offset = next_offset

    return bytes(result)


class TTSCallback(QwenTtsRealtimeCallback):
    """Callback handler for TTS streaming response."""

    def __init__(self):
        super().__init__()
        self.audio_chunks: list[bytes] = []
        self.complete_event = threading.Event()
        self.error: Exception | None = None
        self.session_id: str | None = None

    def on_open(self) -> None:
        pass

    def on_close(self, close_status_code, close_msg) -> None:
        if close_status_code and close_status_code != 1000:
            self.error = RuntimeError(f"WebSocket closed with code {close_status_code}: {close_msg}")
        self.complete_event.set()

    def on_event(self, response: dict) -> None:
        try:
            event_type = response.get("type", "")

            if event_type == "session.created":
                self.session_id = response.get("session", {}).get("id")

            elif event_type == "response.audio.delta":
                audio_b64 = response.get("delta", "")
                if audio_b64:
                    self.audio_chunks.append(base64.b64decode(audio_b64))

            elif event_type == "response.done":
                self.complete_event.set()

            elif event_type == "session.finished":
                self.complete_event.set()

            elif event_type == "error":
                error_msg = response.get("error", {}).get("message", "Unknown error")
                self.error = RuntimeError(f"TTS error: {error_msg}")
                self.complete_event.set()

        except Exception as e:
            self.error = e
            self.complete_event.set()

    def on_error(self, error: Exception) -> None:
        self.error = error
        self.complete_event.set()

    def get_audio_data(self) -> bytes:
        """Get all collected audio data."""
        return b"".join(self.audio_chunks)

    def wait_for_complete(self, timeout: float = 120.0) -> None:
        """Wait for TTS to complete."""
        if not self.complete_event.wait(timeout=timeout):
            raise RuntimeError("TTS request timed out")
        if self.error:
            raise self.error


class TTSV2Callback(TTSV2ResultCallback):
    """Collect audio from the current Qwen-Audio-TTS SDK protocol."""

    def __init__(self):
        self.audio_chunks: list[bytes] = []
        self.error: Exception | None = None

    def on_data(self, data: bytes) -> None:
        self.audio_chunks.append(data)

    def on_error(self, message) -> None:
        self.error = RuntimeError(f"TTS error: {message}")

    def get_audio_data(self) -> bytes:
        return b"".join(self.audio_chunks)


def synthesize_speech_v2(
    text: str,
    voice: str,
    model: str,
    audio_format: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    volume: int = 50,
    speed: float = 1.0,
    pitch: float = 1.0,
    bit_rate: int | None = None,
    seed: int = 0,
    instruction: str | None = None,
    language_hint: str | None = None,
    enable_ssml: bool = False,
) -> bytes:
    """Synthesize with Qwen-Audio-TTS via the current WebSocket protocol."""
    api_key = get_api_key()
    dashscope.api_key = api_key

    if bit_rate is not None and audio_format != "opus":
        raise ValueError("bit-rate is only supported when format is opus")

    callback = TTSV2Callback()
    additional_params = {
        "format": audio_format,
        "sample_rate": sample_rate,
    }
    if bit_rate is not None:
        additional_params["bit_rate"] = bit_rate
    if enable_ssml:
        additional_params["enable_ssml"] = True

    synthesizer = TTSV2SpeechSynthesizer(
        model=model,
        voice=voice,
        format=get_tts_v2_audio_format(audio_format, sample_rate),
        volume=volume,
        speech_rate=speed,
        pitch_rate=pitch,
        seed=seed,
        instruction=instruction,
        language_hints=[language_hint] if language_hint else None,
        callback=callback,
        url=get_tts_v2_ws_url(),
        additional_params=additional_params,
    )

    print(f"Voice: {voice}")
    print(f"Model: {model}")
    print(f"Format: {audio_format}, Sample rate: {sample_rate}Hz")
    print("Synthesizing speech...")

    try:
        # Use streaming_call + streaming_complete instead of call(): dashscope
        # 1.25.x forces enable_ssml in call(), even for plain text requests.
        synthesizer.streaming_call(text)
        synthesizer.streaming_complete(complete_timeout_millis=120000)
    except Exception as e:
        try:
            synthesizer.close()
        except Exception:
            pass
        raise RuntimeError(f"TTS synthesis failed: {e}") from e

    if callback.error:
        raise callback.error

    audio_data = callback.get_audio_data()
    if not audio_data:
        raise RuntimeError("No audio data received from TTS")

    print(f"Request ID: {synthesizer.get_last_request_id()}")
    return audio_data


def synthesize_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    model: str = DEFAULT_MODEL,
    audio_format: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    volume: int = 50,
    speed: float = 1.0,
    pitch: float = 1.0,
    bit_rate: int | None = None,
) -> bytes:
    """
    Synthesize speech from text using DashScope TTS.

    Args:
        text: Text to synthesize
        voice: Voice name (e.g., Cherry, Jennifer)
        model: TTS model to use
        audio_format: Output format (pcm/wav/mp3/opus)
        sample_rate: Audio sample rate
        volume: Volume level (0-100)
        speed: Speech speed (0.5-2.0)
        pitch: Pitch adjustment (0.5-2.0)
        bit_rate: Opus bitrate in kbps

    Returns:
        Audio data as bytes
    """
    api_key = get_api_key()
    dashscope.api_key = api_key

    callback = TTSCallback()

    # Create TTS client
    tts = QwenTtsRealtime(
        model=model,
        callback=callback,
        url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
    )

    print(f"Voice: {voice}")
    print(f"Model: {model}")
    print(f"Format: {audio_format}, Sample rate: {sample_rate}Hz")
    print("Synthesizing speech...")

    try:
        # Connect and configure session
        tts.connect()

        # Update session with parameters
        tts.update_session(
            voice=voice,
            mode="commit",
            audio_format=audio_format,
            sample_rate=sample_rate,
            volume=volume,
            speech_rate=speed,
            pitch_rate=pitch,
            bit_rate=bit_rate,
        )

        # Send text and commit
        tts.append_text(text)
        tts.commit()

        # Wait for completion
        callback.wait_for_complete(timeout=120)

        # Finish session
        tts.finish()

    except Exception as e:
        try:
            tts.close()
        except Exception:
            pass
        raise RuntimeError(f"TTS synthesis failed: {e}")

    audio_data = callback.get_audio_data()
    if not audio_data:
        raise RuntimeError("No audio data received from TTS")

    return audio_data


async def main():
    parser = argparse.ArgumentParser(
        description="Synthesize speech from text using DashScope Qwen TTS"
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
        default=None,
        help="Voice name (defaults to a model-compatible system voice)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"TTS model (default: {DEFAULT_MODEL})",
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
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: auto-generated)",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=50,
        help="Volume level 0-100 (default: 50)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed 0.5-2.0 (default: 1.0)",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=1.0,
        help="Pitch adjustment 0.5-2.0 (default: 1.0)",
    )
    parser.add_argument(
        "--instruction",
        type=str,
        default=None,
        help="Natural-language instruction for emotion, dialect, or character (new models)",
    )
    parser.add_argument(
        "--language-hint",
        choices=SUPPORTED_LANGUAGE_HINTS,
        default=None,
        help="Target language hint (new models)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed 0-65535 (new models; default: 0)",
    )
    parser.add_argument(
        "--bit-rate",
        type=int,
        default=None,
        help="Opus bitrate in kbps, 6-510 (only with --format opus)",
    )
    parser.add_argument(
        "--ssml",
        action="store_true",
        help="Treat input as SSML (new models)",
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
    if args.volume < 0 or args.volume > 100:
        print("Error: Volume must be between 0 and 100", file=sys.stderr)
        sys.exit(1)

    if args.speed < 0.5 or args.speed > 2.0:
        print("Error: Speed must be between 0.5 and 2.0", file=sys.stderr)
        sys.exit(1)

    if args.pitch < 0.5 or args.pitch > 2.0:
        print("Error: Pitch must be between 0.5 and 2.0", file=sys.stderr)
        sys.exit(1)

    if args.seed < 0 or args.seed > 65535:
        print("Error: Seed must be between 0 and 65535", file=sys.stderr)
        sys.exit(1)

    if args.bit_rate is not None and (args.bit_rate < 6 or args.bit_rate > 510):
        print("Error: Bit rate must be between 6 and 510 kbps", file=sys.stderr)
        sys.exit(1)

    if args.bit_rate is not None and args.format != "opus":
        print("Error: --bit-rate is only supported with --format opus", file=sys.stderr)
        sys.exit(1)

    if args.model not in TTS_V2_MODELS and (
        args.instruction or args.language_hint or args.seed != 0 or args.ssml
    ):
        print(
            "Error: --instruction, --language-hint, --seed, and --ssml "
            "require a qwen-audio-3.0-tts-* model",
            file=sys.stderr,
        )
        sys.exit(1)

    voice = args.voice or default_voice_for_model(args.model)

    try:
        # Synthesize speech
        synthesis_args = {
            "text": text,
            "voice": voice,
            "model": args.model,
            "audio_format": args.format,
            "sample_rate": args.sample_rate,
            "volume": args.volume,
            "speed": args.speed,
            "pitch": args.pitch,
            "bit_rate": args.bit_rate,
        }
        if args.model in TTS_V2_MODELS:
            audio_data = synthesize_speech_v2(
                **synthesis_args,
                seed=args.seed,
                instruction=args.instruction,
                language_hint=args.language_hint,
                enable_ssml=args.ssml,
            )
        else:
            audio_data = synthesize_speech(**synthesis_args)

        if args.format == "wav":
            audio_data = finalize_wav_header(audio_data)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            ext = f".{args.format}" if args.format != "pcm" else ".pcm"
            output_path = Path(f"tts_output{ext}")

        # Save audio file
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(audio_data)

        print(f"Audio saved to: {output_path}")
        print(f"Size: {len(audio_data) / 1024:.1f} KB")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
