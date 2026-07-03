"""
Tripo Segment - Segment 3D models into named parts using Tripo API

The output is a single GLB whose parts are named nodes in the scene graph.
Part names are extracted locally and printed for use with tripo-complete.py.
"""

import argparse
import asyncio
import json
import os
import shutil
import struct
import sys
from pathlib import Path

from dotenv import load_dotenv
from tripo3d import TripoClient, TaskStatus


SEGMENT_V2 = "v2.0-20260430"
SUPPORTED_SEGMENT_VERSIONS = [SEGMENT_V2, "v1.0-20250506"]
SUPPORTED_GRANULARITY = ["simple", "balanced", "detailed"]


def list_glb_part_names(glb_path: Path) -> list[str]:
    """Extract mesh node names from a GLB file's JSON chunk (stdlib only)."""
    with open(glb_path, "rb") as f:
        header = f.read(12)
        if len(header) < 12 or header[:4] != b"glTF":
            return []
        chunk_header = f.read(8)
        if len(chunk_header) < 8:
            return []
        chunk_length, chunk_type = struct.unpack("<I4s", chunk_header)
        if chunk_type != b"JSON":
            return []
        gltf = json.loads(f.read(chunk_length))

    names = [
        node["name"]
        for node in gltf.get("nodes", [])
        if "mesh" in node and node.get("name")
    ]
    if not names:
        names = [mesh["name"] for mesh in gltf.get("meshes", []) if mesh.get("name")]
    return names


async def probe_part_names(client: TripoClient, task_id: str, is_v2: bool) -> list[str]:
    """Best-effort: fetch raw task output and collect part-name-like lists."""
    try:
        if is_v2:
            data = await client._v3_get_task(task_id)
        else:
            data = (await client._impl._request("GET", f"/task/{task_id}"))["data"]
        output = data.get("output", {}) or {}
        names = []
        for key, value in output.items():
            if "part" in key.lower() and isinstance(value, list):
                names.extend(str(v) for v in value if isinstance(v, (str, int)))
        return names
    except Exception:
        return []


