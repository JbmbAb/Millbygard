from __future__ import annotations

import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BUILDINGS = DATA_DIR / "orsa_stackmora_3_12_byggnader.geojson"
PROPERTY = DATA_DIR / "orsa_stackmora_3_12_workarea.geojson"
PROPERTY_CIRCLE_META = DATA_DIR / "orsa_stackmora_3_12_workarea_circle_metadata.json"
OUTPUT_GEOJSON = DATA_DIR / "orsa_stackmora_3_12_scale_transition_zones.geojson"
OUTPUT_METADATA = DATA_DIR / "orsa_stackmora_3_12_scale_transition_zones_metadata.json"

INNER_RADIUS_M = 80.0
TRANSITION_RADIUS_M = 140.0
DETAIL_SCALE = 4.0
OUTER_SCALE = 1.0
SEGMENTS = 192


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def farm_center_wgs84() -> tuple[float, float]:
    data = load_json(BUILDINGS)
    points = []
    for feature in data.get("features", []):
        geom = shape(feature["geometry"])
        if geom.geom_type == "Point":
            points.append(geom)
    if points:
        lon = sum(point.x for point in points) / len(points)
        lat = sum(point.y for point in points) / len(points)
        return lon, lat

    prop = shape(load_json(PROPERTY)["features"][0]["geometry"])
    centroid = prop.centroid
    return centroid.x, centroid.y


def smooth_scale_expression() -> str:
    return (
        "if d <= inner_radius_m: scale = 4.0; "
        "elif d >= transition_radius_m: scale = 1.0; "
        "else: t = (d - inner_radius_m) / (transition_radius_m - inner_radius_m); "
        "s = t*t*(3 - 2*t); scale = 4.0 + (1.0 - 4.0) * s"
    )


def iter_exterior_points_3006(geom) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    geoms = geom.geoms if hasattr(geom, "geoms") else [geom]
    for part in geoms:
        if part.geom_type == "Polygon":
            points.extend((float(x), float(y)) for x, y in part.exterior.coords)
        elif part.geom_type == "MultiPolygon":
            points.extend(iter_exterior_points_3006(part))
    return points


def feature(name: str, role: str, geom, properties: dict) -> dict:
    return {
        "type": "Feature",
        "geometry": mapping(geom),
        "properties": {
            "name": name,
            "role": role,
            **properties,
        },
    }


def main() -> None:
    to_3006 = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    to_wgs84 = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)

    center_lon, center_lat = farm_center_wgs84()
    center_x, center_y = to_3006.transform(center_lon, center_lat)
    center_3006 = Point(center_x, center_y)

    property_circle_meta = load_json(PROPERTY_CIRCLE_META)
    property_3006 = transform(to_3006.transform, shape(load_json(PROPERTY)["features"][0]["geometry"]))
    max_property_distance_m = max(
        center_3006.distance(Point(x, y)) for x, y in iter_exterior_points_3006(property_3006)
    )
    context_radius_m = max(float(property_circle_meta["radius_m"]), max_property_distance_m + 10.0)
    if context_radius_m <= TRANSITION_RADIUS_M:
        raise ValueError("Context circle must be larger than transition radius")

    inner_3006 = center_3006.buffer(INNER_RADIUS_M, resolution=SEGMENTS)
    transition_outer_3006 = center_3006.buffer(TRANSITION_RADIUS_M, resolution=SEGMENTS)
    context_outer_3006 = center_3006.buffer(context_radius_m, resolution=SEGMENTS)

    transition_ring_3006 = transition_outer_3006.difference(inner_3006)
    context_ring_3006 = context_outer_3006.difference(transition_outer_3006)

    inner_wgs84 = transform(to_wgs84.transform, inner_3006)
    transition_wgs84 = transform(to_wgs84.transform, transition_ring_3006)
    context_wgs84 = transform(to_wgs84.transform, context_ring_3006)
    property_wgs84 = shape(load_json(PROPERTY)["features"][0]["geometry"])

    features = [
        feature(
            "4to1 gard detail zone",
            "detail_4to1",
            inner_wgs84,
            {
                "scale": DETAIL_SCALE,
                "radius_m": INNER_RADIUS_M,
                "stroke": "#00aa00",
                "stroke-width": 2,
                "fill": "#00aa00",
                "fill-opacity": 0.12,
            },
        ),
        feature(
            "soft transition zone",
            "transition_4to1_to_1to1",
            transition_wgs84,
            {
                "inner_radius_m": INNER_RADIUS_M,
                "outer_radius_m": TRANSITION_RADIUS_M,
                "scale_from": DETAIL_SCALE,
                "scale_to": OUTER_SCALE,
                "scale_function": "smoothstep",
                "stroke": "#ffaa00",
                "stroke-width": 2,
                "fill": "#ffaa00",
                "fill-opacity": 0.10,
            },
        ),
        feature(
            "1to1 context zone",
            "context_1to1",
            context_wgs84,
            {
                "scale": OUTER_SCALE,
                "inner_radius_m": TRANSITION_RADIUS_M,
                "outer_radius_m": round(context_radius_m, 2),
                "stroke": "#0066ff",
                "stroke-width": 2,
                "fill": "#0066ff",
                "fill-opacity": 0.06,
            },
        ),
        feature(
            "fastighetsgrans",
            "property_boundary",
            property_wgs84,
            {
                "stroke": "#ff0000",
                "stroke-width": 3,
                "fill": "#ff0000",
                "fill-opacity": 0.0,
            },
        ),
    ]

    OUTPUT_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    metadata = {
        "output_geojson": str(OUTPUT_GEOJSON.relative_to(ROOT)),
        "center_source": str(BUILDINGS.relative_to(ROOT)),
        "center_wgs84": {"lon": center_lon, "lat": center_lat},
        "center_3006": {"x": center_x, "y": center_y},
        "inner_radius_m": INNER_RADIUS_M,
        "transition_radius_m": TRANSITION_RADIUS_M,
        "context_radius_m": context_radius_m,
        "max_property_distance_from_center_m": max_property_distance_m,
        "detail_scale": DETAIL_SCALE,
        "outer_scale": OUTER_SCALE,
        "scale_function": smooth_scale_expression(),
        "area_sqm": {
            "detail_4to1": inner_3006.area,
            "transition": transition_ring_3006.area,
            "context_1to1": context_ring_3006.area,
        },
        "notes": [
            "Fastighetsgransen ar inte ersatt av cirklarna; den finns som separat overlay-feature.",
            "Anvand zonerna som design-/exportunderlag tills Minecraft-transformen byggs.",
            "Nya fastighetsfoton kan anvandas for att justera center och radier innan terrang exporteras slutligt.",
        ],
    }
    OUTPUT_METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
