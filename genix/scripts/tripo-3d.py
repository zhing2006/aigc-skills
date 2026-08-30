"""
Tripo 3D - Text/Image/Multi-view to 3D Model Generation

Supported modes: text-to-3d, image-to-3d, multiview-to-3d
Supported versions: P1-20260311, Turbo-v1.0-20250506, v1.4-20240625, v2.0-20240919, v2.5-20250123, v3.0-20250812, v3.1-20260211
Supported output formats: GLTF, USDZ, FBX, OBJ, STL, 3MF
"""

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from tripo3d import TripoClient, TaskStatus


SUPPORTED_VERSIONS = [
    "P1-20260311",
    "Turbo-v1.0-20250506",
    "v1.4-20240625",
    "v2.0-20240919",
    "v2.5-20250123",
    "v3.0-20250812",
    "v3.1-20260211",
]
SUPPORTED_MULTIVIEW_VERSIONS = [
    "P1-20260311",
    "v2.0-20240919",
    "v2.5-20250123",
    "v3.0-20250812",
    "v3.1-20260211",
]
SUPPORTED_FORMATS = ["GLTF", "USDZ", "FBX", "OBJ", "STL", "3MF"]
SUPPORTED_TEXTURE_QUALITY = ["standard", "detailed"]
SUPPORTED_GEOMETRY_QUALITY = ["standard", "detailed"]
DEFAULT_NEGATIVE_PROMPT = "low quality, blurry, deformed, extra limbs, multiple heads"
MULTIVIEW_ORDER = ("front", "left", "back", "right")
MISSING_MULTIVIEW_SLOT = "-"


def parse_multiview_slot(value: str) -> str | None:
    """Convert the CLI placeholder for an omitted multiview image to None."""
    return None if value == MISSING_MULTIVIEW_SLOT else value


def validate_multiview_images(
    images: list[str | None],
) -> list[str | None]:
    """Validate and normalize Tripo's fixed [front, left, back, right] slots."""
    if len(images) != len(MULTIVIEW_ORDER):
        raise ValueError(
            "Multiview mode requires exactly 4 image slots in the order "
            "front, left, back, right; use '-' for an omitted non-front view"
        )

    normalized = [image if image else None for image in images]
    if normalized[0] is None:
        raise ValueError("The front image is required for multiview mode")
    if sum(image is not None for image in normalized) < 2:
        raise ValueError("Multiview mode requires at least 2 images")

    return normalized


async def build_multiview_files(
    client: Any,
    images: list[str | None],
) -> list[dict[str, Any]]:
    """Serialize four validated multiview slots without shifting omitted views."""
    return [
        await client._image_to_file_content(image) if image is not None else {}
        for image in images
    ]


