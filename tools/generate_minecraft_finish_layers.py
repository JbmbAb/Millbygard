from __future__ import annotations

import json
import math
import os
from importlib.util import find_spec
from pathlib import Path
from typing import Iterable

from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, shape
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

try:
    import rasterio
except Exception:  # pragma: no cover - optional when only vector layers are regenerated
    rasterio = None


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
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

PROPERTY = DATA / "orsa_stackmora_3_12_workarea.geojson"
SPLIT_PROPERTY = DATA / "orsa_stackmora_3_12_split.geojson"
BUILDINGS = DATA / "orsa_stackmora_3_12_byggnader.geojson"
TOWER = DATA / "orsa_stackmora_3_12_tower_site.geojson"
SCALE_META = DATA / "orsa_stackmora_3_12_scale_transition_zones_metadata.json"
PHOTOS = OUTPUT / "foton_geotaggar_alla.geojson"
PHOTO_DIRECTIONS = OUTPUT / "foton_geotaggar_senaste_80.geojson"
ROADS = DATA / "topografi" / "orsa_stackmora_3_12_topografi_vagar.geojson"
HYDRO = DATA / "topografi" / "orsa_stackmora_3_12_topografi_hydrografi_2km.geojson"
MARKHOJD = DATA / "orsa_stackmora_3_12_markhojd.tif"

OUT_OVERLAY = FUNCTIONS / "farm4_data_overlay.mcfunction"
OUT_COMPLETE = FUNCTIONS / "farm4_complete.mcfunction"
OUT_MANIFEST = DATA / "minecraft_finish_layers_manifest.json"

TARGET_CRS = "EPSG:3006"
WGS84_TO_3006 = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
TO_WGS84 = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)

FARM_X = 360
FARM_Y = 80
FARM_Z = -160

INNER_RADIUS_M = 80.0
TRANSITION_RADIUS_M = 140.0
DETAIL_SCALE = 4.0
OUTER_SCALE = 1.0

MAX_CONTEXT_M = 265.0
PHOTO_DIRECTION_LENGTH_M = 12.0


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def project(geom):
    return shapely_transform(WGS84_TO_3006.transform, geom)


def inverse_project(geom):
    return shapely_transform(TO_WGS84.transform, geom)


def farm_center_3006() -> Point:
    meta = load_json(SCALE_META)
    center = meta["center_wgs84"]
    x, y = WGS84_TO_3006.transform(center["lon"], center["lat"])
    return Point(x, y)


CENTER_3006 = farm_center_3006()


def scale_at_distance(distance_m: float) -> float:
    if distance_m <= INNER_RADIUS_M:
        return DETAIL_SCALE
    if distance_m >= TRANSITION_RADIUS_M:
        return OUTER_SCALE
    t = (distance_m - INNER_RADIUS_M) / (TRANSITION_RADIUS_M - INNER_RADIUS_M)
    smooth = t * t * (3 - 2 * t)
    return DETAIL_SCALE + (OUTER_SCALE - DETAIL_SCALE) * smooth


def displayed_radius(distance_m: float) -> float:
    if distance_m <= 0:
        return 0.0
    step = 1.0
    radius = 0.0
    walked = 0.0
    while walked < distance_m:
        a = walked
        b = min(distance_m, walked + step)
        radius += (b - a) * scale_at_distance((a + b) / 2)
        walked = b
    return radius


def world_to_farm_xy(point: Point) -> tuple[int, int]:
    dx = point.x - CENTER_3006.x
    dz = point.y - CENTER_3006.y
    distance = math.hypot(dx, dz)
    if distance == 0:
        return FARM_X, FARM_Z
    shown = displayed_radius(distance)
    unit_x = dx / distance
    unit_z = dz / distance
    return round(FARM_X + unit_x * shown), round(FARM_Z - unit_z * shown)


def bresenham(x0: int, z0: int, x1: int, z1: int) -> Iterable[tuple[int, int]]:
    dx = abs(x1 - x0)
    dz = abs(z1 - z0)
    sx = 1 if x0 < x1 else -1
    sz = 1 if z0 < z1 else -1
    err = dx - dz
    x, z = x0, z0
    while True:
        yield x, z
        if x == x1 and z == z1:
            break
        e2 = 2 * err
        if e2 > -dz:
            err -= dz
            x += sx
        if e2 < dx:
            err += dx
            z += sz


def add_block(blocks: dict[tuple[int, int, int], str], x: int, y: int, z: int, block: str) -> None:
    blocks[(x, y, z)] = block


