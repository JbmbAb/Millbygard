from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


ROOT = Path(__file__).resolve().parents[1]
BUILDINGS = ROOT / "data" / "orsa_stackmora_3_12_byggnader.geojson"
ABOVE_GROUND = ROOT / "data" / "orsa_stackmora_3_12_ythojd_above_ground.tif"
OUT_CSV = ROOT / "output" / "building_surface_heights_20260416.csv"
OUT_JSON = ROOT / "output" / "building_surface_heights_20260416.json"


def clean_value(value: Any) -> Any:
    if value != value:
        return None
    return value


def stats_for_pixels(values: np.ndarray) -> dict[str, Any]:
    values = values[np.isfinite(values)]
    values = values[(values > -2.0) & (values < 80.0)]
    if values.size == 0:
        return {
            "pixels": 0,
            "height_p50_m": None,
            "height_p90_m": None,
            "height_p95_m": None,
            "height_max_m": None,
        }
    return {
        "pixels": int(values.size),
        "height_p50_m": round(float(np.percentile(values, 50)), 2),
        "height_p90_m": round(float(np.percentile(values, 90)), 2),
        "height_p95_m": round(float(np.percentile(values, 95)), 2),
        "height_max_m": round(float(values.max()), 2),
    }


def rows() -> list[dict[str, Any]]:
    buildings = gpd.read_file(BUILDINGS).to_crs(epsg=3006)
    output: list[dict[str, Any]] = []
    with rasterio.open(ABOVE_GROUND) as src:
        for feature_index, row in buildings.iterrows():
            parts = list(row.geometry.geoms) if row.geometry.geom_type == "MultiPolygon" else [row.geometry]
            for part_index, part in enumerate(parts, start=1):
                if part.is_empty or part.area < 0.5:
                    continue
                image, _ = mask(src, [part.__geo_interface__], crop=True, filled=False)
                data = image[0]
                values = data.compressed() if hasattr(data, "compressed") else data.ravel()
                output.append(
                    {
                        "feature_index": int(feature_index),
                        "part": part_index,
                        "husnummer": clean_value(row.get("husnummer")),
                        "objekttyp": clean_value(row.get("objekttyp")),
                        "andamal1": clean_value(row.get("andamal1")),
                        "insamlingslage": clean_value(row.get("insamlingslage")),
                        "area_m2": round(float(part.area), 2),
                        **stats_for_pixels(values.astype("float32")),
                    }
                )
    return output


def write_outputs(data: list[dict[str, Any]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(data[0].keys()) if data else []
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    payload = {
        "source_buildings": BUILDINGS.relative_to(ROOT).as_posix(),
        "source_above_ground": ABOVE_GROUND.relative_to(ROOT).as_posix(),
        "note": "Heights are DSM minus markhojd inside building polygons. Use p90/p95 as first-pass roof/surface height support, then verify with photos/manual measurements.",
        "features": data,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    data = rows()
    write_outputs(data)
    print(f"Wrote {len(data)} building surface height rows")
    print(OUT_CSV)
    print(OUT_JSON)


if __name__ == "__main__":
    main()
