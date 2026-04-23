from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
EXPORTS_DIR = ROOT / "exports"
REFERENCES_DIR = ROOT / "04_references"
DATAPACK_DIR = ROOT / "MinecraftServer" / "world" / "datapacks" / "millbygard"
FUNCTIONS_DIR = DATAPACK_DIR / "data" / "millbygard" / "functions"

ORTHO_TIF = DATA_DIR / "orsa_stackmora_3_12_ortofoto.tif"
RAW_ORTHO_TIF = ROOT / "01_data_raw" / "ortofoto" / "orsa_stackmora_3_12_ortofoto_highres.tif"
PARCELS_JSON = EXPORTS_DIR / "millbygard_local_parcels.json"
MANIFEST_JSON = DATA_DIR / "minecraft_ortofoto_surface_manifest.json"
NEARZONE_MANIFEST_JSON = DATA_DIR / "minecraft_ortofoto_nearzone_500_manifest.json"
PREVIEW_PNG = REFERENCES_DIR / "orsa_stackmora_3_12_ortofoto_blocks_preview.png"
NEARZONE_PREVIEW_PNG = REFERENCES_DIR / "orsa_stackmora_3_12_ortofoto_nearzone_500_blocks_preview.png"

GROUND_Y = 64
MAX_FUNCTION_COMMANDS = 8000
NEARZONE_RADIUS_M = 250

# RGB references are intentionally conservative. Roof/building colors are hints until
# the official building footprints are available.
PALETTE: list[dict[str, Any]] = [
    {"name": "grass", "rgb": (82, 112, 62), "block": "minecraft:grass_block", "preview": (95, 145, 67)},
    {"name": "forest", "rgb": (46, 74, 38), "block": "minecraft:moss_block", "preview": (40, 96, 48)},
    {"name": "dark_forest", "rgb": (32, 50, 30), "block": "minecraft:spruce_leaves[persistent=true]", "preview": (28, 70, 34)},
    {"name": "field", "rgb": (145, 134, 80), "block": "minecraft:coarse_dirt", "preview": (143, 118, 72)},
    {"name": "dry_field", "rgb": (172, 165, 116), "block": "minecraft:rooted_dirt", "preview": (166, 140, 93)},
    {"name": "gravel", "rgb": (132, 128, 118), "block": "minecraft:gravel", "preview": (140, 140, 140)},
    {"name": "road_light", "rgb": (176, 172, 158), "block": "minecraft:smooth_stone", "preview": (178, 178, 170)},
    {"name": "road_dark", "rgb": (91, 91, 86), "block": "minecraft:gray_concrete", "preview": (83, 86, 88)},
    {"name": "red_roof", "rgb": (120, 54, 45), "block": "minecraft:red_terracotta", "preview": (150, 72, 62)},
    {"name": "dark_roof", "rgb": (63, 58, 54), "block": "minecraft:deepslate_tiles", "preview": (64, 64, 70)},
    {"name": "light_roof", "rgb": (178, 172, 160), "block": "minecraft:light_gray_concrete", "preview": (190, 190, 185)},
    {"name": "shadow", "rgb": (28, 31, 34), "block": "minecraft:podzol", "preview": (74, 55, 38)},
    {"name": "water", "rgb": (51, 80, 102), "block": "minecraft:blue_concrete", "preview": (54, 94, 144)},
]


def prefer_package_proj_data() -> None:
    for package, relative in (("rasterio", "proj_data"), ("pyproj", "proj_dir/share/proj")):
        spec = importlib.util.find_spec(package)
        if spec is None or spec.origin is None:
            continue
        candidate = Path(spec.origin).resolve().parent / relative
        if (candidate / "proj.db").exists():
            os.environ["PROJ_LIB"] = str(candidate)
            os.environ["PROJ_DATA"] = str(candidate)
            return


prefer_package_proj_data()

try:
    import rasterio
    from rasterio.coords import BoundingBox
    from rasterio.errors import NotGeoreferencedWarning
    from rasterio.transform import rowcol
    from rasterio.windows import from_bounds
    from pyproj import Transformer
except ImportError as error:
    print(f"Fel: saknar Python-bibliotek: {error.name}")
    print("Kor exempelvis: pip install rasterio pyproj numpy")
    sys.exit(1)


