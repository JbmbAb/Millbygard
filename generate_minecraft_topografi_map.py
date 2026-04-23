from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon


ROOT = Path(__file__).resolve().parent
TOPO_DIR = ROOT / "data" / "topografi"
ROADS_GPKG = TOPO_DIR / "orsa_stackmora_3_12_topografi_vagar_2km_3006.gpkg"
LAND_GPKG = TOPO_DIR / "orsa_stackmora_3_12_topografi_mark_2km_3006.gpkg"
BUILDINGS_GPKG = TOPO_DIR / "orsa_stackmora_3_12_topografi_byggnadsverk_2km_3006.gpkg"
HYDRO_GPKG = TOPO_DIR / "orsa_stackmora_3_12_topografi_hydrografi_2km_3006.gpkg"
WORKAREA = ROOT / "data" / "orsa_stackmora_3_12_workarea.geojson"
MANIFEST = TOPO_DIR / "orsa_stackmora_3_12_topografi_context_2km_manifest.json"

FUNCTIONS_DIR = (
    ROOT
    / "MinecraftServer"
    / "world"
    / "datapacks"
    / "millbygard"
    / "data"
    / "millbygard"
    / "functions"
)

MAP_ORIGIN_X = 0
MAP_ORIGIN_Z = 320
MAP_Y = 90
SCALE_M_PER_BLOCK = 20.0
MAX_FUNCTION_COMMANDS = 8000


LAND_BLOCKS = {
    "Aker": "minecraft:yellow_terracotta",
    "Open": "minecraft:grass_block",
    "Forest": "minecraft:moss_block",
    "Wetland": "minecraft:mud",
    "Water": "minecraft:blue_concrete",
    "Built": "minecraft:bricks",
    "Industry": "minecraft:smooth_stone",
}

ROAD_BLOCKS = {
    "large": "minecraft:light_gray_concrete",
    "small": "minecraft:smooth_sandstone",
    "track": "minecraft:coarse_dirt",
    "path": "minecraft:dirt_path",
    "cycle": "minecraft:gray_concrete",
}


def ascii_kind(value: object) -> str:
    text = str(value or "").lower()
    if "aker" in text or "åker" in text:
        return "Aker"
    if "skog" in text:
        return "Forest"
    if "sankmark" in text:
        return "Wetland"
    if "sjo" in text or "sjö" in text or "vattendragsyta" in text:
        return "Water"
    if "industri" in text:
        return "Industry"
    if "bebyggelse" in text:
        return "Built"
    return "Open"


def road_kind(value: object) -> str:
    text = str(value or "").lower()
    if "gång" in text or "gang" in text or "stig" in text or "elljus" in text:
        return "path"
    if "cykel" in text:
        return "cycle"
    if "traktor" in text:
        return "track"
    if "landsväg" in text or "landsvag" in text or "huvudgata" in text:
        return "large"
    return "small"


def iter_lines(geometry):
    if geometry is None or geometry.is_empty:
        return
    if isinstance(geometry, LineString):
        yield geometry
    elif isinstance(geometry, MultiLineString):
        yield from geometry.geoms
    elif isinstance(geometry, Polygon):
        yield LineString(geometry.exterior.coords)
        for ring in geometry.interiors:
            yield LineString(ring.coords)
    elif isinstance(geometry, MultiPolygon):
        for polygon in geometry.geoms:
            yield LineString(polygon.exterior.coords)
            for ring in polygon.interiors:
                yield LineString(ring.coords)


def rasterize_line(line: LineString, center_x: float, center_y: float, step_m: float):
    coords = list(line.coords)
    for start, end in zip(coords, coords[1:]):
        x1, y1 = start[:2]
        x2, y2 = end[:2]
        distance = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(math.ceil(distance / step_m)))
        for index in range(steps + 1):
            ratio = index / steps
            x = x1 + (x2 - x1) * ratio
            y = y1 + (y2 - y1) * ratio
            rel_x = round((x - center_x) / SCALE_M_PER_BLOCK)
            rel_z = round((center_y - y) / SCALE_M_PER_BLOCK)
            yield rel_x, rel_z


def point_to_cell(point: Point, center_x: float, center_y: float) -> tuple[int, int]:
    rel_x = round((point.x - center_x) / SCALE_M_PER_BLOCK)
    rel_z = round((center_y - point.y) / SCALE_M_PER_BLOCK)
    return rel_x, rel_z


def rasterize_geometry(geometry, center_x: float, center_y: float, step_m: float) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    if geometry is None or geometry.is_empty:
        return cells
    if isinstance(geometry, Point):
        cells.add(point_to_cell(geometry, center_x, center_y))
        return cells
    for line in iter_lines(geometry):
        cells.update(rasterize_line(line, center_x, center_y, step_m))
    if isinstance(geometry, (Polygon, MultiPolygon)):
        cells.add(point_to_cell(geometry.representative_point(), center_x, center_y))
    return cells


