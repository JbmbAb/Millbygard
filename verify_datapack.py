from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "data" / "control_panel_manifest.json"
SERVER_PROPERTIES = ROOT / "MinecraftServer" / "server.properties"


FUNCTION_REF_RE = re.compile(r"(?:^|[\" :])/?function\s+([a-z0-9_.-]+:[a-z0-9_./-]+)")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def function_to_path(function_id: str, functions_dir: Path) -> Path:
    namespace, name = function_id.split(":", 1)
    if namespace != "millbygard":
        raise ValueError(f"Only millbygard namespace is supported here: {function_id}")
    return functions_dir / f"{name}.mcfunction"


def read_server_properties(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def collect_function_refs(functions_dir: Path) -> dict[Path, set[str]]:
    refs: dict[Path, set[str]] = {}
    for path in sorted(functions_dir.rglob("*.mcfunction")):
        text = path.read_text(encoding="utf-8")
        refs[path] = set(FUNCTION_REF_RE.findall(text))
    return refs


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not MANIFEST_PATH.exists():
        print(f"FAIL: missing manifest: {MANIFEST_PATH.relative_to(ROOT)}")
        return 1

    manifest = load_json(MANIFEST_PATH)
    functions_dir = ROOT / manifest["functions_dir"]
    control = manifest["control_panel"]
    buttons = control["buttons"]

    if not functions_dir.exists():
        errors.append(f"Missing functions dir: {functions_dir.relative_to(ROOT)}")

    if manifest.get("requires_command_blocks"):
        props = read_server_properties(SERVER_PROPERTIES)
        if props.get("enable-command-block") != "true":
            errors.append("server.properties must have enable-command-block=true for physical launch buttons.")

    button_ids = [button["id"] for button in buttons]
    if len(button_ids) != len(set(button_ids)):
        errors.append("Duplicate button id in control panel manifest.")

    command_block_positions = [tuple(button["command_block"]) for button in buttons]
    if len(command_block_positions) != len(set(command_block_positions)):
        errors.append("Duplicate command_block coordinates in control panel manifest.")

    physical_button_positions = [tuple(button["button"]) for button in buttons]
    if len(physical_button_positions) != len(set(physical_button_positions)):
        errors.append("Duplicate button coordinates in control panel manifest.")

    required_functions = {
        control["function"],
        control["tower_function"],
        control["operator_menu_function"],
        control["status_function"],
        control.get("manifest_function", "millbygard:manifest"),
        *(button["function"] for button in buttons),
    }

    for function_id in sorted(required_functions):
        path = function_to_path(function_id, functions_dir)
        if not path.exists():
            errors.append(f"Missing function file for {function_id}: {path.relative_to(ROOT)}")

    control_path = function_to_path(control["function"], functions_dir)
    if control_path.exists():
        control_text = control_path.read_text(encoding="utf-8")
        for button in buttons:
            function_id = button["function"]
            x, y, z = button["command_block"]
            expected_command = (
                f'setblock {x} {y} {z} minecraft:command_block'
                f'{{Command:"execute as @p[distance=..5] at @s run function {function_id}",auto:0b}}'
            )
            if expected_command not in control_text:
                errors.append(
                    f"Control panel does not wire button {button['id']} to {function_id} "
                    f"at {x} {y} {z}."
                )

            bx, by, bz = button["button"]
            expected_button = f"setblock {bx} {by} {bz} minecraft:crimson_pressure_plate"
            if expected_button not in control_text:
                errors.append(f"Control panel is missing physical pressure plate {button['id']} at {bx} {by} {bz}.")

            if button["label"] not in control_text:
                warnings.append(f"Button label {button['label']} is not visible in control_panel.mcfunction.")

    if functions_dir.exists():
        refs = collect_function_refs(functions_dir)
        for source_path, function_ids in refs.items():
            for function_id in sorted(function_ids):
                try:
                    target_path = function_to_path(function_id, functions_dir)
                except ValueError:
                    continue
                if not target_path.exists():
                    errors.append(
                        f"Broken function reference in {source_path.relative_to(ROOT)}: {function_id}"
                    )

    print("Millbygard datapack verification")
    print(f"Manifest: {MANIFEST_PATH.relative_to(ROOT)}")
    print(f"Buttons: {', '.join(button['label'] for button in buttons)}")
    print()

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if errors:
        print("FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: manifest, physical launch buttons, and function references look consistent.")
    print("Next in-game check: /reload, /function millbygard:tower, then test each red button once.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