def ensure_datapack() -> None:
    FUNCTIONS_DIR.mkdir(parents=True, exist_ok=True)
    pack_mcmeta = DATAPACK_DIR / "pack.mcmeta"
    if not pack_mcmeta.exists():
        pack_mcmeta.write_text(
            json.dumps(
                {
                    "pack": {
                        "pack_format": 26,
                        "description": "Millbygard GIS-generated build layers",
                    }
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def clean_previous_functions() -> None:
    for pattern in ("ortofoto_surface*.mcfunction", "ortofoto_nearzone*.mcfunction"):
        for path in FUNCTIONS_DIR.glob(pattern):
            path.unlink()


def load_origin_3006() -> tuple[float, float, float, float]:
    data = json.loads(PARCELS_JSON.read_text(encoding="utf-8"))
    lon = float(data["coordinate_basis"]["origin_lon"])
    lat = float(data["coordinate_basis"]["origin_lat"])
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    east, north = transformer.transform(lon, lat)
    return lon, lat, east, north


def classify_rgb(rgb: np.ndarray) -> dict[str, Any]:
    r, g, b = [float(value) for value in rgb]
    brightness = (r + g + b) / 3.0
    saturation = max(r, g, b) - min(r, g, b)

    by_name = {item["name"]: item for item in PALETTE}

    # Most of this ortofoto is low-contrast vegetation with long shadows. Pure
    # nearest-RGB matching over-classifies it as gray roof/road material, so use
    # simple spectral relations first and leave RGB distance as the fallback.
    if b > g + 20 and b > r + 30 and brightness > 80:
        return by_name["water"]
    if r > g + 14 and r > b + 10 and brightness > 55:
        return by_name["red_roof"]
    if brightness > 148 and saturation < 32:
        return by_name["light_roof"]
    if brightness > 122 and saturation < 24:
        return by_name["road_light"]
    if brightness > 88 and saturation < 18 and g - r < 8:
        return by_name["gravel"]
    if brightness < 54:
        return by_name["dark_forest"] if g >= r else by_name["shadow"]
    if g >= r + 6 and g >= b - 7:
        if brightness < 76:
            return by_name["dark_forest"]
        if brightness < 104:
            return by_name["forest"]
        return by_name["grass"]
    if brightness < 88 and saturation < 20:
        return by_name["road_dark"]
    if r > g - 3 and g > b - 4 and brightness > 70:
        return by_name["field"]

    color = rgb.astype(np.int32)
    return min(PALETTE, key=lambda item: int(np.sum((color - np.array(item["rgb"], dtype=np.int32)) ** 2)))


def cell_mean_rgb(
    data: np.ndarray,
    alpha: np.ndarray | None,
    transform: Any,
    bounds: Any,
    east: float,
    north: float,
) -> np.ndarray | None:
    left = east
    right = east + 1.0
    bottom = north
    top = north + 1.0
    if right <= bounds.left or left >= bounds.right or top <= bounds.bottom or bottom >= bounds.top:
        return None

    left = max(left, bounds.left)
    right = min(right, bounds.right)
    bottom = max(bottom, bounds.bottom)
    top = min(top, bounds.top)

    row_top, col_left = rowcol(transform, left, top, op=math.floor)
    row_bottom, col_right = rowcol(transform, right, bottom, op=math.ceil)
    row_start = max(0, min(row_top, row_bottom))
    row_stop = min(data.shape[1], max(row_top, row_bottom) + 1)
    col_start = max(0, min(col_left, col_right))
    col_stop = min(data.shape[2], max(col_left, col_right) + 1)
    if row_start >= row_stop or col_start >= col_stop:
        return None

    pixels = data[:, row_start:row_stop, col_start:col_stop]
    flat_pixels = pixels.reshape(3, -1)
    valid = np.any(flat_pixels > 0, axis=0)
    if alpha is not None:
        flat_alpha = alpha[row_start:row_stop, col_start:col_stop].reshape(-1)
        valid &= flat_alpha > 0
    if not np.any(valid):
        return None
    return flat_pixels[:, valid].mean(axis=1)


def chunked(items: list[str], size: int):
    for offset in range(0, len(items), size):
        yield items[offset : offset + size]


def write_function(path: Path, commands: list[str]) -> None:
    path.write_text("\n".join(commands) + "\n", encoding="utf-8")


def write_preview(preview: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "PNG",
        "height": preview.shape[0],
        "width": preview.shape[1],
        "count": preview.shape[2],
        "dtype": "uint8",
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(path, "w", **profile) as dest:
            dest.write(np.moveaxis(preview, -1, 0))


def requested_bounds(
    src_bounds: Any,
    origin_east: float,
    origin_north: float,
    local_bounds: tuple[int, int, int, int] | None,
) -> tuple[int, int, int, int, Any]:
    if local_bounds is None:
        left = src_bounds.left
        right = src_bounds.right
        bottom = src_bounds.bottom
        top = src_bounds.top
        if left >= right or bottom >= top:
            raise ValueError("Requested ortofoto area is outside the source raster.")

        min_x = math.floor(left - origin_east)
        max_x = math.ceil(right - origin_east) - 1
        min_north = math.floor(bottom - origin_north)
        max_north = math.ceil(top - origin_north) - 1
        return min_x, max_x, min_north, max_north, BoundingBox(left, bottom, right, top)

    min_x, max_x, min_north, max_north = local_bounds
    width_cells = max_x - min_x + 1
    height_cells = max_north - min_north + 1

    source_min_x = math.ceil(src_bounds.left - origin_east)
    source_max_x = math.floor(src_bounds.right - origin_east) - 1
    source_min_north = math.ceil(src_bounds.bottom - origin_north)
    source_max_north = math.floor(src_bounds.top - origin_north) - 1
    if width_cells > source_max_x - source_min_x + 1 or height_cells > source_max_north - source_min_north + 1:
        raise ValueError("Requested ortofoto area is larger than the source raster.")

    if min_x < source_min_x:
        max_x += source_min_x - min_x
        min_x = source_min_x
    if max_x > source_max_x:
        min_x -= max_x - source_max_x
        max_x = source_max_x
    if min_north < source_min_north:
        max_north += source_min_north - min_north
        min_north = source_min_north
    if max_north > source_max_north:
        min_north -= max_north - source_max_north
        max_north = source_max_north

    left = origin_east + min_x
    right = origin_east + max_x + 1.0
    bottom = origin_north + min_north
    top = origin_north + max_north + 1.0
    return min_x, max_x, min_north, max_north, BoundingBox(left, bottom, right, top)


def generate_surface(
    source_tif: Path,
    master_function_name: str,
    manifest_json: Path,
    preview_png: Path,
    origin_lon: float,
    origin_lat: float,
    origin_east: float,
    origin_north: float,
    local_bounds: tuple[int, int, int, int] | None = None,
    notes_extra: list[str] | None = None,
) -> dict[str, Any]:
    with rasterio.open(source_tif) as src:
        if src.crs is None or src.crs.to_epsg() != 3006:
            raise ValueError(f"Ortofoto must be EPSG:3006, got {src.crs}")

        min_x, max_x, min_north, max_north, bounds = requested_bounds(
            src.bounds,
            origin_east,
            origin_north,
            local_bounds,
        )
        window = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, transform=src.transform)
        window = window.round_offsets().round_lengths()
        data = src.read([1, 2, 3], window=window)
        alpha = src.read(4, window=window) if src.count >= 4 else None
        transform = src.window_transform(window)
        width = max_x - min_x + 1
        height = max_north - min_north + 1

        commands_by_block: dict[str, list[str]] = {}
        counts: Counter[str] = Counter()
        preview = np.zeros((height, width, 4), dtype=np.uint8)

        for north_m in range(max_north, min_north - 1, -1):
            preview_row = max_north - north_m
            for x_m in range(min_x, max_x + 1):
                preview_col = x_m - min_x
                rgb = cell_mean_rgb(data, alpha, transform, bounds, origin_east + x_m, origin_north + north_m)
                if rgb is None:
                    continue
                item = classify_rgb(rgb)
                counts[item["name"]] += 1
                preview[preview_row, preview_col, :3] = np.array(item["preview"], dtype=np.uint8)
                preview[preview_row, preview_col, 3] = 255

                mc_x = x_m
                mc_z = -north_m
                command = f"setblock {mc_x} {GROUND_Y} {mc_z} {item['block']}"
                commands_by_block.setdefault(item["block"], []).append(command)

    generated_functions: list[str] = []
    master_commands = [
        "# Generated from Lantmateriet ortofoto.",
        f"# Source: {source_tif.relative_to(ROOT).as_posix()}",
        f"# Origin WGS84: lon {origin_lon:.9f}, lat {origin_lat:.9f}",
        f"# Minecraft mapping: x=east meters, z=-north meters, y={GROUND_Y}",
    ]

    for block_index, (block_name, commands) in enumerate(sorted(commands_by_block.items())):
        for chunk_index, chunk in enumerate(chunked(commands, MAX_FUNCTION_COMMANDS)):
            safe_name = (
                block_name.replace("minecraft:", "")
                .replace("[", "_")
                .replace("]", "")
                .replace("=", "_")
                .replace(",", "_")
            )
            function_name = f"{master_function_name}_{block_index:02d}_{safe_name}_{chunk_index:02d}"
            generated_functions.append(function_name)
            write_function(FUNCTIONS_DIR / f"{function_name}.mcfunction", ["# Generated ortofoto surface."] + chunk)
            master_commands.append(f"function millbygard:{function_name}")

    write_function(FUNCTIONS_DIR / f"{master_function_name}.mcfunction", master_commands)
    write_preview(preview, preview_png)

    notes = [
        f"Run /reload, then /function millbygard:{master_function_name} in Minecraft.",
        "This is a flat visual surface layer from ortofoto; terrain height and building volumes are separate steps.",
        "Water-colored cells use blue_concrete instead of real water to avoid fluid spread.",
    ]
    if notes_extra:
        notes.extend(notes_extra)

    manifest = {
        "function": f"millbygard:{master_function_name}",
        "source": str(source_tif.relative_to(ROOT)),
        "preview": str(preview_png.relative_to(ROOT)),
        "ground_y": GROUND_Y,
        "scale": "1 block = 1 meter",
        "origin": {
            "lon": origin_lon,
            "lat": origin_lat,
            "epsg3006_east": origin_east,
            "epsg3006_north": origin_north,
        },
        "minecraft_area": {
            "x": [min_x, max_x],
            "z": [-max_north, -min_north],
            "width_blocks": width,
            "depth_blocks": height,
            "total_blocks": int(sum(counts.values())),
        },
        "generated_functions": [master_function_name, *generated_functions],
        "palette_counts": dict(sorted(counts.items())),
        "notes": notes,
    }
    manifest_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    if not ORTHO_TIF.exists():
        print(f"Fel: saknar {ORTHO_TIF}")
        print("Kor forst: python fetch_lantmateriet_layers.py --layers ortofoto")
        return 1
    if not RAW_ORTHO_TIF.exists():
        print(f"Fel: saknar {RAW_ORTHO_TIF}")
        print("Kor forst: python fetch_lantmateriet_layers.py --layers ortofoto")
        return 1
    if not PARCELS_JSON.exists():
        print(f"Fel: saknar {PARCELS_JSON}")
        print("Kor forst: python Millbygard.py")
        return 1

    ensure_datapack()
    clean_previous_functions()
    origin_lon, origin_lat, origin_east, origin_north = load_origin_3006()

    surface_manifest = generate_surface(
        ORTHO_TIF,
        "ortofoto_surface",
        MANIFEST_JSON,
        PREVIEW_PNG,
        origin_lon,
        origin_lat,
        origin_east,
        origin_north,
    )
    nearzone_manifest = generate_surface(
        RAW_ORTHO_TIF,
        "ortofoto_nearzone_500",
        NEARZONE_MANIFEST_JSON,
        NEARZONE_PREVIEW_PNG,
        origin_lon,
        origin_lat,
        origin_east,
        origin_north,
        local_bounds=(-NEARZONE_RADIUS_M, NEARZONE_RADIUS_M - 1, -NEARZONE_RADIUS_M, NEARZONE_RADIUS_M - 1),
        notes_extra=[
            "This is the stable 500 m x 500 m 1:1 nearzone around Millbygard origin.",
            "Use this before attempting a full 2 km x 2 km 1:1 build.",
        ],
    )
    print(json.dumps({"surface": surface_manifest, "nearzone_500": nearzone_manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