def add_line(
    blocks: dict[tuple[int, int, int], str],
    a: tuple[int, int],
    b: tuple[int, int],
    y: int,
    block: str,
    width: int = 0,
) -> None:
    for x, z in bresenham(a[0], a[1], b[0], b[1]):
        for ox in range(-width, width + 1):
            for oz in range(-width, width + 1):
                if ox * ox + oz * oz <= width * width:
                    add_block(blocks, x + ox, y, z + oz, block)


def densified_line_points(line: LineString, spacing_m: float = 3.0) -> list[Point]:
    length = line.length
    if length <= 0:
        return []
    count = max(1, math.ceil(length / spacing_m))
    return [line.interpolate(length * i / count) for i in range(count + 1)]


def geometry_lines(geom) -> Iterable[LineString]:
    if geom.is_empty:
        return
    if geom.geom_type == "LineString":
        yield geom
    elif geom.geom_type == "MultiLineString":
        for part in geom.geoms:
            yield part
    elif geom.geom_type == "Polygon":
        yield LineString(geom.exterior.coords)
        for interior in geom.interiors:
            yield LineString(interior.coords)
    elif geom.geom_type == "MultiPolygon":
        for part in geom.geoms:
            yield from geometry_lines(part)
    elif hasattr(geom, "geoms"):
        for part in geom.geoms:
            yield from geometry_lines(part)


def add_geometry_outline(
    blocks: dict[tuple[int, int, int], str],
    geom,
    y: int,
    block: str,
    spacing_m: float = 3.0,
    width: int = 0,
) -> int:
    placed_before = len(blocks)
    for line in geometry_lines(geom):
        pts = densified_line_points(line, spacing_m)
        if len(pts) < 2:
            continue
        transformed = [world_to_farm_xy(pt) for pt in pts]
        for a, b in zip(transformed, transformed[1:]):
            add_line(blocks, a, b, y, block, width=width)
    return len(blocks) - placed_before


def add_geometry_dots(
    blocks: dict[tuple[int, int, int], str],
    geom,
    y: int,
    block: str,
    spacing_m: float = 12.0,
) -> int:
    placed_before = len(blocks)
    for line in geometry_lines(geom):
        for point in densified_line_points(line, spacing_m):
            x, z = world_to_farm_xy(point)
            add_block(blocks, x, y, z, block)
    return len(blocks) - placed_before


def add_square_marker(
    blocks: dict[tuple[int, int, int], str],
    point: Point,
    y: int,
    block: str,
    radius: int = 1,
) -> None:
    x, z = world_to_farm_xy(point)
    for ox in range(-radius, radius + 1):
        for oz in range(-radius, radius + 1):
            add_block(blocks, x + ox, y, z + oz, block)


def add_scale_rings(blocks: dict[tuple[int, int, int], str]) -> dict[str, int]:
    stats = {}
    for distance, block, name, y in [
        (INNER_RADIUS_M, "minecraft:lime_concrete", "detail_80m_ring", 86),
        (TRANSITION_RADIUS_M, "minecraft:orange_concrete", "transition_140m_ring", 86),
        (MAX_CONTEXT_M, "minecraft:light_blue_concrete", "context_coverage_ring", 86),
    ]:
        radius = round(displayed_radius(distance))
        before = len(blocks)
        steps = max(96, round(2 * math.pi * radius / 18))
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            x = round(FARM_X + math.sin(angle) * radius)
            z = round(FARM_Z + math.cos(angle) * radius)
            add_block(blocks, x, y, z, block)
        stats[name] = len(blocks) - before
    return stats


def add_property_layers(blocks: dict[tuple[int, int, int], str]) -> dict[str, int]:
    workarea = project(shape(load_json(PROPERTY)["features"][0]["geometry"]))
    split = load_json(SPLIT_PROPERTY)
    stats = {
        "master_property_boundary_blocks": add_geometry_outline(
            blocks, workarea, 88, "minecraft:red_concrete", spacing_m=12.0, width=0
        )
    }
    part_blocks = 0
    for feature in split["features"]:
        part_blocks += add_geometry_dots(
            blocks,
            project(shape(feature["geometry"])),
            89,
            "minecraft:red_stained_glass",
            spacing_m=18.0,
        )
    stats["split_property_boundary_blocks"] = part_blocks
    return stats


def add_buildings(blocks: dict[tuple[int, int, int], str]) -> dict[str, int]:
    data = load_json(BUILDINGS)
    count = 0
    for feature in data["features"]:
        geom = project(shape(feature["geometry"]))
        block = "minecraft:gold_block" if feature["properties"].get("objekttyp") == "Bostad" else "minecraft:yellow_concrete"
        count += add_geometry_outline(blocks, geom, 90, block, spacing_m=3.0)
    return {"official_building_footprint_blocks": count, "official_building_features": len(data["features"])}