async def generate_3d_model(
    prompt: str | None = None,
    image: str | None = None,
    images: list[str | None] | None = None,
    negative_prompt: str | None = None,
    model_version: str = "v3.1-20260211",
    texture_quality: str = "standard",
    geometry_quality: str = "standard",
    face_limit: int | None = None,
    texture: bool = True,
    pbr: bool = True,
    smart_low_poly: bool = False,
    enable_image_autofix: bool = False,
    export_uv: bool = True,
    output_format: str | None = None,
    output_path: str | None = None,
) -> Path:
    """
    Generate 3D model using Tripo API.

    Args:
        prompt: Text prompt for text-to-3d generation
        image: Single image path for image-to-3d generation
        images: Exactly four multiview slots in the order front (0°), left (90°),
            back (180°), right (270°). Use None for an omitted non-front view. At
            least two slots must contain images. "left"/"right" are the character's
            own sides, not the viewer's: in the left image the face points to the
            image's left edge, in the right image it points to the right edge
        negative_prompt: Negative prompt (text-to-3d only)
        model_version: Model version to use
        texture_quality: Texture quality (standard/detailed)
        geometry_quality: Geometry quality (standard/detailed)
        face_limit: Maximum number of faces
        texture: Generate texture
        pbr: Generate PBR material
        smart_low_poly: Generate low-poly meshes with hand-crafted topology
        enable_image_autofix: Optimize input image for better results (image mode only)
        export_uv: Whether to perform UV unwrapping during generation
        output_format: Output format for conversion (GLTF/USDZ/FBX/OBJ/STL/3MF)
        output_path: Output file path (optional)

    Returns:
        Path to the generated model file
    """
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        raise ValueError("TRIPO_API_KEY environment variable is not set")
    base_url = os.environ.get("TRIPO_API_BASE_URL")
    if base_url:
        print(f"Using custom Tripo API base URL: {base_url}")
        TripoClient.BASE_URL = base_url

    is_p1 = model_version == "P1-20260311"

    # Determine mode
    if images is not None:
        mode = "multiview"
        if model_version not in SUPPORTED_MULTIVIEW_VERSIONS:
            raise ValueError(
                f"Unsupported version for multiview: {model_version}. "
                f"Supported: {SUPPORTED_MULTIVIEW_VERSIONS}"
            )
        images = validate_multiview_images(images)
    elif image:
        mode = "image"
    elif prompt:
        mode = "text"
    else:
        raise ValueError("Must provide prompt, image, or images")

    if model_version not in SUPPORTED_VERSIONS:
        raise ValueError(
            f"Unsupported version: {model_version}. Supported: {SUPPORTED_VERSIONS}"
        )

    # P1 model parameter validation
    if is_p1:
        if smart_low_poly:
            raise ValueError("P1 model does not support --smart-low-poly (it is inherently optimized for low-poly)")
        if geometry_quality != "standard":
            raise ValueError("P1 model does not support --geometry-quality (quality is pre-optimized)")
        if face_limit is not None and not (48 <= face_limit <= 20000):
            raise ValueError("P1 model face_limit must be between 48 and 20000")

    if texture_quality not in SUPPORTED_TEXTURE_QUALITY:
        raise ValueError(
            f"Unsupported texture quality: {texture_quality}. "
            f"Supported: {SUPPORTED_TEXTURE_QUALITY}"
        )

    if not is_p1 and geometry_quality not in SUPPORTED_GEOMETRY_QUALITY:
        raise ValueError(
            f"Unsupported geometry quality: {geometry_quality}. "
            f"Supported: {SUPPORTED_GEOMETRY_QUALITY}"
        )

    if output_format and output_format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {output_format}. Supported: {SUPPORTED_FORMATS}"
        )

    # Validate input files
    if image:
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image}")

    if images is not None:
        for img in images:
            if img is None:
                continue
            img_path = Path(img)
            if not img_path.exists():
                raise FileNotFoundError(f"Image file not found: {img}")

    print(f"Mode: {mode}-to-3d")
    if prompt:
        print(f"Prompt: {prompt}")
    if negative_prompt:
        print(f"Negative prompt: {negative_prompt}")
    print(f"Model version: {model_version}")
    if is_p1:
        print(f"P1 low-poly mode (face_limit: {face_limit or 'auto'})")
    elif smart_low_poly:
        print(f"Smart low-poly: enabled (face_limit: {face_limit or 'auto'})")
    print(f"Texture quality: {texture_quality}", end="")
    if not is_p1:
        print(f", Geometry quality: {geometry_quality}")
    else:
        print()
    print("Generating 3D model...")

    async with TripoClient(api_key=api_key) as client:
        # Build task data - use create_task directly for full parameter control
        # (SDK methods don't support P1 model or enable_image_autofix/export_uv params)

        # --- Mode-specific base data ---
        if mode == "text":
            task_data = {"type": "text_to_model", "prompt": prompt}
            if negative_prompt:
                task_data["negative_prompt"] = negative_prompt
        elif mode == "image":
            task_data = {
                "type": "image_to_model",
                "file": await client._image_to_file_content(image),
            }
            if enable_image_autofix:
                task_data["enable_image_autofix"] = True
        else:  # multiview
            file_tokens = await build_multiview_files(client, images)
            task_data = {"type": "multiview_to_model", "files": file_tokens}

        # --- Common params (all models) ---
        task_data["model_version"] = model_version
        task_data["texture_quality"] = texture_quality
        task_data["texture"] = texture
        task_data["pbr"] = pbr
        if face_limit is not None:
            task_data["face_limit"] = face_limit
        if not export_uv:
            task_data["export_uv"] = False

        # --- Standard model params (not applicable to P1) ---
        if not is_p1:
            task_data["geometry_quality"] = geometry_quality
            if smart_low_poly:
                task_data["smart_low_poly"] = True

        task_id = await client.create_task(task_data)

        print(f"Task submitted: {task_id}")

        # Wait for task completion
        task = await client.wait_for_task(task_id, verbose=True)

        if task.status != TaskStatus.SUCCESS:
            raise RuntimeError(f"Task failed with status: {task.status}")

        print("Model generation completed!")

        # Determine output directory for downloading
        # If output_path has no extension or is an existing directory, treat as directory
        if output_path:
            out_file = Path(output_path)
            if out_file.is_dir() or not out_file.suffix:
                download_dir = out_file
                output_path = None  # will generate filename automatically
            else:
                download_dir = out_file.parent if out_file.parent != Path() else Path(".")
        else:
            download_dir = Path(".")

        download_dir.mkdir(parents=True, exist_ok=True)

        # Convert format if requested
        if output_format:
            print(f"Converting to {output_format} format...")
            convert_task_id = await client.convert_model(
                original_model_task_id=task_id,
                format=output_format,
            )
            convert_task = await client.wait_for_task(convert_task_id, verbose=True)

            if convert_task.status != TaskStatus.SUCCESS:
                raise RuntimeError(
                    f"Format conversion failed with status: {convert_task.status}"
                )

            # Download converted model
            downloaded = await client.download_task_models(convert_task, str(download_dir))
        else:
            # Download original model
            downloaded = await client.download_task_models(task, str(download_dir))

        # Find the main model file (prefer: model > pbr_model > base_model)
        model_file = None
        for model_type in ["model", "pbr_model", "base_model"]:
            if model_type in downloaded and downloaded[model_type]:
                file_path = downloaded[model_type]
                print(f"Downloaded {model_type}: {file_path}")
                if model_file is None:
                    model_file = Path(file_path)
            elif model_type in downloaded:
                pass  # Key exists but no file

        # Print any other downloaded files
        for model_type, file_path in downloaded.items():
            if model_type not in ["model", "pbr_model", "base_model"] and file_path:
                print(f"Downloaded {model_type}: {file_path}")

        if model_file:
            # Determine final output path
            if output_path:
                # User specified output path
                final_path = Path(output_path)
            else:
                # Generate default name based on mode
                if mode == "text":
                    base_name = "text_to_3d"
                elif mode == "image":
                    base_name = "image_to_3d"
                else:
                    base_name = "multiview_to_3d"

                ext = model_file.suffix
                final_path = download_dir / f"{base_name}{ext}"

                # Avoid overwriting
                counter = 1
                while final_path.exists():
                    final_path = download_dir / f"{base_name}_{counter}{ext}"
                    counter += 1

            # Move/rename to final path
            if model_file != final_path:
                shutil.move(str(model_file), str(final_path))

            print(f"Model saved to: {final_path}")
            return final_path

        raise RuntimeError("No model file was downloaded")