def chunked(items: list[str], size: int):
    for offset in range(0, len(items), size):
        yield items[offset : offset + size]


def write_function(path: Path, commands: list[str]) -> None:
    path.write_text("\n".join(commands) + "\n", encoding="utf-8")


def fill_layer_commands(min_x: int, max_x: int, min_z: int, max_z: int, y1: int, y2: int, block: str):
    commands: list[str] = []
    depth = max_z - min_z + 1
    height = y2 - y1 + 1
    max_width = max(1, 32000 // max(1, depth * height))
    for start_x in range(min_x, max_x + 1, max_width):
        end_x = min(max_x, start_x + max_width - 1)
        commands.append(f"fill {start_x} {y1} {min_z} {end_x} {y2} {max_z} {block}")
    return commands


def main() -> None:
    FUNCTIONS_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bbox = manifest["clip_bbox_3006"]
    minx = float(bbox["minx"])
    miny = float(bbox["miny"])
    maxx = float(bbox["maxx"])
    maxy = float(bbox["maxy"])
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2

    rel_min_x = math.floor((minx - center_x) / SCALE_M_PER_BLOCK)
    rel_max_x = math.ceil((maxx - center_x) / SCALE_M_PER_BLOCK)
    rel_min_z = math.floor((center_y - maxy) / SCALE_M_PER_BLOCK)
    rel_max_z = math.ceil((center_y - miny) / SCALE_M_PER_BLOCK)
    mc_min_x = MAP_ORIGIN_X + rel_min_x
    mc_max_x = MAP_ORIGIN_X + rel_max_x
    mc_min_z = MAP_ORIGIN_Z + rel_min_z
    mc_max_z = MAP_ORIGIN_Z + rel_max_z

    land = gpd.read_file(LAND_GPKG).to_crs("EPSG:3006")
    roads = gpd.read_file(ROADS_GPKG).to_crs("EPSG:3006")
    buildings = gpd.read_file(BUILDINGS_GPKG).to_crs("EPSG:3006")
    hydro = gpd.read_file(HYDRO_GPKG).to_crs("EPSG:3006")
    workarea = gpd.read_file(WORKAREA).to_crs("EPSG:3006")

    land_commands: list[str] = []
    land_counts: defaultdict[str, int] = defaultdict(int)
    sindex = land.sindex
    priority = {"Water": 6, "Wetland": 5, "Built": 4, "Industry": 4, "Aker": 3, "Forest": 2, "Open": 1}

    for rel_x in range(rel_min_x, rel_max_x + 1):
        sample_x = center_x + rel_x * SCALE_M_PER_BLOCK
        for rel_z in range(rel_min_z, rel_max_z + 1):
            sample_y = center_y - rel_z * SCALE_M_PER_BLOCK
            point = Point(sample_x, sample_y)
            best_kind = "Open"
            best_priority = 0
            for feature_index in sindex.query(point):
                row = land.iloc[int(feature_index)]
                if row.geometry is not None and row.geometry.covers(point):
                    kind = ascii_kind(row.get("objekttyp"))
                    if priority[kind] > best_priority:
                        best_kind = kind
                        best_priority = priority[kind]
            block = LAND_BLOCKS[best_kind]
            if block == "minecraft:grass_block":
                continue
            mc_x = MAP_ORIGIN_X + rel_x
            mc_z = MAP_ORIGIN_Z + rel_z
            land_counts[best_kind] += 1
            land_commands.append(f"setblock {mc_x} {MAP_Y} {mc_z} {block}")

    land_function_names: list[str] = []
    for index, commands in enumerate(chunked(land_commands, MAX_FUNCTION_COMMANDS)):
        name = f"topografi_2km_land_{index}"
        land_function_names.append(name)
        write_function(FUNCTIONS_DIR / f"{name}.mcfunction", ["# Generated land cells."] + commands)

    road_cells: dict[tuple[int, int], str] = {}
    road_counts: defaultdict[str, int] = defaultdict(int)
    for _, row in roads.iterrows():
        kind = road_kind(row.get("objekttyp"))
        block = ROAD_BLOCKS[kind]
        for line in iter_lines(row.geometry):
            for rel_x, rel_z in rasterize_line(line, center_x, center_y, SCALE_M_PER_BLOCK / 2):
                road_cells[(rel_x, rel_z)] = block

    road_commands: list[str] = ["# Generated roads."]
    for (rel_x, rel_z), block in sorted(road_cells.items()):
        mc_x = MAP_ORIGIN_X + rel_x
        mc_z = MAP_ORIGIN_Z + rel_z
        road_counts[block] += 1
        road_commands.append(f"setblock {mc_x} {MAP_Y + 1} {mc_z} {block}")
    write_function(FUNCTIONS_DIR / "topografi_2km_roads.mcfunction", road_commands)

    hydro_cells: set[tuple[int, int]] = set()
    for _, row in hydro.iterrows():
        hydro_cells.update(rasterize_geometry(row.geometry, center_x, center_y, SCALE_M_PER_BLOCK / 2))
    hydro_commands = ["# Generated hydrography."]
    for rel_x, rel_z in sorted(hydro_cells):
        mc_x = MAP_ORIGIN_X + rel_x
        mc_z = MAP_ORIGIN_Z + rel_z
        hydro_commands.append(f"setblock {mc_x} {MAP_Y + 2} {mc_z} minecraft:light_blue_concrete")
    write_function(FUNCTIONS_DIR / "topografi_2km_hydro.mcfunction", hydro_commands)

    building_cells: set[tuple[int, int]] = set()
    for _, row in buildings.iterrows():
        building_cells.update(rasterize_geometry(row.geometry, center_x, center_y, SCALE_M_PER_BLOCK / 3))
    building_commands = ["# Generated building works."]
    for rel_x, rel_z in sorted(building_cells):
        mc_x = MAP_ORIGIN_X + rel_x
        mc_z = MAP_ORIGIN_Z + rel_z
        building_commands.append(f"setblock {mc_x} {MAP_Y + 3} {mc_z} minecraft:bricks")
    write_function(FUNCTIONS_DIR / "topografi_2km_buildings.mcfunction", building_commands)

    property_cells: set[tuple[int, int]] = set()
    for geom in workarea.geometry:
        for line in iter_lines(geom):
            property_cells.update(rasterize_line(line, center_x, center_y, SCALE_M_PER_BLOCK / 3))
    property_commands = ["# Generated property outline."]
    for rel_x, rel_z in sorted(property_cells):
        mc_x = MAP_ORIGIN_X + rel_x
        mc_z = MAP_ORIGIN_Z + rel_z
        property_commands.append(f"setblock {mc_x} {MAP_Y + 4} {mc_z} minecraft:red_concrete")
    write_function(FUNCTIONS_DIR / "topografi_2km_property.mcfunction", property_commands)

    master_commands: list[str] = [
        "# Generated Millbygard topografi overview.",
        f"# Scale: 1 block = {SCALE_M_PER_BLOCK:g} meters. Origin: {MAP_ORIGIN_X} {MAP_Y} {MAP_ORIGIN_Z}.",
        "kill @e[type=text_display,tag=millbygard_topografi]",
    ]
    master_commands += fill_layer_commands(mc_min_x, mc_max_x, mc_min_z, mc_max_z, MAP_Y, MAP_Y + 4, "minecraft:air")
    master_commands += fill_layer_commands(mc_min_x, mc_max_x, mc_min_z, mc_max_z, MAP_Y, MAP_Y, "minecraft:grass_block")
    master_commands += [f"function millbygard:{name}" for name in land_function_names]
    master_commands.append("function millbygard:topografi_2km_roads")
    master_commands.append("function millbygard:topografi_2km_hydro")
    master_commands.append("function millbygard:topografi_2km_buildings")
    master_commands.append("function millbygard:topografi_2km_property")
    master_commands.append(
        "summon text_display "
        f"{mc_min_x} {MAP_Y + 6} {mc_min_z - 3} "
        "{Tags:[\"millbygard_topografi\"],billboard:\"center\","
        "text:'{\"text\":\"Millbygard Topografi 2 km - 1 block = 20 m\",\"color\":\"gold\",\"bold\":true}'}"
    )
    master_commands.append(
        "summon text_display "
        f"{mc_min_x} {MAP_Y + 4} {mc_min_z - 3} "
        "{Tags:[\"millbygard_topografi\"],billboard:\"center\","
        "text:'{\"text\":\"Rod linje = fastighet, tegel = byggnad, gra/gul/brun = vagar, bla = vatten, gron = skog\",\"color\":\"white\"}'}"
    )
    write_function(FUNCTIONS_DIR / "topografi_2km.mcfunction", master_commands)

    summary = {
        "function": "millbygard:topografi_2km",
        "minecraft_area": {
            "x": [mc_min_x, mc_max_x],
            "y": [MAP_Y, MAP_Y + 4],
            "z": [mc_min_z, mc_max_z],
        },
        "tp_hint": f"/tp @s {MAP_ORIGIN_X} {MAP_Y + 8} {MAP_ORIGIN_Z}",
        "scale_m_per_block": SCALE_M_PER_BLOCK,
        "generated_functions": [
            "topografi_2km",
            *land_function_names,
            "topografi_2km_roads",
            "topografi_2km_hydro",
            "topografi_2km_buildings",
            "topografi_2km_property",
        ],
        "land_cells": dict(sorted(land_counts.items())),
        "road_cells": dict(sorted(road_counts.items())),
        "hydro_cells": len(hydro_cells),
        "building_cells": len(building_cells),
        "property_outline_cells": len(property_cells),
    }
    (TOPO_DIR / "minecraft_topografi_2km_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
