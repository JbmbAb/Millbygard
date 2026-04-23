from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


TASKS: dict[str, list[list[str]]] = {
    "status": [
        [sys.executable, "check_inputs.py"],
        [sys.executable, "check_tif.py"],
    ],
    "ortofoto": [
        [sys.executable, "fetch_lantmateriet_layers.py", "--layers", "ortofoto"],
        [sys.executable, "clip_data.py"],
        [sys.executable, "generate_minecraft_ortofoto_surface.py"],
    ],
    "heightmap": [
        [sys.executable, "export_heightmap.py"],
    ],
    "datapack": [
        [sys.executable, "generate_minecraft_ortofoto_surface.py"],
        [sys.executable, "generate_minecraft_topografi_map.py"],
        [sys.executable, "generate_signs.py"],
    ],
    "verify": [
        [
            sys.executable,
            "-m",
            "py_compile",
            "fetch_lantmateriet_layers.py",
            "clip_data.py",
            "check_inputs.py",
            "check_tif.py",
            "generate_minecraft_ortofoto_surface.py",
            "generate_minecraft_topografi_map.py",
            "generate_signs.py",
            "export_heightmap.py",
            "verify_datapack.py",
        ],
        [sys.executable, "check_inputs.py"],
        [sys.executable, "check_tif.py"],
        [sys.executable, "verify_datapack.py"],
    ],
}


def run_command(command: list[str]) -> int:
    print("\n> " + " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        print(f"\nStoppade efter felkod {result.returncode}: {' '.join(command)}")
    return result.returncode


def run_task(name: str) -> int:
    for command in TASKS[name]:
        code = run_command(command)
        if code != 0:
            return code
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Millbygard local launcher for GIS and Minecraft datapack steps.")
    parser.add_argument(
        "task",
        choices=sorted(TASKS),
        help="Task to run. Recommended day-to-day: status, ortofoto, datapack, verify.",
    )
    args = parser.parse_args()
    return run_task(args.task)


if __name__ == "__main__":
    raise SystemExit(main())
