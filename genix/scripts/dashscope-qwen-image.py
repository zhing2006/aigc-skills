"""
DashScope Qwen Image 3.0 - Text/Image to Image Generation and Editing

Supported model: qwen-image-3.0-pro
Modes:
  Text-to-Image (T2I): prompt only
  Image-to-Image (I2I): prompt plus 1-3 reference images

The model uses DashScope's native synchronous multimodal generation API.
It is currently invite-only and must be enabled in Alibaba Cloud Model Studio
before use.
"""

import argparse
import asyncio
import base64
import io
import json
import os
import re
import sys
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv
from PIL import Image


DEFAULT_MODEL = "qwen-image-3.0-pro"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com"
ENDPOINT_PATH = "/api/v1/services/aigc/multimodal-generation/generation"

MAX_REFERENCE_IMAGES = 3
MAX_OUTPUT_IMAGES = 6
MAX_INPUT_FILE_SIZE = 10 * 1024 * 1024
MIN_OUTPUT_PIXELS = 512 * 512
MAX_OUTPUT_PIXELS = 2048 * 2048
MAX_SEED = 2147483647

IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
OUTPUT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def get_api_endpoint() -> str:
    """Resolve the native multimodal generation endpoint."""
    base = os.environ.get("DASHSCOPE_IMAGE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if "/compatible-mode/" in base:
        raise ValueError(
            "DASHSCOPE_IMAGE_BASE_URL must be a native DashScope host, not an "
            "OpenAI-compatible endpoint"
        )
    if base.endswith(ENDPOINT_PATH):
        return base
    if base.endswith("/api/v1"):
        return f"{base}{ENDPOINT_PATH.removeprefix('/api/v1')}"
    return f"{base}{ENDPOINT_PATH}"


def normalize_size(value: str) -> str:
    """Accept WxH or W*H and return the API's W*H format."""
    normalized = value.lower().replace("x", "*")
    if not re.fullmatch(r"\d+\*\d+", normalized):
        raise argparse.ArgumentTypeError("size must use '<width>x<height>' or '<width>*<height>'")

    width, height = (int(part) for part in normalized.split("*"))
    total_pixels = width * height
    if not (MIN_OUTPUT_PIXELS <= total_pixels <= MAX_OUTPUT_PIXELS):
        raise argparse.ArgumentTypeError(
            "size must contain between 512*512 and 2048*2048 total pixels"
        )
    return f"{width}*{height}"


def encode_image_base64(image_path: str) -> str:
    """Validate and encode a local reference image as a data URI."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type = IMAGE_MIME_TYPES.get(path.suffix.lower())
    if not mime_type:
        supported = ", ".join(sorted(IMAGE_MIME_TYPES))
        raise ValueError(f"Unsupported image format: {path.suffix or '(none)'}. Supported: {supported}")

    file_size = path.stat().st_size
    if file_size > MAX_INPUT_FILE_SIZE:
        raise ValueError(f"Image file exceeds the 10MB limit: {image_path}")

    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def resolve_image(image: str) -> str:
    """Return a public URL/data URI unchanged or encode a local file."""
    if image.startswith(("http://", "https://")):
        return image
    if image.startswith("data:image/"):
        return image
    if image.startswith("data:"):
        raise ValueError("Reference data URIs must contain an image MIME type")
    return encode_image_base64(image)


def resolve_output_path(output_path: str | None) -> Path:
    output = Path(output_path) if output_path else Path("generated_image.png")
    if not output.suffix:
        output = output.with_suffix(".png")
    if output.suffix.lower() not in OUTPUT_EXTENSIONS:
        supported = ", ".join(sorted(OUTPUT_EXTENSIONS))
        raise ValueError(f"Unsupported output format: {output.suffix}. Supported: {supported}")
    return output


def convert_image(data: bytes, output: Path) -> None:
    """Convert the API's PNG response when another output extension is requested."""
    extension = output.suffix.lower()
    target_format = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".webp": "WEBP",
    }[extension]
    with Image.open(io.BytesIO(data)) as image:
        if target_format == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.save(output, format=target_format)


async def save_image(data: bytes, output: Path) -> None:
    if output.suffix.lower() == ".png":
        async with aiofiles.open(output, "wb") as output_file:
            await output_file.write(data)
        return
    await asyncio.to_thread(convert_image, data, output)


def extract_image_urls(result: dict) -> list[str]:
    urls: list[str] = []
    choices = (result.get("output") or {}).get("choices") or []
    for choice in choices:
        content = ((choice.get("message") or {}).get("content")) or []
        for item in content:
            if isinstance(item, dict) and item.get("image"):
                urls.append(item["image"])
    return urls


