"""
DashScope TTS - Real-time Text-to-Speech

Synthesize speech from text using DashScope Qwen TTS with system voices.
Supported models: qwen3-tts-flash-realtime, qwen-tts-realtime
Supported formats: PCM, WAV, MP3, Opus
"""

import argparse
import asyncio
import base64
import os
import sys
import threading
from pathlib import Path

import aiofiles
from dotenv import load_dotenv

# Import DashScope SDK for WebSocket TTS
try:
    import dashscope
    from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback
except ImportError:
    print("Error: dashscope package not installed. Run: uv add dashscope", file=sys.stderr)
    sys.exit(1)


SUPPORTED_MODELS = [
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
DEFAULT_MODEL = "qwen3-tts-flash-realtime"
DEFAULT_VOICE = "Cherry"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000

SUPPORTED_FORMATS = ["pcm", "wav", "mp3", "opus"]
SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 24000, 44100, 48000]

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


def synthesize_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    model: str = DEFAULT_MODEL,
    audio_format: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    volume: int = 50,
    speed: float = 1.0,
    pitch: float = 1.0,
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
        default=DEFAULT_VOICE,
        help=f"Voice name (default: {DEFAULT_VOICE})",
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

    try:
        # Synthesize speech
        audio_data = synthesize_speech(
            text=text,
            voice=args.voice,
            model=args.model,
            audio_format=args.format,
            sample_rate=args.sample_rate,
            volume=args.volume,
            speed=args.speed,
            pitch=args.pitch,
        )

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