async def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D models using Tripo API"
    )
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        default=None,
        help="Text prompt for text-to-3d generation",
    )
    parser.add_argument(
        "-i", "--image",
        type=str,
        default=None,
        help="Single image path for image-to-3d generation",
    )
    parser.add_argument(
        "--images",
        type=parse_multiview_slot,
        nargs=4,
        default=None,
        metavar=("FRONT", "LEFT", "BACK", "RIGHT"),
        help=(
            "Exactly four multiview slots in order: front (0deg), left (90deg), "
            "back (180deg), right (270deg); use '-' for an omitted non-front view "
            "and provide at least two images. 'left'/'right' are the character's own "
            "sides, NOT the viewer's"
        ),
    )
    parser.add_argument(
        "--negative-prompt",
        type=str,
        default=None,
        help=f"Negative prompt (text-to-3d only, default: '{DEFAULT_NEGATIVE_PROMPT}')",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="v3.1-20260211",
        choices=SUPPORTED_VERSIONS,
        help="Model version (default: v3.1-20260211)",
    )
    parser.add_argument(
        "--texture-quality",
        type=str,
        default="standard",
        choices=SUPPORTED_TEXTURE_QUALITY,
        help="Texture quality (default: standard)",
    )
    parser.add_argument(
        "--geometry-quality",
        type=str,
        default="standard",
        choices=SUPPORTED_GEOMETRY_QUALITY,
        help="Geometry quality (default: standard)",
    )
    parser.add_argument(
        "--face-limit",
        type=int,
        default=None,
        help="Maximum number of faces",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        choices=SUPPORTED_FORMATS,
        dest="output_format",
        help="Output format for conversion (default: keep original GLB)",
    )
    parser.add_argument(
        "--smart-low-poly",
        action="store_true",
        help="Generate low-poly meshes with hand-crafted topology (face_limit should be 1000~20000)",
    )
    parser.add_argument(
        "--enable-image-autofix",
        action="store_true",
        help="Optimize input image for better generation results (image mode only)",
    )
    parser.add_argument(
        "--no-export-uv",
        action="store_true",
        help="Skip UV unwrapping during generation (faster, smaller model; UV handled during texturing)",
    )
    parser.add_argument(
        "--no-texture",
        action="store_true",
        help="Do not generate texture",
    )
    parser.add_argument(
        "--no-pbr",
        action="store_true",
        help="Do not generate PBR material",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: text_to_3d.glb / image_to_3d.glb / multiview_to_3d.glb)",
    )

    args = parser.parse_args()

    # Validate input
    if not args.prompt and not args.image and not args.images:
        parser.error("Must provide prompt, --image, or --images")

    if args.negative_prompt and not args.prompt:
        parser.error("--negative-prompt requires a prompt (text-to-3d mode)")

    # Apply default negative prompt only for text-to-3d mode
    negative_prompt = args.negative_prompt
    if args.prompt and negative_prompt is None:
        negative_prompt = DEFAULT_NEGATIVE_PROMPT

    try:
        await generate_3d_model(
            prompt=args.prompt,
            image=args.image,
            images=args.images,
            negative_prompt=negative_prompt,
            model_version=args.model,
            texture_quality=args.texture_quality,
            geometry_quality=args.geometry_quality,
            face_limit=args.face_limit,
            texture=not args.no_texture,
            pbr=not args.no_pbr,
            smart_low_poly=args.smart_low_poly,
            enable_image_autofix=args.enable_image_autofix,
            export_uv=not args.no_export_uv,
            output_format=args.output_format,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