async def segment_model(
    task_id: str,
    model_version: str = SEGMENT_V2,
    granularity: str | None = None,
    ref_image: str | None = None,
    split_by_connectivity: bool = False,
    output_path: str | None = None,
) -> Path:
    """
    Segment a 3D model into named parts using Tripo API.

    Args:
        task_id: The task ID of the original model
        model_version: Segmentation model version
        granularity: Segmentation granularity (v2 only)
        ref_image: Reference image guiding segmentation (v2 only)
        split_by_connectivity: Also split by mesh connectivity (v2 only)
        output_path: Output file path (optional)

    Returns:
        Path to the segmented model file
    """
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        raise ValueError("TRIPO_API_KEY environment variable is not set")
    base_url = os.environ.get("TRIPO_API_BASE_URL")
    if base_url:
        print(f"Using custom Tripo API base URL: {base_url}")
        TripoClient.BASE_URL = base_url
    v3_base_url = os.environ.get("TRIPO_API_V3_BASE_URL")
    if not v3_base_url and base_url and "tripo3d.com" in base_url:
        # Mainland endpoint in use; the v3 channel has a .com counterpart too
        v3_base_url = "https://openapi.tripo3d.com"
    if v3_base_url:
        print(f"Using Tripo API v3 base URL: {v3_base_url}")

    if ref_image and not Path(ref_image).is_file():
        raise FileNotFoundError(f"Reference image not found: {ref_image}")

    is_v2 = model_version == SEGMENT_V2

    print(f"Original task: {task_id}")
    print(f"Segmentation model: {model_version}")
    if granularity:
        print(f"Granularity: {granularity}")
    print("Segmenting model...")

    async with TripoClient(api_key=api_key, v3_base_url=v3_base_url) as client:
        segment_kwargs = {
            "original_model_task_id": task_id,
            "model_version": model_version,
        }
        if granularity:
            segment_kwargs["segmentation_granularity"] = granularity
        if ref_image:
            segment_kwargs["ref_image"] = ref_image
        if split_by_connectivity:
            segment_kwargs["split_by_connectivity"] = True

        segment_task_id = await client.mesh_segmentation(**segment_kwargs)
        print(f"Segment task submitted: {segment_task_id}")

        task = await client.wait_for_task(segment_task_id, verbose=True, use_v3=is_v2)

        if task.status != TaskStatus.SUCCESS:
            raise RuntimeError(f"Segmentation failed with status: {task.status}")

        print("Model segmentation completed!")
        print(f"Segment task ID: {segment_task_id}")
        print("  (use it with tripo-complete.py to fill occluded part geometry)")

        # Determine output directory
        if output_path:
            out_file = Path(output_path)
            download_dir = out_file.parent if out_file.parent != Path() else Path(".")
        else:
            download_dir = Path(".")

        download_dir.mkdir(parents=True, exist_ok=True)

        downloaded = await client.download_task_models(task, str(download_dir))

        # Find the main model file
        model_file = None
        for model_type in ["model", "pbr_model", "base_model"]:
            if model_type in downloaded and downloaded[model_type]:
                file_path = downloaded[model_type]
                print(f"Downloaded {model_type}: {file_path}")
                if model_file is None:
                    model_file = Path(file_path)

        for model_type, file_path in downloaded.items():
            if model_type not in ["model", "pbr_model", "base_model"] and file_path:
                print(f"Downloaded {model_type}: {file_path}")

        if model_file:
            if output_path:
                final_path = Path(output_path)
            else:
                ext = model_file.suffix
                final_path = download_dir / f"segmented{ext}"

                counter = 1
                while final_path.exists():
                    final_path = download_dir / f"segmented_{counter}{ext}"
                    counter += 1

            if model_file != final_path:
                shutil.move(str(model_file), str(final_path))

            print(f"Model saved to: {final_path}")

            part_names = []
            if final_path.suffix.lower() == ".glb":
                try:
                    part_names = list_glb_part_names(final_path)
                except Exception:
                    part_names = []
            for name in await probe_part_names(client, segment_task_id, is_v2):
                if name not in part_names:
                    part_names.append(name)

            if part_names:
                print(f"Detected parts ({len(part_names)}): {', '.join(part_names)}")
                print(
                    "Use these names with: tripo-complete.py "
                    f"{segment_task_id} --parts <name> ..."
                )
            else:
                print(
                    "No part names detected locally; inspect the model's scene "
                    "nodes in a GLB viewer to get part names."
                )

            return final_path

        raise RuntimeError("No model file was downloaded")


async def main():
    parser = argparse.ArgumentParser(
        description="Segment 3D models into named parts using Tripo API"
    )
    parser.add_argument(
        "task_id",
        type=str,
        help="Task ID of the original model (from tripo-3d.py)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=SEGMENT_V2,
        choices=SUPPORTED_SEGMENT_VERSIONS,
        help=f"Segmentation model version (default: {SEGMENT_V2})",
    )
    parser.add_argument(
        "--granularity",
        type=str,
        default=None,
        choices=SUPPORTED_GRANULARITY,
        help="Segmentation granularity (v2 only)",
    )
    parser.add_argument(
        "--ref-image",
        type=str,
        default=None,
        help="Reference image guiding segmentation (v2 only)",
    )
    parser.add_argument(
        "--split-by-connectivity",
        action="store_true",
        help="Also split parts by mesh connectivity (v2 only)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: segmented.glb)",
    )

    args = parser.parse_args()

    if args.model != SEGMENT_V2 and (
        args.granularity or args.ref_image or args.split_by_connectivity
    ):
        parser.error(
            "--granularity, --ref-image and --split-by-connectivity are only "
            f"supported by segmentation model {SEGMENT_V2}"
        )

    try:
        await segment_model(
            task_id=args.task_id,
            model_version=args.model,
            granularity=args.granularity,
            ref_image=args.ref_image,
            split_by_connectivity=args.split_by_connectivity,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