def add_tower(blocks: dict[tuple[int, int, int], str]) -> dict[str, int | float]:
    feature = load_json(TOWER)["features"][0]
    point = project(shape(feature["geometry"]))
    x, z = world_to_farm_xy(point)
    for y in range(82, 104):
        add_block(blocks, x, y, z, "minecraft:magenta_concrete")
    for ox in range(-2, 3):
        for oz in range(-2, 3):
            add_block(blocks, x + ox, 104, z + oz, "minecraft:magenta_stained_glass")
    return {
        "tower_marker_x": x,
        "tower_marker_z": z,
        "tower_elevation_m": round(float(feature["properties"]["elevation_m"]), 2),
    }


def add_photos(blocks: dict[tuple[int, int, int], str]) -> dict[str, int]:
    if not PHOTOS.exists():
        return {"photo_points": 0, "photo_direction_blocks": 0}
    data = load_json(PHOTOS)
    point_count = 0
    for feature in data["features"]:
        props = feature.get("properties", {})
        if not props.get("has_gps"):
            continue
        point = project(shape(feature["geometry"]))
        add_square_marker(blocks, point, 91, "minecraft:yellow_concrete", radius=0)
        point_count += 1

    line_before = len(blocks)
    direction_data = load_json(PHOTO_DIRECTIONS) if PHOTO_DIRECTIONS.exists() else data
    direction_count = 0
    for feature in direction_data["features"]:
        props = feature.get("properties", {})
        if not props.get("has_gps") or not props.get("has_direction"):
            continue
        point = project(shape(feature["geometry"]))
        direction = math.radians(float(props["direction_deg"]))
        end = Point(
            point.x + math.sin(direction) * PHOTO_DIRECTION_LENGTH_M,
            point.y + math.cos(direction) * PHOTO_DIRECTION_LENGTH_M,
        )
        add_line(blocks, world_to_farm_xy(point), world_to_farm_xy(end), 92, "minecraft:white_concrete")
        direction_count += 1
    return {
        "photo_points": point_count,
        "photo_direction_features": direction_count,
        "photo_direction_blocks": len(blocks) - line_before,
    }


def add_topography(blocks: dict[tuple[int, int, int], str]) -> dict[str, int]:
    stats = {}
    context_circle = CENTER_3006.buffer(MAX_CONTEXT_M)
    for path, block, key, y, spacing in [
        (ROADS, "minecraft:gray_concrete", "topografi_road_blocks", 85, 28.0),
        (HYDRO, "minecraft:cyan_stained_glass", "groundwater_hydro_cue_blocks", 78, 30.0),
    ]:
        if not path.exists():
            stats[key] = 0
            continue
        before = len(blocks)
        for feature in load_json(path)["features"]:
            geom = project(shape(feature["geometry"])).intersection(context_circle)
            if key == "groundwater_hydro_cue_blocks":
                add_geometry_dots(blocks, geom, y, block, spacing_m=spacing)
            else:
                add_geometry_outline(blocks, geom, y, block, spacing_m=spacing)
        stats[key] = len(blocks) - before
    return stats


def add_height_points(blocks: dict[tuple[int, int, int], str]) -> dict[str, float | int]:
    if rasterio is None or not MARKHOJD.exists():
        return {"height_anchor_points": 0}
    workarea = project(shape(load_json(PROPERTY)["features"][0]["geometry"]))
    before = len(blocks)
    values: list[float] = []
    with rasterio.open(MARKHOJD) as src:
        minx, miny, maxx, maxy = workarea.bounds
        step = 30.0
        y = miny
        points: list[Point] = []
        while y <= maxy:
            x = minx
            while x <= maxx:
                point = Point(x, y)
                if workarea.contains(point):
                    points.append(point)
                x += step
            y += step
        samples = list(src.sample([(p.x, p.y) for p in points]))
        valid: list[tuple[Point, float]] = []
        for point, sample in zip(points, samples):
            value = float(sample[0])
            if math.isfinite(value) and value > -1000:
                valid.append((point, value))
                values.append(value)
        if not valid:
            return {"height_anchor_points": 0}
        low = min(values)
        high = max(values)
        span = max(1.0, high - low)
        for point, value in valid:
            y_block = 82 + round((value - low) / span * 14)
            block = "minecraft:lime_concrete"
            if value > low + span * 0.66:
                block = "minecraft:red_concrete"
            elif value > low + span * 0.33:
                block = "minecraft:orange_concrete"
            add_square_marker(blocks, point, y_block, block, radius=0)
    return {
        "height_anchor_points": len(blocks) - before,
        "height_min_m": round(min(values), 2),
        "height_max_m": round(max(values), 2),
    }


