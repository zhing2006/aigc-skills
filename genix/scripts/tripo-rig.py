"""
Tripo Rig - Auto-rig 3D models and apply preset animations using Tripo API

Pipeline: riggable pre-check -> rig (skeleton + skin weights) -> optional
animation retargeting (preset animations baked into the output file).
"""

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from tripo3d import TripoClient, TaskStatus
from tripo3d.models import Animation, RigSpec, RigType


SUPPORTED_RIG_TYPES = [
    "biped",
    "quadruped",
    "hexapod",
    "octopod",
    "avian",
    "serpentine",
    "aquatic",
    "others",
]
SUPPORTED_SPECS = ["tripo", "mixamo"]
SUPPORTED_RIG_VERSIONS = ["v1.0-20240301", "v2.0-20250506"]
SUPPORTED_FORMATS = ["glb", "fbx"]
SUPPORTED_ANIMATIONS = [
    "idle",
    "walk",
    "run",
    "dive",
    "climb",
    "jump",
    "slash",
    "shoot",
    "hurt",
    "fall",
    "turn",
    "quadruped:walk",
    "hexapod:walk",
    "octopod:walk",
    "serpentine:march",
    "aquatic:march",
]


async def rig_model(
    task_id: str,
    rig_type: str | None = None,
    spec: str = "tripo",
    model_version: str | None = None,
    out_format: str = "glb",
    animations: list[str] | None = None,
    rig_task_id: str | None = None,
    skip_check: bool = False,
    bake_animation: bool = True,
    export_with_geometry: bool = False,
    animate_in_place: bool = False,
    output_path: str | None = None,
) -> Path:
    """
    Rig a 3D model and optionally apply preset animations.

    Args:
        task_id: The task ID of the original model
        rig_type: Skeleton type (auto-detected by pre-check when omitted)
        spec: Rig specification, "tripo" or "mixamo"
        model_version: Rig model version (server default when omitted)
        out_format: Output format, "glb" or "fbx"
        animations: Preset animation names to retarget after rigging
        rig_task_id: Existing rig task ID (skip check + rig, retarget only)
        skip_check: Skip the riggable pre-check
        bake_animation: Bake the animation on retarget
        export_with_geometry: Export animation with geometry
        animate_in_place: Keep the animation in place (no root motion)
        output_path: Output file path (optional)

    Returns:
        Path to the rigged/animated model file
    """
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        raise ValueError("TRIPO_API_KEY environment variable is not set")
    base_url = os.environ.get("TRIPO_API_BASE_URL")
    if base_url:
        print(f"Using custom Tripo API base URL: {base_url}")
        TripoClient.BASE_URL = base_url

    async with TripoClient(api_key=api_key) as client:
        if rig_task_id:
            print(f"Reusing rig task: {rig_task_id}")
            final_task = None
        else:
            detected_rig_type = None
            if not skip_check:
                print(f"Checking if model is riggable: {task_id}")
                check_task_id = await client.check_riggable(task_id)
                check_task = await client.wait_for_task(check_task_id, verbose=True)
                if check_task.status != TaskStatus.SUCCESS:
                    raise RuntimeError(
                        f"Riggable check failed with status: {check_task.status}"
                    )
                if not check_task.output.riggable:
                    raise RuntimeError(
                        "Model is not riggable. Rigging works best on character-like "
                        "models (biped/quadruped etc.) in a neutral pose."
                    )
                # SDK returns rig_type as a raw string despite the enum annotation
                detected = check_task.output.rig_type
                detected_rig_type = getattr(detected, "value", detected)
                print(
                    "Model is riggable "
                    f"(detected rig type: {detected_rig_type or 'unknown'})"
                )

            effective_rig_type = rig_type or detected_rig_type or "biped"
            print(f"Rigging model (rig type: {effective_rig_type}, spec: {spec})...")
            # Use create_task directly so model_version is only sent when the
            # user asks for a specific one (v2.0 is not available on every
            # API endpoint; the server default is the safest choice)
            rig_task_data = {
                "type": "animate_rig",
                "original_model_task_id": task_id,
                "out_format": out_format,
                "rig_type": RigType(effective_rig_type).value,
                "spec": RigSpec(spec).value,
            }
            if model_version:
                rig_task_data["model_version"] = model_version
            rig_task_id = await client.create_task(rig_task_data)
            print(f"Rig task submitted: {rig_task_id}")

            rig_task = await client.wait_for_task(rig_task_id, verbose=True)
            if rig_task.status != TaskStatus.SUCCESS:
                raise RuntimeError(f"Rigging failed with status: {rig_task.status}")

            print("Model rigging completed!")
            print(f"Rig task ID: {rig_task_id}")
            print(
                "  (reuse it to apply more animations without re-rigging: "
                f"tripo-rig.py {task_id} --rig-task-id {rig_task_id} "
                "--animations <name> ...)"
            )
            final_task = rig_task

        if animations:
            anim_enums = [Animation(f"preset:{name}") for name in animations]
            anim_arg = anim_enums[0] if len(anim_enums) == 1 else anim_enums
            print(f"Retargeting animations: {', '.join(animations)}")
            retarget_task_id = await client.retarget_animation(
                original_model_task_id=rig_task_id,
                animation=anim_arg,
                out_format=out_format,
                bake_animation=bake_animation,
                export_with_geometry=export_with_geometry,
                animate_in_place=animate_in_place,
            )
            print(f"Retarget task submitted: {retarget_task_id}")

            final_task = await client.wait_for_task(retarget_task_id, verbose=True)
            if final_task.status != TaskStatus.SUCCESS:
                raise RuntimeError(
                    f"Animation retargeting failed with status: {final_task.status}"
                )

            print("Animation retargeting completed!")

        # Determine output directory
        if output_path:
            out_file = Path(output_path)
            download_dir = out_file.parent if out_file.parent != Path() else Path(".")
        else:
            download_dir = Path(".")

        download_dir.mkdir(parents=True, exist_ok=True)

        downloaded = await client.download_task_models(final_task, str(download_dir))

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
                base_name = "animated" if animations else "rigged"
                final_path = download_dir / f"{base_name}{ext}"

                counter = 1
                while final_path.exists():
                    final_path = download_dir / f"{base_name}_{counter}{ext}"
                    counter += 1

            if model_file != final_path:
                shutil.move(str(model_file), str(final_path))

            print(f"Model saved to: {final_path}")
            return final_path

        raise RuntimeError("No model file was downloaded")


