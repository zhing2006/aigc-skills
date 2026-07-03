"""
Tripo Complete - Fill occluded geometry of segmented model parts using Tripo API

Takes the task ID of a segmented model (from tripo-segment.py) and completes
hidden/occluded geometry so each part becomes an independent closed mesh.
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


SUPPORTED_COMPLETION_VERSIONS = ["v1.0-20250506"]


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


async def complete_model(
    task_id: str,
    parts: list[str] | None = None,
    model_version: str = "v1.0-20250506",
    output_path: str | None = None,
) -> Path:
    """
    Complete occluded geometry of a segmented model using Tripo API.

    Args:
        task_id: The task ID of the segmented model (from tripo-segment.py)
        parts: Part names to complete (all parts when omitted)
        model_version: Completion model version
        output_path: Output file path (optional)

    Returns:
        Path to the completed model file
    """
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        raise ValueError("TRIPO_API_KEY environment variable is not set")
    base_url = os.environ.get("TRIPO_API_BASE_URL")
    if base_url:
        print(f"Using custom Tripo API base URL: {base_url}")
        TripoClient.BASE_URL = base_url

    print(f"Segmented model task: {task_id}")
    if parts:
        print(f"Parts to complete: {', '.join(parts)}")
    else:
        print("Parts to complete: all")
    print("Completing model...")

    async with TripoClient(api_key=api_key) as client:
        complete_kwargs = {
            "original_model_task_id": task_id,
            "model_version": model_version,
        }
        if parts:
            complete_kwargs["part_names"] = parts

        complete_task_id = await client.mesh_completion(**complete_kwargs)
        print(f"Completion task submitted: {complete_task_id}")

        task = await client.wait_for_task(complete_task_id, verbose=True)

        if task.status != TaskStatus.SUCCESS:
            raise RuntimeError(f"Completion failed with status: {task.status}")

        print("Model completion completed!")

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
                final_path = download_dir / f"completed{ext}"

                counter = 1
                while final_path.exists():
                    final_path = download_dir / f"completed_{counter}{ext}"
                    counter += 1

            if model_file != final_path:
                shutil.move(str(model_file), str(final_path))

            print(f"Model saved to: {final_path}")

            if final_path.suffix.lower() == ".glb":
                try:
                    part_names = list_glb_part_names(final_path)
                except Exception:
                    part_names = []
                if part_names:
                    print(
                        f"Parts in result ({len(part_names)}): "
                        f"{', '.join(part_names)}"
                    )

            return final_path

        raise RuntimeError("No model file was downloaded")


async def main():
    parser = argparse.ArgumentParser(
        description="Fill occluded geometry of segmented model parts using Tripo API"
    )
    parser.add_argument(
        "task_id",
        type=str,
        help="Task ID of the segmented model (from tripo-segment.py)",
    )
    parser.add_argument(
        "--parts",
        type=str,
        nargs="+",
        default=None,
        help="Part names to complete (from tripo-segment.py output; "
        "default: all parts)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="v1.0-20250506",
        choices=SUPPORTED_COMPLETION_VERSIONS,
        help="Completion model version (default: v1.0-20250506)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: completed.glb)",
    )

    args = parser.parse_args()

    try:
        await complete_model(
            task_id=args.task_id,
            parts=args.parts,
            model_version=args.model,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
