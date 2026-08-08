"""
Volcengine Seedream - Text/Image to Image Generation

Supported models: doubao-seedream-5-0-pro-260628 (default),
                  doubao-seedream-5-0-lite-260128,
                  doubao-seedream-4-5-251128,
                  doubao-seedream-4-0-250828
Supported sizes: resolution presets (1K/2K/3K/4K, model-dependent) or
                 explicit "<width>x<height>" pixel values
Sequential (group) generation: 5.0 lite / 4.5 / 4.0 only, up to 15 images
Web search tool: 5.0 lite only
"""

import argparse
import asyncio
import base64
import io
import mimetypes
import os
import re
import sys
from pathlib import Path

import aiofiles
import aiohttp
from dotenv import load_dotenv
from PIL import Image


DEFAULT_MODEL = "doubao-seedream-5-0-pro-260628"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# Per-model capabilities. Pixel ranges apply to explicit "<w>x<h>" sizes:
# total pixels (w*h) must fall inside [pixel_min, pixel_max] and the
# aspect ratio (w/h) inside [1/16, 16].
MODEL_CAPS = {
    "doubao-seedream-5-0-pro-260628": {
        "presets": ["1K", "2K"],
        "pixel_min": 921600,       # 1280x720
        "pixel_max": 4624220,      # 2048x2048x1.1025
        "max_ref_images": 10,
        "sequential": False,
        "web_search": False,
        "output_format": True,
        "fast_optimize": True,
    },
    "doubao-seedream-5-0-lite-260128": {
        "presets": ["2K", "3K", "4K"],
        "pixel_min": 3686400,      # 2560x1440
        "pixel_max": 16777216,     # 4096x4096
        "max_ref_images": 14,
        "sequential": True,
        "web_search": True,
        "output_format": True,
        "fast_optimize": False,
    },
    "doubao-seedream-4-5-251128": {
        "presets": ["2K", "4K"],
        "pixel_min": 3686400,      # 2560x1440
        "pixel_max": 16777216,     # 4096x4096
        "max_ref_images": 14,
        "sequential": True,
        "web_search": False,
        "output_format": False,
        "fast_optimize": False,
    },
    "doubao-seedream-4-0-250828": {
        "presets": ["1K", "2K", "4K"],
        "pixel_min": 921600,       # 1280x720
        "pixel_max": 16777216,     # 4096x4096
        "max_ref_images": 14,
        "sequential": True,
        "web_search": False,
        "output_format": False,
        "fast_optimize": True,
    },
}
SUPPORTED_MODELS = list(MODEL_CAPS.keys())
MAX_GROUP_IMAGES = 15


def encode_image_base64(image_path: str) -> str:
    """Encode a local image file to base64 data URI."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    fmt = mime_type.split("/")[1].lower()

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:image/{fmt};base64,{encoded}"


def resolve_image_url(path_or_url: str) -> str:
    """Resolve an image path or URL. Local files are base64-encoded."""
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    return encode_image_base64(path_or_url)


def validate_size(model: str, size: str) -> str:
    """Validate a size value (preset or WxH) against the model's limits."""
    caps = MODEL_CAPS[model]

    if re.fullmatch(r"\d+x\d+", size):
        width, height = (int(v) for v in size.split("x"))
        total = width * height
        if not (caps["pixel_min"] <= total <= caps["pixel_max"]):
            raise ValueError(
                f"Size {size} has {total} total pixels, outside the range "
                f"[{caps['pixel_min']}, {caps['pixel_max']}] for model {model}"
            )
        ratio = width / height
        if not (1 / 16 <= ratio <= 16):
            raise ValueError(f"Size {size} aspect ratio must be within [1/16, 16]")
        return size

    preset = size.upper()
    if preset in caps["presets"]:
        return preset

    raise ValueError(
        f"Unsupported size '{size}' for model {model}. "
        f"Use a preset ({caps['presets']}) or '<width>x<height>' pixel values"
    )


async def save_image_bytes(data: bytes, output_file: Path) -> None:
    """Save image bytes, converting format if it differs from the extension."""
    ext = output_file.suffix.lower().lstrip(".")
    ext_format = "jpeg" if ext in ("jpg", "jpeg") else ext

    image = Image.open(io.BytesIO(data))
    actual_format = (image.format or "").lower()

    if actual_format == ext_format:
        async with aiofiles.open(output_file, "wb") as f:
            await f.write(data)
    else:
        # Re-encode to match the requested extension (e.g. jpeg -> png)
        if ext_format == "jpeg" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(output_file)


