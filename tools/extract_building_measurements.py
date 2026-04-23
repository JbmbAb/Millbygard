from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import MultiPolygon


ROOT = Path(__file__).resolve().parents[1]
BUILDINGS_PATH = ROOT / "data" / "orsa_stackmora_3_12_byggnader.geojson"
OUT_CSV = ROOT / "output" / "building_measurements_20260416.csv"
OUT_JSON = ROOT / "output" / "building_measurements_20260416.json"


def rectangle_dimensions(geom) -> tuple[float, float]:
    rect = geom.minimum_rotated_rectangle
    coords = list(rect.exterior.coords)
    edges = []
    for first, second in zip(coords, coords[1:]):
        dx = second[0] - first[0]
        dy = second[1] - first[1]
        edges.append((dx * dx + dy * dy) ** 0.5)
    edges = sorted(edges[:4], reverse=True)
    return float(edges[0]), float(edges[2] if len(edges) > 2 else edges[-1])


def clean_value(value: Any) -> Any:
    if value != value:
        return None
    return value


def measurement_rows() -> list[dict[str, Any]]:
    gdf = gpd.read_file(BUILDINGS_PATH).to_crs(epsg=3006)
    rows: list[dict[str, Any]] = []
    for feature_index, row in gdf.iterrows():
        geom = row.geometry
        parts = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
        for part_index, part in enumerate(parts, start=1):
            if part.is_empty or part.area < 0.5:
                continue
            length_m, width_m = rectangle_dimensions(part)
            centroid = part.centroid
            rows.append(
                {
                    "feature_index": int(feature_index),
                    "part": part_index,
                    "husnummer": clean_value(row.get("husnummer")),
                    "objekttyp": clean_value(row.get("objekttyp")),
                    "andamal1": clean_value(row.get("andamal1")),
                    "insamlingslage": clean_value(row.get("insamlingslage")),
                    "lagesosakerhetplan_m": clean_value(row.get("lagesosakerhetplan")),
                    "area_m2": round(float(part.area), 2),
                    "length_m": round(length_m, 2),
                    "width_m": round(width_m, 2),
                    "centroid_easting": round(float(centroid.x), 2),
                    "centroid_northing": round(float(centroid.y), 2),
                }
            )
    return rows


def write_outputs(rows: list[dict[str, Any]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "source": BUILDINGS_PATH.relative_to(ROOT).as_posix(),
        "note": "Dimensions are from Lantmateriet building polygons. Most local features use insamlingslage=Takkant, so length/width describe roof-edge footprint rather than measured wall footprint.",
        "features": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    rows = measurement_rows()
    write_outputs(rows)
    print(f"Wrote {len(rows)} building measurement rows")
    print(OUT_CSV)
    print(OUT_JSON)


if __name__ == "__main__":
    main()
