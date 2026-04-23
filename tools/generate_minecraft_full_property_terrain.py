from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import numpy as np
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as shapely_transform


def configure_proj_data() -> None:
    spec = find_spec("rasterio")
    if not spec or not spec.origin:
        return
    proj_data = Path(spec.origin).parent / "proj_data"
    if proj_data.exists():
        os.environ.setdefault("PROJ_DATA", str(proj_data))
        os.environ.setdefault("PROJ_LIB", str(proj_data))


configure_proj_data()

import rasterio


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPORTS = ROOT / "exports"
OUTPUT = ROOT / "output"
FUNCTIONS = (
    ROOT
    / "MinecraftServer"
    / "world"
    / "datapacks"
    / "millbygard"
    / "data"
    / "millbygard"
    / "functions"
)

MARKHOJD = DATA / "orsa_stackmora_3_12_markhojd.tif"
YTHOJD_AG = DATA / "orsa_stackmora_3_12_ythojd_above_ground.tif"
ORTHO = DATA / "orsa_stackmora_3_12_ortofoto.tif"
WORKAREA = DATA / "orsa_stackmora_3_12_workarea.geojson"
BUILDINGS = DATA / "orsa_stackmora_3_12_byggnader.geojson"
PARCELS = EXPORTS / "millbygard_local_parcels.json"
BUILDING_HEIGHTS = OUTPUT / "building_surface_heights_20260416.json"

MANIFEST = DATA / "minecraft_full_property_terrain_manifest.json"
MASTER_FUNCTION = FUNCTIONS / "full_property_complete.mcfunction"
TERRAIN_MASTER = FUNCTIONS / "full_property_terrain.mcfunction"
BUILDINGS_FUNCTION = FUNCTIONS / "full_property_buildings.mcfunction"
BOUNDARY_FUNCTION = FUNCTIONS / "full_property_boundary.mcfunction"

BASE_Y = 40
SURFACE_BASE_Y = 70
MAX_FUNCTION_COMMANDS = 1000

SURFACE_BLOCKS = {
    "grass": "minecraft:grass_block",
    "forest": "minecraft:moss_block",
    "dark_forest": "minecraft:podzol",
    "field": "minecraft:coarse_dirt",
    "dry_field": "minecraft:rooted_dirt",
    "gravel": "minecraft:gravel",
    "road_light": "minecraft:smooth_stone",
    "road_dark": "minecraft:gray_concrete",
    "red_roof": "minecraft:red_terracotta",
    "dark_roof": "minecraft:deepslate_tiles",
    "light_roof": "minecraft:light_gray_concrete",
    "shadow": "minecraft:podzol",
    "water": "minecraft:grass_block",
}

PALETTE: list[dict[str, Any]] = [
    {"name": "grass", "rgb": (82, 112, 62)},
    {"name": "forest", "rgb": (46, 74, 38)},
    {"name": "dark_forest", "rgb": (32, 50, 30)},
    {"name": "field", "rgb": (145, 134, 80)},
    {"name": "dry_field", "rgb": (172, 165, 116)},
    {"name": "gravel", "rgb": (132, 128, 118)},
    {"name": "road_light", "rgb": (176, 172, 158)},
    {"name": "road_dark", "rgb": (91, 91, 86)},
    {"name": "red_roof", "rgb": (120, 54, 45)},
    {"name": "dark_roof", "rgb": (63, 58, 54)},
    {"name": "light_roof", "rgb": (178, 172, 160)},
    {"name": "shadow", "rgb": (28, 31, 34)},
    {"name": "water", "rgb": (51, 80, 102)},
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_origin_3006() -> tuple[float, float]:
    basis = load_json(PARCELS)["coordinate_basis"]
    lon = float(basis["origin_lon"])
    lat = float(basis["origin_lat"])
    return Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True).transform(lon, lat)


def classify_rgb(rgb: np.ndarray) -> str:
    r, g, b = [float(value) for value in rgb]
    brightness = (r + g + b) / 3.0
    saturation = max(r, g, b) - min(r, g, b)
    if b > g + 20 and b > r + 30 and brightness > 80:
        return "water"
    if r > g + 14 and r > b + 10 and brightness > 55:
        return "red_roof"
    if brightness > 148 and saturation < 32:
        return "light_roof"
    if brightness > 122 and saturation < 24:
        return "road_light"
    if brightness > 88 and saturation < 18 and g - r < 8:
        return "gravel"
    if brightness < 54:
        return "dark_forest" if g >= r else "shadow"
    if g >= r + 6 and g >= b - 7:
        if brightness < 76:
            return "dark_forest"
        if brightness < 104:
            return "forest"
        return "grass"
    if brightness < 88 and saturation < 20:
        return "road_dark"
    if r > g - 3 and g > b - 4 and brightness > 70:
        return "field"
    color = rgb.astype(np.int32)
    return min(PALETTE, key=lambda item: int(np.sum((color - np.array(item["rgb"], dtype=np.int32)) ** 2)))["name"]