async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    model: str = DEFAULT_MODEL,
    size: str = "2K",
    group: bool = False,
    max_images: int | None = None,
    optimize: str | None = None,
    web_search: bool = False,
    watermark: bool = False,
    output_path: str | None = None,
) -> list[Path]:
    """Generate image(s) using Volcengine Seedream."""
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Supported: {SUPPORTED_MODELS}")

    caps = MODEL_CAPS[model]
    size = validate_size(model, size)

    if images and len(images) > caps["max_ref_images"]:
        raise ValueError(
            f"Too many reference images: {len(images)}. "
            f"Model {model} supports at most {caps['max_ref_images']}"
        )

    if group and not caps["sequential"]:
        raise ValueError(f"Model {model} does not support group (sequential) generation")

    if group:
        ref_count = len(images) if images else 0
        limit = MAX_GROUP_IMAGES - ref_count
        if max_images is None:
            max_images = limit
        if not (1 <= max_images <= limit):
            raise ValueError(
                f"max_images must be within [1, {limit}] "
                f"(reference images + generated images <= {MAX_GROUP_IMAGES})"
            )

    if web_search and not caps["web_search"]:
        raise ValueError(f"Model {model} does not support web search (Seedream 5.0 lite only)")

    if optimize == "fast" and not caps["fast_optimize"]:
        raise ValueError(f"Model {model} does not support the 'fast' prompt optimize mode")

    api_key = os.environ.get("VOLCENGINE_API_KEY")
    if not api_key:
        raise ValueError("VOLCENGINE_API_KEY environment variable is not set")
    base_url = os.environ.get("VOLCENGINE_API_BASE", DEFAULT_BASE_URL)

    output_file = Path(output_path) if output_path else Path("generated_image.png")

    # Build request body
    body: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": watermark,
    }

    if images:
        resolved = [resolve_image_url(img) for img in images]
        body["image"] = resolved[0] if len(resolved) == 1 else resolved

    if caps["sequential"]:
        body["sequential_image_generation"] = "auto" if group else "disabled"
        if group:
            body["sequential_image_generation_options"] = {"max_images": max_images}

    if caps["output_format"]:
        ext = output_file.suffix.lower().lstrip(".")
        body["output_format"] = "jpeg" if ext in ("jpg", "jpeg") else "png"

    if web_search:
        body["tools"] = [{"type": "web_search"}]

    if optimize:
        body["optimize_prompt_options"] = {"mode": optimize}

    # Determine mode
    ref_count = len(images) if images else 0
    if group:
        mode = "Group Generation"
    elif ref_count > 1:
        mode = "Multi-Image-to-Image"
    elif ref_count == 1:
        mode = "Image-to-Image"
    else:
        mode = "Text-to-Image"

    print(f"Prompt: {prompt}")
    group_str = f", max {max_images} images" if group else ""
    print(f"Generating image ({mode}, {size}, model: {model}{group_str})...")

    timeout = aiohttp.ClientTimeout(total=1800)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{base_url}/images/generations",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
        ) as resp:
            result = await resp.json()

        if result.get("error"):
            error = result["error"]
            raise Exception(f"Image generation failed: [{error.get('code')}] {error.get('message')}")
        if resp.status != 200:
            raise Exception(f"Image generation failed: HTTP {resp.status} {result}")

        data = result.get("data") or []
        succeeded = [item for item in data if item.get("url")]
        if not succeeded:
            raise Exception(f"No image returned: {result}")

        saved_files: list[Path] = []
        for index, item in enumerate(data):
            if item.get("error"):
                error = item["error"]
                print(
                    f"Warning: image {index + 1} failed: "
                    f"[{error.get('code')}] {error.get('message')}",
                    file=sys.stderr,
                )
                continue

            if len(succeeded) > 1:
                target = output_file.with_name(
                    f"{output_file.stem}_{len(saved_files) + 1}{output_file.suffix}"
                )
            else:
                target = output_file

            async with session.get(item["url"]) as img_resp:
                if img_resp.status != 200:
                    raise Exception(f"Failed to download image: HTTP {img_resp.status}")
                await save_image_bytes(await img_resp.read(), target)

            size_info = f" ({item['size']})" if item.get("size") else ""
            print(f"Image saved to: {target}{size_info}")
            print(f"Image URL (expires in 24h): {item['url']}")
            saved_files.append(target)

    usage = result.get("usage") or {}
    if usage:
        print(
            f"Usage: {usage.get('generated_images', len(saved_files))} image(s), "
            f"{usage.get('total_tokens', '-')} tokens"
        )

    return saved_files


async def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Volcengine Seedream"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text prompt for image generation",
    )
    parser.add_argument(
        "-i", "--images",
        type=str,
        nargs="*",
        help="Reference image file paths or URLs (max 10 for 5.0 pro, 14 for others)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=SUPPORTED_MODELS,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-s", "--size",
        type=str,
        default="2K",
        help="Resolution preset (1K/2K/3K/4K, model-dependent) or "
             "'<width>x<height>' pixels (default: 2K)",
    )
    parser.add_argument(
        "-g", "--group",
        action="store_true",
        help="Enable group generation - a set of related images (not for 5.0 pro)",
    )
    parser.add_argument(
        "-n", "--max-images",
        type=int,
        default=None,
        help="Max images for group generation, 1-15 (implies --group)",
    )
    parser.add_argument(
        "--optimize",
        type=str,
        default=None,
        choices=["standard", "fast"],
        help="Prompt optimization mode (fast: 5.0 pro / 4.0 only)",
    )
    parser.add_argument(
        "--web-search",
        action="store_true",
        help="Enable web search tool (5.0 lite only)",
    )
    parser.add_argument(
        "--watermark",
        action="store_true",
        help="Add 'AI generated' watermark",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path; group images get _1, _2... suffixes "
             "(default: generated_image.png)",
    )

    args = parser.parse_args()

    try:
        await generate_image(
            prompt=args.prompt,
            images=args.images,
            model=args.model,
            size=args.size,
            group=args.group or args.max_images is not None,
            max_images=args.max_images,
            optimize=args.optimize,
            web_search=args.web_search,
            watermark=args.watermark,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
