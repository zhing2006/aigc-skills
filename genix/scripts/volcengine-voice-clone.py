"""
Volcengine Voice Clone - Clone and Manage Voices (Voice Clone 2.0)

Supported actions: train, status, upgrade, list, order, renew
Supported audio formats: WAV, MP3, OGG, M4A, AAC, PCM (24kHz mono only)
Supported languages: cn, en, ja, es, id, pt, de, fr, ko, th, vi, ru, fil, ms, ar, mx, pt-br

Note: train/status/upgrade use the OpenSpeech API (VOLCENGINE_TTS_API_KEY);
list/order/renew use the account management API (VOLCENGINE_ACCESS_KEY /
VOLCENGINE_SECRET_KEY / VOLCENGINE_TTS_APPID). order/renew are PAID operations.
"""

import argparse
import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import os
import sys
import urllib.parse
import uuid
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://openspeech.bytedance.com"
MGMT_HOST = "open.volcengineapi.com"
MGMT_VERSION = "2023-11-07"
MGMT_REGION = "cn-north-1"
MGMT_SERVICE = "speech_saas_prod"

LANGUAGE_MAP = {
    "cn": 0, "en": 1, "ja": 2, "es": 3, "id": 4, "pt": 5, "de": 6, "fr": 7,
    "ko": 8, "th": 10, "vi": 11, "ru": 12, "fil": 13, "ms": 14, "ar": 15,
    "mx": 16, "pt-br": 17,
}
SUPPORTED_AUDIO_FORMATS = {
    ".wav": "wav",
    ".mp3": "mp3",
    ".ogg": "ogg",
    ".m4a": "m4a",
    ".aac": "aac",
    ".pcm": "pcm",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
STATUS_NAMES = {0: "NotFound", 1: "Training", 2: "Success", 3: "Failed", 4: "Active"}
MGMT_STATES = ["Unknown", "Training", "Success", "Active", "Expired", "Reclaimed"]


def get_api_key() -> str:
    """Get Volcengine speech API key from environment."""
    api_key = os.environ.get("VOLCENGINE_TTS_API_KEY")
    if not api_key:
        raise ValueError("VOLCENGINE_TTS_API_KEY environment variable is not set")
    return api_key


def get_base_url() -> str:
    """Get the OpenSpeech base URL from environment."""
    return os.environ.get("VOLCENGINE_TTS_BASE", DEFAULT_BASE_URL).rstrip("/")


def get_mgmt_credentials() -> tuple[str, str, str]:
    """Get management API credentials (access key, secret key, app ID)."""
    access_key = os.environ.get("VOLCENGINE_ACCESS_KEY")
    secret_key = os.environ.get("VOLCENGINE_SECRET_KEY")
    app_id = os.environ.get("VOLCENGINE_TTS_APPID")
    if not access_key:
        raise ValueError("VOLCENGINE_ACCESS_KEY environment variable is not set")
    if not secret_key:
        raise ValueError("VOLCENGINE_SECRET_KEY environment variable is not set")
    if not app_id:
        raise ValueError("VOLCENGINE_TTS_APPID environment variable is not set")
    return access_key, secret_key, app_id


def speaker_params(speaker_id: str, custom: bool) -> dict:
    """Build speaker_id/custom_speaker_id request fields."""
    if custom:
        return {"speaker_id": "custom_speaker_id", "custom_speaker_id": speaker_id}
    return {"speaker_id": speaker_id}


async def openspeech_post(path: str, body: dict, timeout: int = 120) -> tuple[dict, str]:
    """POST to the OpenSpeech voice clone API. Returns (response JSON, logid)."""
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
            data = await response.json()
    return data, logid


def sign_mgmt_request(action: str, body: bytes, access_key: str, secret_key: str) -> tuple[str, dict]:
    """
    Sign a management API request with the Volcengine HMAC-SHA256 (SigV4-style) scheme.

    Returns (url, headers).
    """
    x_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short_date = x_date[:8]
    payload_hash = hashlib.sha256(body).hexdigest()

    query = {"Action": action, "Version": MGMT_VERSION}
    canonical_query = "&".join(
        f"{urllib.parse.quote(k, safe='-_.~')}={urllib.parse.quote(v, safe='-_.~')}"
        for k, v in sorted(query.items())
    )

    canonical_headers = (
        f"content-type:application/json; charset=utf-8\n"
        f"host:{MGMT_HOST}\n"
        f"x-content-sha256:{payload_hash}\n"
        f"x-date:{x_date}\n"
    )
    signed_headers = "content-type;host;x-content-sha256;x-date"

    canonical_request = "\n".join([
        "POST",
        "/",
        canonical_query,
        canonical_headers,
        signed_headers,
        payload_hash,
    ])

    scope = f"{short_date}/{MGMT_REGION}/{MGMT_SERVICE}/request"
    string_to_sign = "\n".join([
        "HMAC-SHA256",
        x_date,
        scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    key = secret_key.encode("utf-8")
    for part in (short_date, MGMT_REGION, MGMT_SERVICE, "request"):
        key = hmac.new(key, part.encode("utf-8"), hashlib.sha256).digest()
    signature = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Date": x_date,
        "X-Content-Sha256": payload_hash,
        "Authorization": (
            f"HMAC-SHA256 Credential={access_key}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        ),
    }
    url = f"https://{MGMT_HOST}/?{canonical_query}"
    return url, headers


async def call_mgmt_api(action: str, body: dict) -> dict:
    """Call a signed management API action and return its Result."""
    access_key, secret_key, _ = get_mgmt_credentials()
    body_bytes = json.dumps(body).encode("utf-8")
    url, headers = sign_mgmt_request(action, body_bytes, access_key, secret_key)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=body_bytes,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            text = await response.text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                raise RuntimeError(f"API request failed ({response.status}): {text}")

    metadata = data.get("ResponseMetadata", {})
    error = metadata.get("Error")
    if error:
        raise RuntimeError(f"{action} failed: {error.get('Code')}: {error.get('Message')}")
    return data.get("Result", {})


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
    """Print the voice status fields returned by voice_clone/get_voice/upgrade_voice."""
    status = data.get("status")
    print(f"Speaker ID: {data.get('speaker_id', '')}")
    print(f"Status: {status} ({STATUS_NAMES.get(status, 'Unknown')})")
    if data.get("available_training_times") is not None:
        print(f"Remaining training times: {data['available_training_times']}")
    if data.get("create_time"):
        print(f"Create time: {data['create_time']}")
    if status in (2, 4):
        print("The voice is ready for TTS synthesis (use volcengine-text-speech.py).")


async def train_voice(
    audio_file: str,
    speaker_id: str,
    custom: bool = False,
    text: str | None = None,
    language: str | None = None,
    demo_text: str | None = None,
    denoise: bool = False,
    no_volume_normalization: bool = False,
) -> dict:
    """Train a cloned voice from an audio sample."""
    file_path = Path(audio_file)
    if not file_path.exists():
        raise ValueError(f"Audio file not found: {audio_file}")

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"Audio file too large: {file_size / 1024 / 1024:.1f}MB. Maximum: 10MB")

    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {ext}. Supported: {list(SUPPORTED_AUDIO_FORMATS.keys())}")
    audio_format = SUPPORTED_AUDIO_FORMATS[ext]
    if audio_format == "pcm":
        print("Note: PCM samples must be 24kHz mono.")

    if language is not None and language not in LANGUAGE_MAP:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(LANGUAGE_MAP.keys())}")

    print(f"Reading audio file: {file_path}")
    async with aiofiles.open(file_path, "rb") as f:
        audio_bytes = await f.read()

    body: dict = speaker_params(speaker_id, custom)
    body["audio"] = {
        "data": base64.b64encode(audio_bytes).decode(),
        "format": audio_format,
    }
    if text:
        body["text"] = text
    if language is not None:
        body["language"] = LANGUAGE_MAP[language]

    extra_params: dict = {}
    if demo_text:
        extra_params["demo_text"] = demo_text
    if denoise:
        extra_params["enable_audio_denoise"] = True
    if no_volume_normalization:
        extra_params["disable_volume_normalization"] = True
    if extra_params:
        body["extra_params"] = extra_params

    print(f"Speaker ID: {speaker_id}")
    print("Training cloned voice...")

    data, _ = await openspeech_post("voice_clone", body, timeout=300)
    return data


async def get_voice_status(speaker_id: str, custom: bool = False) -> dict:
    """Query the training status of a voice."""
    print(f"Querying voice: {speaker_id}...")
    data, _ = await openspeech_post("get_voice", speaker_params(speaker_id, custom))
    return data


async def upgrade_voice(speaker_id: str, custom: bool = False) -> dict:
    """Upgrade a V1 cloned voice to V3 so it can be used across products."""
    print(f"Upgrading voice: {speaker_id}...")
    data, _ = await openspeech_post("upgrade_voice", speaker_params(speaker_id, custom))
    return data


async def list_voices(
    speaker_ids: list[str] | None = None,
    state: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> list[dict]:
    """List purchased voice instances and their states (management API)."""
    _, _, app_id = get_mgmt_credentials()

    body: dict = {
        "AppID": app_id,
        "PageNumber": page,
        "PageSize": page_size,
    }
    if speaker_ids:
        body["SpeakerIDs"] = speaker_ids
    if state:
        body["State"] = state

    print(f"Fetching voices (page {page}, size {page_size})...")
    result = await call_mgmt_api("BatchListMegaTTSTrainStatus", body)

    statuses = result.get("Statuses") or []
    total = result.get("TotalCount", len(statuses))
    print(f"Found {total} voice(s) (showing {len(statuses)} on this page)")
    print()

    for voice in statuses:
        print(f"  Speaker ID: {voice.get('SpeakerID', '')}")
        print(f"  State: {voice.get('State', '')}, Version: {voice.get('Version', '')}")
        if voice.get("Alias"):
            print(f"  Alias: {voice['Alias']}")
        if voice.get("AvailableTrainingTimes") is not None:
            print(f"  Remaining training times: {voice['AvailableTrainingTimes']}")
        if voice.get("ExpireTime"):
            print(f"  Expire time: {voice['ExpireTime']}")
        if voice.get("DemoAudio"):
            print(f"  Demo audio: {voice['DemoAudio']}")
        print()

    return statuses


async def order_voices(quantity: int = 1, times: int = 1) -> list[str]:
    """Order (purchase) voice clone resource packs. PAID operation."""
    _, _, app_id = get_mgmt_credentials()

    body = {
        "AppID": int(app_id),
        "ResourceID": "volc.megatts.voiceclone",
        "Code": "Model_storage",
        "Times": times,
        "Quantity": quantity,
    }

    print(f"Ordering {quantity} voice(s) x {times} month(s)...")
    result = await call_mgmt_api("OrderAccessResourcePacks", body)

    order_ids = result.get("OrderIDs") or []
    for order_id in order_ids:
        print(f"Order created: {order_id}")
    return order_ids


async def renew_voices(speaker_ids: list[str], times: int = 1) -> list[str]:
    """Renew voice instances. PAID operation."""
    get_mgmt_credentials()

    body = {
        "SpeakerIDs": speaker_ids,
        "Times": times,
    }

    print(f"Renewing {len(speaker_ids)} voice(s) x {times} month(s)...")
    result = await call_mgmt_api("RenewAccessResourcePacks", body)

    order_ids = result.get("OrderIDs") or []
    for order_id in order_ids:
        print(f"Order created: {order_id}")
    return order_ids


async def main():
    parser = argparse.ArgumentParser(
        description="Clone and manage voices using Volcengine Voice Clone 2.0"
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    # Train subcommand
    train_parser = subparsers.add_parser("train", help="Train a cloned voice from an audio sample")
    train_parser.add_argument(
        "audio_file",
        type=str,
        help="Path to the audio sample (WAV/MP3/OGG/M4A/AAC/PCM, <10MB)",
    )
    train_parser.add_argument(
        "-s", "--speaker-id",
        type=str,
        required=True,
        help="Purchased speaker ID (S_xxx) or a custom speaker ID with --custom",
    )
    train_parser.add_argument(
        "--custom",
        action="store_true",
        help="Treat the speaker ID as a custom (postpaid) speaker ID",
    )
    train_parser.add_argument(
        "-t", "--text",
        type=str,
        default=None,
        help="Reference transcript of the audio (training fails on large mismatch)",
    )
    train_parser.add_argument(
        "-l", "--language",
        type=str,
        default=None,
        choices=list(LANGUAGE_MAP.keys()),
        help="Audio language (default: cn)",
    )
    train_parser.add_argument(
        "--demo-text",
        type=str,
        default=None,
        help="Demo text for the preview audio (4-300 chars)",
    )
    train_parser.add_argument(
        "--denoise",
        action="store_true",
        help="Enable audio denoising (recommended for noisy samples)",
    )
    train_parser.add_argument(
        "--no-volume-normalization",
        action="store_true",
        help="Disable volume normalization (closer to the sample's volume)",
    )

    # Status subcommand
    status_parser = subparsers.add_parser("status", help="Query the training status of a voice")
    status_parser.add_argument("speaker_id", type=str, help="Speaker ID to query")
    status_parser.add_argument(
        "--custom",
        action="store_true",
        help="Treat the speaker ID as a custom (postpaid) speaker ID",
    )
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

    # Upgrade subcommand
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade a V1 cloned voice to V3")
    upgrade_parser.add_argument("speaker_id", type=str, help="Speaker ID to upgrade")
    upgrade_parser.add_argument(
        "--custom",
        action="store_true",
        help="Treat the speaker ID as a custom (postpaid) speaker ID",
    )

    # List subcommand (management API)
    list_parser = subparsers.add_parser("list", help="List purchased voices and their states")
    list_parser.add_argument(
        "--speaker-ids",
        type=str,
        nargs="+",
        default=None,
        help="Filter by specific speaker IDs",
    )
    list_parser.add_argument(
        "--state",
        type=str,
        default=None,
        choices=MGMT_STATES,
        help="Filter by voice state",
    )
    list_parser.add_argument(
        "-p", "--page",
        type=int,
        default=1,
        help="Page number, 1-based (default: 1)",
    )
    list_parser.add_argument(
        "-n", "--page-size",
        type=int,
        default=10,
        help="Number of items per page, 1-100 (default: 10)",
    )

    # Order subcommand (management API, PAID)
    order_parser = subparsers.add_parser("order", help="Purchase voice clone resource packs (PAID)")
    order_parser.add_argument(
        "--quantity",
        type=int,
        default=1,
        help="Number of voices to purchase (default: 1)",
    )
    order_parser.add_argument(
        "--times",
        type=int,
        default=1,
        help="Duration in months (default: 1)",
    )

    # Renew subcommand (management API, PAID)
    renew_parser = subparsers.add_parser("renew", help="Renew voice instances (PAID)")
    renew_parser.add_argument(
        "speaker_ids",
        type=str,
        nargs="+",
        help="Speaker IDs to renew",
    )
    renew_parser.add_argument(
        "--times",
        type=int,
        default=1,
        help="Duration in months (default: 1)",
    )

    args = parser.parse_args()

    try:
        if args.action == "train":
            data = await train_voice(
                audio_file=args.audio_file,
                speaker_id=args.speaker_id,
                custom=args.custom,
                text=args.text,
                language=args.language,
                demo_text=args.demo_text,
                denoise=args.denoise,
                no_volume_normalization=args.no_volume_normalization,
            )
            print()
            print_voice_status(data)
            if data.get("demo_audio"):
                print("Demo audio URL (valid for 1 hour): available")
                output_path = Path(f"{args.speaker_id}_demo.mp3")
                await download_demo_audio(data["demo_audio"], output_path)
        elif args.action == "status":
            data = await get_voice_status(args.speaker_id, custom=args.custom)
            print()
            print_voice_status(data)
            demo_url = data.get("demo_audio")
            if demo_url:
                if args.download_demo:
                    output_path = Path(args.output) if args.output else Path(f"{args.speaker_id}_demo.mp3")
                    await download_demo_audio(demo_url, output_path)
                else:
                    print(f"Demo audio URL (valid for 1 hour): {demo_url}")
        elif args.action == "upgrade":
            data = await upgrade_voice(args.speaker_id, custom=args.custom)
            print()
            print_voice_status(data)
        elif args.action == "list":
            await list_voices(
                speaker_ids=args.speaker_ids,
                state=args.state,
                page=args.page,
                page_size=args.page_size,
            )
        elif args.action == "order":
            await order_voices(quantity=args.quantity, times=args.times)
        elif args.action == "renew":
            await renew_voices(speaker_ids=args.speaker_ids, times=args.times)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
