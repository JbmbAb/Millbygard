from __future__ import annotations

import json
import math
import random
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WORKAREA = DATA_DIR / "orsa_stackmora_3_12_workarea.geojson"
OUTPUT_GEOJSON = DATA_DIR / "orsa_stackmora_3_12_workarea_circle.geojson"
OUTPUT_OVERLAY = DATA_DIR / "orsa_stackmora_3_12_workarea_circle_overlay.geojson"
OUTPUT_METADATA = DATA_DIR / "orsa_stackmora_3_12_workarea_circle_metadata.json"

SEGMENTS = 192
MARGIN_M = 10.0


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def circle_from_2(a: tuple[float, float], b: tuple[float, float]) -> tuple[tuple[float, float], float]:
    center = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return center, dist(a, b) / 2


def circle_from_3(
    a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]
) -> tuple[tuple[float, float], float]:
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        candidates = [circle_from_2(a, b), circle_from_2(a, c), circle_from_2(b, c)]
        return min(candidates, key=lambda item: item[1])
    ux = (
        (ax * ax + ay * ay) * (by - cy)
        + (bx * bx + by * by) * (cy - ay)
        + (cx * cx + cy * cy) * (ay - by)
    ) / d
    uy = (
        (ax * ax + ay * ay) * (cx - bx)
        + (bx * bx + by * by) * (ax - cx)
        + (cx * cx + cy * cy) * (bx - ax)
    ) / d
    center = (ux, uy)
    return center, dist(center, a)


def contains(circle: tuple[tuple[float, float], float], point: tuple[float, float]) -> bool:
    center, radius = circle
    return dist(center, point) <= radius + 1e-7


def min_enclosing_circle(points: list[tuple[float, float]]) -> tuple[tuple[float, float], float]:
    shuffled = points[:]
    random.Random(312).shuffle(shuffled)
    circle: tuple[tuple[float, float], float] | None = None
    for i, p in enumerate(shuffled):
        if circle is not None and contains(circle, p):
            continue
        circle = (p, 0.0)
        for j, q in enumerate(shuffled[:i]):
            if contains(circle, q):
                continue
            circle = circle_from_2(p, q)
            for r in shuffled[:j]:
                if not contains(circle, r):
                    circle = circle_from_3(p, q, r)
    if circle is None:
        raise ValueError("No coordinates found in workarea")
    return circle


def iter_exterior_points(geom) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    geoms = geom.geoms if hasattr(geom, "geoms") else [geom]
    for part in geoms:
        if part.geom_type == "Polygon":
            points.extend((float(x), float(y)) for x, y in part.exterior.coords)
        elif part.geom_type == "MultiPolygon":
            points.extend(iter_exterior_points(part))
    return points


def main() -> None:
    data = json.loads(WORKAREA.read_text(encoding="utf-8"))
    union_wgs84 = shape(data["features"][0]["geometry"])

    to_3006 = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    to_wgs84 = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)

    union_3006 = transform(to_3006.transform, union_wgs84)
    points_3006 = iter_exterior_points(union_3006)
    center_3006, radius_m = min_enclosing_circle(points_3006)
    radius_with_margin_m = radius_m + MARGIN_M

    circle_3006 = shape({"type": "Point", "coordinates": center_3006}).buffer(
        radius_with_margin_m, resolution=SEGMENTS
    )
    circle_wgs84 = transform(to_wgs84.transform, circle_3006)
    center_lon, center_lat = to_wgs84.transform(center_3006[0], center_3006[1])

    feature = {
        "type": "Feature",
        "geometry": mapping(circle_wgs84),
        "properties": {
            "name": "ORSA STACKMORA 3:12 enclosing circle",
            "source": str(WORKAREA.relative_to(ROOT)),
            "method": "minimum enclosing circle in EPSG:3006 plus margin",
            "radius_m": round(radius_with_margin_m, 2),
            "diameter_m": round(radius_with_margin_m * 2, 2),
            "margin_m": MARGIN_M,
            "center_lon": round(center_lon, 9),
            "center_lat": round(center_lat, 9),
            "center_x_3006": round(center_3006[0], 3),
            "center_y_3006": round(center_3006[1], 3),
        },
    }
    OUTPUT_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    boundary_feature = {
        "type": "Feature",
        "geometry": data["features"][0]["geometry"],
        "properties": {
            **data["features"][0].get("properties", {}),
            "name": "ORSA STACKMORA 3:12 fastighetsgräns",
            "role": "property_boundary",
            "stroke": "#ff0000",
            "stroke-width": 3,
            "fill": "#ff0000",
            "fill-opacity": 0.0,
        },
    }
    overlay_circle = {
        **feature,
        "properties": {
            **feature["properties"],
            "role": "coverage_circle",
            "stroke": "#0066ff",
            "stroke-width": 2,
            "fill": "#0066ff",
            "fill-opacity": 0.08,
        },
    }
    OUTPUT_OVERLAY.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": [overlay_circle, boundary_feature]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    metadata = {
        "source": str(WORKAREA.relative_to(ROOT)),
        "output_geojson": str(OUTPUT_GEOJSON.relative_to(ROOT)),
        "output_overlay_geojson": str(OUTPUT_OVERLAY.relative_to(ROOT)),
        "crs_processing": "EPSG:3006",
        "crs_output": "EPSG:4326",
        "center_wgs84": {"lon": center_lon, "lat": center_lat},
        "center_3006": {"x": center_3006[0], "y": center_3006[1]},
        "radius_without_margin_m": radius_m,
        "margin_m": MARGIN_M,
        "radius_m": radius_with_margin_m,
        "diameter_m": radius_with_margin_m * 2,
        "property_area_sqm": union_3006.area,
        "circle_area_sqm": circle_3006.area,
        "circle_covers_workarea": bool(circle_3006.covers(union_3006)),
        "bounds_3006": {
            "minx": union_3006.bounds[0],
            "miny": union_3006.bounds[1],
            "maxx": union_3006.bounds[2],
            "maxy": union_3006.bounds[3],
        },
    }
    OUTPUT_METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
