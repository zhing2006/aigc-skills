"""
Google Lyria 3 - Text/Image to Music Generation

Supported models: lyria-3-pro-preview (full songs), lyria-3-clip-preview (30s clips)
Supported output formats: MP3 (both models), WAV (Pro only)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image


SUPPORTED_MODELS = [
    "lyria-3-pro-preview",
    "lyria-3-clip-preview",
]
SUPPORTED_FORMATS = ["mp3", "wav"]
MAX_INPUT_IMAGES = 10
DEFAULT_MODEL = "lyria-3-pro-preview"
DEFAULT_FORMAT = "mp3"


async def generate_music(
    prompt: str,
    images: list[str] | None = None,
    model_id: str = DEFAULT_MODEL,
    output_format: str = DEFAULT_FORMAT,
    instrumental: bool = False,
    save_lyrics: bool = False,
    output_path: str | None = None,
) -> Path:
    """
    Generate music using Google Lyria 3 API.

    Args:
        prompt: Text description of the music to generate
        images: List of image file paths for image-to-music (max 10)
        model_id: Model to use for generation
        output_format: Output audio format (mp3 or wav; wav is Pro only)
        instrumental: Force instrumental (no vocals)
        save_lyrics: Save lyrics to a separate .lyrics.txt file
        output_path: Output file path (optional)

    Returns:
        Path to the generated audio file
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {SUPPORTED_MODELS}")

    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {output_format}. Supported: {SUPPORTED_FORMATS}")

    if model_id == "lyria-3-clip-preview" and output_format == "wav":
        raise ValueError(
            "WAV format is only supported with lyria-3-pro-preview. "
            "Use MP3 with lyria-3-clip-preview, or switch to the Pro model."
        )

    if images and len(images) > MAX_INPUT_IMAGES:
        raise ValueError(f"Too many input images: {len(images)}. Maximum: {MAX_INPUT_IMAGES}")

    use_vertex_ai = os.environ.get("USE_VERTEX_AI", "false").lower() == "true"
    if use_vertex_ai:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

        client = genai.Client(vertexai=True, project=project, location=location)
    else:
        api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_CLOUD_API_KEY environment variable is not set")

        client = genai.Client(api_key=api_key)

    # Build contents with prompt and optional images
    prompt_text = prompt
    if instrumental:
        prompt_text += " Instrumental only, no vocals."

    contents: list = [prompt_text]
    if images:
        for image_path in images:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            contents.append(Image.open(path))

    config = types.GenerateContentConfig(
        response_modalities=["AUDIO", "TEXT"],
    )

    # Determine output file
    ext = ".wav" if output_format == "wav" else ".mp3"
    output_file = Path(output_path) if output_path else Path(f"generated_music{ext}")

    # Print generation info
    print(f"Prompt: {prompt}")
    mode = "Image-to-Music" if images else "Text-to-Music"
    instrumental_str = ", instrumental" if instrumental else ""
    print(f"Generating music ({mode}, format: {output_format}{instrumental_str}, model: {model_id})...")

    response = await client.aio.models.generate_content(
        model=model_id,
        contents=contents,
        config=config,
    )

    lyrics_text = ""
    audio_saved = False

    if response.parts:
        for part in response.parts:
            if part.text is not None:
                lyrics_text += part.text
                print(part.text)
            elif part.inline_data is not None:
                output_file.write_bytes(part.inline_data.data)
                audio_saved = True

    if not audio_saved:
        raise RuntimeError("No audio data received from the API")

    if save_lyrics and lyrics_text:
        lyrics_file = output_file.with_suffix(".lyrics.txt")
        lyrics_file.write_text(lyrics_text, encoding="utf-8")
        print(f"Lyrics saved to: {lyrics_file}")

    print(f"Music saved to: {output_file}")

    return output_file


async def main():
    parser = argparse.ArgumentParser(
        description="Generate music using Google Lyria 3"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text description of the music to generate",
    )
    parser.add_argument(
        "-i", "--images",
        type=str,
        nargs="*",
        help=f"Input image file paths for image-to-music (max {MAX_INPUT_IMAGES})",
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
        default=DEFAULT_FORMAT,
        choices=SUPPORTED_FORMATS,
        dest="output_format",
        help=f"Output audio format (default: {DEFAULT_FORMAT}; wav is Pro only)",
    )
    parser.add_argument(
        "--instrumental",
        action="store_true",
        help="Force instrumental (no vocals)",
    )
    parser.add_argument(
        "--save-lyrics",
        action="store_true",
        help="Save lyrics to a separate .lyrics.txt file",
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
            images=args.images,
            model_id=args.model,
            output_format=args.output_format,
            instrumental=args.instrumental,
            save_lyrics=args.save_lyrics,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