async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    model: str = DEFAULT_MODEL,
    size: str | None = None,
    num_images: int = 1,
    prompt_extend: bool = True,
    negative_prompt: str | None = None,
    seed: int | None = None,
    watermark: bool = False,
    output_path: str | None = None,
) -> list[Path]:
    """Generate or edit images with DashScope Qwen Image 3.0."""
    if model != DEFAULT_MODEL:
        raise ValueError(f"Unsupported model: {model}. Supported: {DEFAULT_MODEL}")
    if not prompt.strip():
        raise ValueError("Prompt must not be empty")
    if images and len(images) > MAX_REFERENCE_IMAGES:
        raise ValueError(f"At most {MAX_REFERENCE_IMAGES} reference images are supported")
    if not (1 <= num_images <= MAX_OUTPUT_IMAGES):
        raise ValueError(f"num_images must be between 1 and {MAX_OUTPUT_IMAGES}")
    if seed is not None and not (0 <= seed <= MAX_SEED):
        raise ValueError(f"seed must be between 0 and {MAX_SEED}")

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable is not set")

    output = resolve_output_path(output_path)
    content = [{"image": resolve_image(image)} for image in (images or [])]
    content.append({"text": prompt})

    parameters: dict = {
        "prompt_extend": prompt_extend,
        "n": num_images,
        "watermark": watermark,
    }
    if size:
        parameters["size"] = normalize_size(size)
    if negative_prompt:
        parameters["negative_prompt"] = negative_prompt
    if seed is not None:
        parameters["seed"] = seed

    body = {
        "model": model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        },
        "parameters": parameters,
    }

    mode = "Image-to-Image / Edit" if images else "Text-to-Image"
    size_label = size or "auto"
    print(f"Prompt: {prompt}")
    print(
        f"Generating image ({mode}, size: {size_label}, count: {num_images}, "
        f"model: {model})..."
    )

    timeout = aiohttp.ClientTimeout(total=600)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            get_api_endpoint(),
            json=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        ) as response:
            response_text = await response.text()
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as error:
                raise Exception(
                    f"Image generation failed: HTTP {response.status}, non-JSON response"
                ) from error

        if response.status != 200 or result.get("code"):
            code = result.get("code", response.status)
            message = result.get("message", result)
            raise Exception(f"Image generation failed: [{code}] {message}")

        image_urls = extract_image_urls(result)
        if not image_urls:
            raise Exception(f"No image returned: {result}")

        saved_files: list[Path] = []
        for index, image_url in enumerate(image_urls, start=1):
            target = (
                output.with_name(f"{output.stem}_{index}{output.suffix}")
                if len(image_urls) > 1
                else output
            )
            async with session.get(image_url) as image_response:
                if image_response.status != 200:
                    raise Exception(
                        f"Failed to download image {index}: HTTP {image_response.status}"
                    )
                await save_image(await image_response.read(), target)
            print(f"Image saved to: {target}")
            saved_files.append(target)

    usage = result.get("usage") or {}
    if usage:
        print(
            f"Usage: {usage.get('image_count', len(saved_files))} image(s), "
            f"{usage.get('width', '-')}x{usage.get('height', '-')}"
        )
    return saved_files


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate and edit images using DashScope Qwen Image 3.0"
    )
    parser.add_argument("prompt", help="Text prompt or image editing instruction")
    parser.add_argument(
        "-i",
        "--images",
        nargs="+",
        help="Reference image paths, public URLs, or data URIs (1-3)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        choices=[DEFAULT_MODEL],
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=normalize_size,
        default=None,
        help="Output size as '<width>x<height>'; omitted for model-selected size",
    )
    parser.add_argument(
        "-n",
        "--num-images",
        type=int,
        choices=range(1, MAX_OUTPUT_IMAGES + 1),
        default=1,
        help=f"Number of output images, 1-{MAX_OUTPUT_IMAGES} (default: 1)",
    )
    parser.add_argument(
        "--no-prompt-extend",
        action="store_true",
        help="Disable automatic prompt rewriting",
    )
    parser.add_argument(
        "--negative-prompt",
        default=None,
        help="Describe content that should not appear",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=f"Random seed, 0-{MAX_SEED}",
    )
    parser.add_argument(
        "--watermark",
        action="store_true",
        help="Add the Qwen-Image watermark",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path; multiple images get _1, _2... suffixes",
    )
    args = parser.parse_args()

    if args.images and len(args.images) > MAX_REFERENCE_IMAGES:
        parser.error(f"--images accepts at most {MAX_REFERENCE_IMAGES} values")

    try:
        await generate_image(
            prompt=args.prompt,
            images=args.images,
            model=args.model,
            size=args.size,
            num_images=args.num_images,
            prompt_extend=not args.no_prompt_extend,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
            watermark=args.watermark,
            output_path=args.output,
        )
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