def sample_ortho_block(src, east: float, north: float) -> str:
    try:
        row, col = src.index(east + 0.5, north + 0.5)
    except Exception:
        return "minecraft:grass_block"
    if row < 0 or col < 0 or row >= src.height or col >= src.width:
        return "minecraft:grass_block"
    values = src.read([1, 2, 3], window=((row, row + 1), (col, col + 1))).reshape(3)
    kind = classify_rgb(values.astype(np.float32))
    return SURFACE_BLOCKS[kind]


def chunked(items: list[str], size: int):
    for offset in range(0, len(items), size):
        yield items[offset : offset + size]


def write_function(path: Path, commands: list[str]) -> None:
    path.write_text("\n".join(commands) + "\n", encoding="utf-8")


def minecraft_y(elevation_m: float, min_elevation_m: float) -> int:
    return SURFACE_BASE_Y + round(elevation_m - min_elevation_m)


def minecraft_xz(east: float, north: float, origin_east: float, origin_north: float) -> tuple[int, int]:
    return round(east - origin_east), -round(north - origin_north)


def bresenham(x0: int, z0: int, x1: int, z1: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dz = -abs(z1 - z0)
    sx = 1 if x0 < x1 else -1
    sz = 1 if z0 < z1 else -1
    err = dx + dz
    x, z = x0, z0
    while True:
        points.append((x, z))
        if x == x1 and z == z1:
            break
        e2 = 2 * err
        if e2 >= dz:
            err += dz
            x += sx
        if e2 <= dx:
            err += dx
            z += sz
    return points


def collect_terrain_cells() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    origin_east, origin_north = load_origin_3006()
    to_3006 = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    workarea = shapely_transform(to_3006.transform, shape(load_json(WORKAREA)["features"][0]["geometry"]))

    cells: list[dict[str, Any]] = []
    with rasterio.open(MARKHOJD) as dem:
        data = dem.read(1, masked=True)
        values: list[float] = []
        candidates: list[tuple[int, int, float, float, float]] = []
        for row in range(dem.height):
            for col in range(dem.width):
                if data.mask[row, col]:
                    continue
                east, north = dem.xy(row, col)
                point = Point(east, north)
                if not workarea.contains(point):
                    continue
                elevation = float(data[row, col])
                if not math.isfinite(elevation) or elevation < -1000:
                    continue
                candidates.append((row, col, east, north, elevation))
                values.append(elevation)

        min_elev = min(values)
        max_elev = max(values)

        with rasterio.open(ORTHO) as ortho:
            for row, col, east, north, elevation in candidates:
                x, z = minecraft_xz(east, north, origin_east, origin_north)
                y = minecraft_y(elevation, min_elev)
                cells.append(
                    {
                        "row": row,
                        "col": col,
                        "east": east,
                        "north": north,
                        "x": x,
                        "z": z,
                        "y": y,
                        "elevation_m": elevation,
                        "surface_block": sample_ortho_block(ortho, east, north),
                    }
                )

    metadata = {
        "origin_3006": {"east": origin_east, "north": origin_north},
        "cell_count": len(cells),
        "min_elevation_m": round(min_elev, 3),
        "max_elevation_m": round(max_elev, 3),
        "height_range_m": round(max_elev - min_elev, 3),
        "minecraft_y": {
            "base_fill_y": BASE_Y,
            "surface_base_y": SURFACE_BASE_Y,
            "min_surface_y": min(cell["y"] for cell in cells),
            "max_surface_y": max(cell["y"] for cell in cells),
            "vertical_scale": "1 block = 1 meter relative height",
        },
        "minecraft_area": {
            "min_x": min(cell["x"] for cell in cells),
            "max_x": max(cell["x"] for cell in cells),
            "min_z": min(cell["z"] for cell in cells),
            "max_z": max(cell["z"] for cell in cells),
        },
    }
    return cells, metadata


def write_terrain_functions(cells: list[dict[str, Any]]) -> list[str]:
    command_groups: dict[str, list[str]] = defaultdict(list)
    block_counts: Counter[str] = Counter()

    for cell in cells:
        x = cell["x"]
        y = cell["y"]
        z = cell["z"]
        surface_block = cell["surface_block"]
        block_counts[surface_block] += 1
        if y - 5 >= BASE_Y:
            command_groups["stone"].append(f"fill {x} {BASE_Y} {z} {x} {y - 5} {z} minecraft:stone")
        if y - 1 >= BASE_Y:
            dirt_start = max(BASE_Y, y - 4)
            command_groups["dirt"].append(f"fill {x} {dirt_start} {z} {x} {y - 1} {z} minecraft:dirt")
        command_groups[surface_block.replace("minecraft:", "").replace("[", "_").replace("]", "_").replace("=", "_")].append(
            f"setblock {x} {y} {z} {surface_block}"
        )

    function_names: list[str] = []
    for key in sorted(command_groups):
        commands = command_groups[key]
        for index, chunk in enumerate(chunked(commands, MAX_FUNCTION_COMMANDS)):
            name = f"full_property_terrain_{key}_{index:02d}"
            write_function(FUNCTIONS / f"{name}.mcfunction", ["# Generated full-property terrain chunk."] + chunk)
            function_names.append(name)

    write_function(
        TERRAIN_MASTER,
        [
            "# Safe alias for full property terrain generation.",
            "# Use the staged complete build so terrain chunks are not all run in one tick.",
            "function millbygard:full_property_complete",
        ],
    )
    return function_names, {str(k): int(v) for k, v in block_counts.items()}


def write_building_surface_function(cells: list[dict[str, Any]], terrain_meta: dict[str, Any]) -> dict[str, Any]:
    heights = load_json(BUILDING_HEIGHTS) if BUILDING_HEIGHTS.exists() else {"features": []}
    building_data = load_json(BUILDINGS)
    to_3006 = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    origin_east, origin_north = load_origin_3006()
    min_elev = float(terrain_meta["min_elevation_m"])

    commands: list[str] = ["# Building surface/height support from Lantmateriet building vector and ythojd above-ground stats."]
    feature_count = 0
    block_count = 0

    height_by_feature_part: dict[tuple[int, int], float] = {}
    for item in heights.get("features", []):
        key = (int(item["feature_index"]), int(item["part"]))
        height_by_feature_part[key] = float(item.get("height_p95_m") or item.get("height_p90_m") or 4.0)

    for feature_index, feature in enumerate(building_data.get("features", [])):
        geom = shapely_transform(to_3006.transform, shape(feature["geometry"]))
        polygons = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        for part_index, polygon in enumerate(polygons, start=1):
            if polygon.is_empty:
                continue
            roof_height = max(1.0, height_by_feature_part.get((feature_index, part_index), 4.0))
            minx, miny, maxx, maxy = polygon.bounds
            x_start = math.floor(minx - origin_east)
            x_end = math.ceil(maxx - origin_east)
            z_start = -math.ceil(maxy - origin_north)
            z_end = -math.floor(miny - origin_north)
            purpose = str(feature.get("properties", {}).get("objekttyp") or "")
            wall = "minecraft:red_terracotta" if "Bostad" in purpose else "minecraft:spruce_planks"
            roof = "minecraft:deepslate_tiles" if "Bostad" in purpose else "minecraft:dark_oak_planks"

            for x in range(x_start, x_end + 1):
                for z in range(z_start, z_end + 1):
                    east = origin_east + x
                    north = origin_north - z
                    point = Point(east, north)
                    if not polygon.contains(point):
                        continue
                    ground_elev = min((cell["elevation_m"] for cell in cells if cell["x"] == x and cell["z"] == z), default=min_elev)
                    ground_y = minecraft_y(ground_elev, min_elev)
                    roof_y = ground_y + round(roof_height)
                    if roof_y > ground_y:
                        commands.append(f"fill {x} {ground_y + 1} {z} {x} {roof_y - 1} {z} {wall}")
                    commands.append(f"setblock {x} {roof_y} {z} {roof}")
                    block_count += max(1, roof_y - ground_y)
            feature_count += 1

    write_function(
        BUILDINGS_FUNCTION,
        commands + ['tellraw @a [{"text":"Building footprints raised with ythojd roof-height support.","color":"gold"}]'],
    )
    return {"building_surface_features": feature_count, "building_surface_block_columns": block_count}


def write_boundary_function(cells: list[dict[str, Any]]) -> dict[str, Any]:
    origin_east, origin_north = load_origin_3006()
    to_3006 = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    workarea = shapely_transform(to_3006.transform, shape(load_json(WORKAREA)["features"][0]["geometry"]))
    ground_y = {(int(cell["x"]), int(cell["z"])): int(cell["y"]) for cell in cells}
    fallback_y = min(ground_y.values()) + 1

    boundary_cells: set[tuple[int, int]] = set()
    polygons = list(workarea.geoms) if workarea.geom_type == "MultiPolygon" else [workarea]
    for polygon in polygons:
        coords = list(polygon.exterior.coords)
        for start, end in zip(coords, coords[1:]):
            x0, z0 = minecraft_xz(float(start[0]), float(start[1]), origin_east, origin_north)
            x1, z1 = minecraft_xz(float(end[0]), float(end[1]), origin_east, origin_north)
            boundary_cells.update(bresenham(x0, z0, x1, z1))

    commands = ["# Lightweight red property boundary placed one block above generated terrain."]
    for x, z in sorted(boundary_cells):
        y = ground_y.get((x, z))
        if y is None:
            nearby = [
                ground_y[(x + dx, z + dz)]
                for radius in range(1, 4)
                for dx in range(-radius, radius + 1)
                for dz in range(-radius, radius + 1)
                if (x + dx, z + dz) in ground_y
            ]
            y = max(nearby) if nearby else fallback_y
        commands.append(f"setblock {x} {y + 1} {z} minecraft:red_concrete")

    write_function(
        BOUNDARY_FUNCTION,
        commands + ['tellraw @a [{"text":"Property boundary visible on generated terrain.","color":"red"}]'],
    )
    return {"boundary_surface_blocks": len(boundary_cells)}


def write_staged_master(function_names: list[str]) -> list[str]:
    stage_targets = [*function_names, "full_property_buildings", "full_property_boundary", "signs"]
    stage_names: list[str] = []
    for index, target in enumerate(stage_targets):
        stage_name = f"full_property_stage_{index:02d}"
        stage_names.append(stage_name)
        lines = [
            f"# Scheduled full-property build stage {index + 1}/{len(stage_targets)}.",
            f"function millbygard:{target}",
        ]
        if index + 1 < len(stage_targets):
            next_stage_name = f"full_property_stage_{index + 1:02d}"
            lines.append(f"schedule function millbygard:{next_stage_name} 20t replace")
            lines.append(
                f'tellraw @a [{{"text":"Full property build stage {index + 1}/{len(stage_targets)} klar. Nasta etapp om 1 sekund.","color":"gray"}}]'
            )
        else:
            lines.extend(
                [
                    "tp @a[tag=!millbygard_no_auto_tp,distance=..900] 0 115 -100 0 35",
                    'tellraw @a [{"text":"Full property build ready: all markhojd points used, ythojd building support applied, property boundary visible.","color":"gold"}]',
                ]
            )
        write_function(FUNCTIONS / f"{stage_name}.mcfunction", lines)

    lines = [
        "# Scheduled complete full-property build.",
        "# Uses all 1 m markhojd terrain cells, ythojd building support, property overlay and labels.",
        "schedule clear millbygard:full_property_stage_00",
        "schedule function millbygard:full_property_stage_00 1t replace",
        f'tellraw @a [{{"text":"Startar full fastighetsbyggnad i {len(stage_targets)} etapper. Lat servern arbeta klart innan ni gar in.","color":"gold"}}]',
    ]
    write_function(MASTER_FUNCTION, lines)
    return stage_names


def main() -> None:
    FUNCTIONS.mkdir(parents=True, exist_ok=True)
    for pattern in ("full_property_terrain_*.mcfunction", "full_property_stage_*.mcfunction"):
        for path in FUNCTIONS.glob(pattern):
            path.unlink()

    cells, metadata = collect_terrain_cells()
    function_names, block_counts = write_terrain_functions(cells)
    building_stats = write_building_surface_function(cells, metadata)
    boundary_stats = write_boundary_function(cells)
    stage_names = write_staged_master(function_names)

    metadata.update(
        {
            "source_markhojd": str(MARKHOJD.relative_to(ROOT)),
            "source_ythojd_above_ground": str(YTHOJD_AG.relative_to(ROOT)),
            "source_ortofoto": str(ORTHO.relative_to(ROOT)),
            "source_buildings": str(BUILDINGS.relative_to(ROOT)),
            "terrain_function": "millbygard:full_property_terrain",
            "building_function": "millbygard:full_property_buildings",
            "boundary_function": "millbygard:full_property_boundary",
            "complete_function": "millbygard:full_property_complete",
            "generated_function_count": len(function_names) + len(stage_names) + 4,
            "scheduled_stage_count": len(stage_names),
            "scheduled_stage_spacing": "20 ticks / about 1 second",
            "surface_block_counts": block_counts,
            **building_stats,
            **boundary_stats,
            "notes": [
                "All valid 1 m markhojd cells inside the property are used.",
                "Vertical terrain differences are preserved at 1 block per meter relative to min elevation.",
                "Ythojd is used selectively as building roof/surface height support, not as full 0.25 m terrain.",
                "No real water blocks are generated.",
            ],
        }
    )
    MANIFEST.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