async def main():
    parser = argparse.ArgumentParser(
        description="Auto-rig 3D models and apply preset animations using Tripo API"
    )
    parser.add_argument(
        "task_id",
        type=str,
        help="Task ID of the original model (from tripo-3d.py)",
    )
    parser.add_argument(
        "--rig-type",
        type=str,
        default=None,
        choices=SUPPORTED_RIG_TYPES,
        help="Skeleton type (default: auto-detected by the riggable pre-check)",
    )
    parser.add_argument(
        "--spec",
        type=str,
        default="tripo",
        choices=SUPPORTED_SPECS,
        help="Rig specification: tripo for preset animations, "
        "mixamo for Mixamo pipelines (default: tripo)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        choices=SUPPORTED_RIG_VERSIONS,
        help="Rig model version (default: server default; v2.0-20250506 may "
        "not be available on all endpoints)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="glb",
        choices=SUPPORTED_FORMATS,
        dest="out_format",
        help="Output format (default: glb)",
    )
    parser.add_argument(
        "--animations",
        type=str,
        nargs="+",
        default=None,
        choices=SUPPORTED_ANIMATIONS,
        help="Preset animations to apply after rigging",
    )
    parser.add_argument(
        "--rig-task-id",
        type=str,
        default=None,
        help="Existing rig task ID: skip rigging and only retarget animations "
        "(requires --animations)",
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="Skip the riggable pre-check",
    )
    parser.add_argument(
        "--no-bake",
        action="store_true",
        help="Do not bake the animation (retarget only)",
    )
    parser.add_argument(
        "--export-with-geometry",
        action="store_true",
        help="Export animation with geometry (retarget only)",
    )
    parser.add_argument(
        "--animate-in-place",
        action="store_true",
        help="Keep the animation in place, no root motion (retarget only)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path (default: rigged.glb, or animated.glb "
        "when --animations is given)",
    )

    args = parser.parse_args()

    if args.rig_task_id and not args.animations:
        parser.error("--rig-task-id requires --animations (retarget-only mode)")
    if args.rig_task_id and (args.rig_type or args.model or args.skip_check):
        parser.error(
            "--rig-task-id skips rigging; it cannot be combined with "
            "--rig-type, --model or --skip-check"
        )
    if not args.animations and (
        args.no_bake or args.export_with_geometry or args.animate_in_place
    ):
        parser.error(
            "--no-bake, --export-with-geometry and --animate-in-place "
            "only apply when --animations is given"
        )

    try:
        await rig_model(
            task_id=args.task_id,
            rig_type=args.rig_type,
            spec=args.spec,
            model_version=args.model,
            out_format=args.out_format,
            animations=args.animations,
            rig_task_id=args.rig_task_id,
            skip_check=args.skip_check,
            bake_animation=not args.no_bake,
            export_with_geometry=args.export_with_geometry,
            animate_in_place=args.animate_in_place,
            output_path=args.output,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    load_dotenv(dotenv_path=".genix.env", override=True)
    asyncio.run(main())
