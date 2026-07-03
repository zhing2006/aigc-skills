"""
Tripo Import - Upload your own 3D model to Tripo API

Imports a local model file (GLB/OBJ/FBX/STL) and prints the task ID, which
can then be used with tripo-rig.py, tripo-segment.py, tripo-convert.py, etc.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from tripo3d import TripoClient, TaskStatus


SUPPORTED_MODEL_FORMATS = [".glb", ".obj", ".fbx", ".stl"]


async def import_model(file: str) -> str:
    """
    Import a local 3D model file into Tripo.

    Args:
        file: Path to the model file (GLB/OBJ/FBX/STL)

    Returns:
        The import task ID (usable as input for downstream Tripo scripts)
    """
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        raise ValueError("TRIPO_API_KEY environment variable is not set")
    base_url = os.environ.get("TRIPO_API_BASE_URL")
    if base_url:
        print(f"Using custom Tripo API base URL: {base_url}")
        TripoClient.BASE_URL = base_url

    file_path = Path(file)
    if not file_path.is_file():
        raise FileNotFoundError(f"Model file not found: {file}")
    if file_path.suffix.lower() not in SUPPORTED_MODEL_FORMATS:
        raise ValueError(
            f"Unsupported model format: {file_path.suffix}. "
            f"Supported: {', '.join(SUPPORTED_MODEL_FORMATS)}"
        )

    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"Importing model: {file_path} ({size_mb:.1f} MB)")
    print("Uploading...")

    async with TripoClient(api_key=api_key) as client:
        task_id = await client.import_model(str(file_path))
        print(f"Import task submitted: {task_id}")

        task = await client.wait_for_task(task_id, verbose=True)

        if task.status != TaskStatus.SUCCESS:
            raise RuntimeError(f"Import failed with status: {task.status}")

        print("Model import completed!")
        print(f"Import task ID: {task_id}")
        print("Use it with:")
        print(f"  tripo-rig.py {task_id} --animations walk ...")
        print(f"  tripo-segment.py {task_id} ...")
        print(f"  tripo-convert.py {task_id} --format FBX ...")
        return task_id


async def main():
    parser = argparse.ArgumentParser(
        description="Upload your own 3D model to Tripo API for rigging, "
        "segmentation, conversion, etc."
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to a local 3D model file "
        f"({'/'.join(f[1:].upper() for f in SUPPORTED_MODEL_FORMATS)})",
    )

    args = parser.parse_args()

    ext = Path(args.file).suffix.lower()
    if ext not in SUPPORTED_MODEL_FORMATS:
        parser.error(
            f"unsupported model format: {ext or '(none)'} "
            f"(supported: {', '.join(SUPPORTED_MODEL_FORMATS)})"
        )

    try:
        await import_model(file=args.file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