def write_overlay(blocks: dict[tuple[int, int, int], str], stats: dict) -> None:
    lines = [
        "# Generated finish overlay for the 4:1 Millbygard plan.",
        "# Sources: property boundary, scale rings, official building vector, tower point, photos, topography and markhojd anchors.",
        "# Does not place water blocks; hydrography/groundwater is a cyan glass cue below the surface.",
        "kill @e[type=text_display,tag=millbygard_finish]",
    ]
    for (x, y, z), block in sorted(blocks.items(), key=lambda item: (item[0][1], item[0][2], item[0][0])):
        lines.append(f"setblock {x} {y} {z} {block}")
    lines.extend(
        [
            f"summon text_display {FARM_X} 118 {FARM_Z} {{Tags:[\"millbygard_finish\"],billboard:\"center\",brightness:{{sky:15,block:15}},see_through:1b,shadow:1b,background:1073741824,text:'{{\"text\":\"Millbygard komplett planlager: grans, hus, hojd, foto, topo\",\"color\":\"gold\",\"bold\":true}}'}}",
            f"summon text_display {FARM_X} 115 {FARM_Z + 6} {{Tags:[\"millbygard_finish\"],billboard:\"center\",brightness:{{sky:15,block:15}},see_through:1b,shadow:1b,background:1073741824,text:'{{\"text\":\"Rod=fastighet Gul=LM byggnad Magenta=torn Gul/vit=foto Gra=vag Cyan under mark=grundvatten\",\"color\":\"white\"}}'}}",
            'tellraw @a [{"text":"Millbygard komplett enligt planlager: fastighetsgrans, byggnader, skalringar, hojdankare, fotopunkter och topografikontroll ar pa plats.","color":"gold"}]',
        ]
    )
    OUT_OVERLAY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_complete() -> None:
    lines = [
        "# Complete 4:1 Millbygard build according to the local plan.",
        "# Builds the dry farm model, then overlays official/context layers.",
        "function millbygard:farm4_zone",
        "function millbygard:farm4_data_overlay",
        f"tp @a[tag=!millbygard_no_auto_tp,distance=..900] {FARM_X} 125 {FARM_Z} 0 35",
        'tellraw @a [{"text":"4:1 Millbygard komplett: gard + planlager. Inget vatten har lagts ut.","color":"gold"}]',
    ]
    OUT_COMPLETE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    blocks: dict[tuple[int, int, int], str] = {}
    stats: dict = {
        "farm_center_3006": {"x": CENTER_3006.x, "y": CENTER_3006.y},
        "minecraft_center": {"x": FARM_X, "y": FARM_Y, "z": FARM_Z},
        "radial_lens": {
            "inner_radius_m": INNER_RADIUS_M,
            "transition_radius_m": TRANSITION_RADIUS_M,
            "context_radius_m": MAX_CONTEXT_M,
            "display_radius_inner_blocks": round(displayed_radius(INNER_RADIUS_M)),
            "display_radius_transition_blocks": round(displayed_radius(TRANSITION_RADIUS_M)),
            "display_radius_context_blocks": round(displayed_radius(MAX_CONTEXT_M)),
        },
        "sources": {
            "property": str(PROPERTY.relative_to(ROOT)),
            "split_property": str(SPLIT_PROPERTY.relative_to(ROOT)),
            "buildings": str(BUILDINGS.relative_to(ROOT)),
            "tower": str(TOWER.relative_to(ROOT)),
            "photos": str(PHOTOS.relative_to(ROOT)),
            "photo_directions": str(PHOTO_DIRECTIONS.relative_to(ROOT)),
            "roads": str(ROADS.relative_to(ROOT)),
            "hydro": str(HYDRO.relative_to(ROOT)),
            "markhojd": str(MARKHOJD.relative_to(ROOT)),
        },
    }
    stats.update(add_scale_rings(blocks))
    stats.update(add_property_layers(blocks))
    stats.update(add_topography(blocks))
    stats.update(add_buildings(blocks))
    stats.update(add_height_points(blocks))
    stats.update(add_tower(blocks))
    stats.update(add_photos(blocks))
    stats["total_unique_blocks"] = len(blocks)
    stats["output_functions"] = [
        str(OUT_OVERLAY.relative_to(ROOT)),
        str(OUT_COMPLETE.relative_to(ROOT)),
    ]
    stats["no_water_blocks"] = True

    write_overlay(blocks, stats)
    write_complete()
    OUT_MANIFEST.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
