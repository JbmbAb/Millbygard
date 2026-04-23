from __future__ import annotations

import json
import os
from importlib.util import find_spec
from pathlib import Path
from typing import Any


def configure_proj_data() -> None:
    """Force Rasterio to use its matching PROJ database on Windows."""
    spec = find_spec("rasterio")
    if not spec or not spec.origin:
        return
    proj_data = Path(spec.origin).parent / "proj_data"
    if proj_data.exists():
        os.environ.setdefault("PROJ_DATA", str(proj_data))
        os.environ.setdefault("PROJ_LIB", str(proj_data))


configure_proj_data()

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.mask import mask
from rasterio.warp import transform, transform_geom


ROOT = Path(__file__).resolve().parents[1]
DEM_PATH = ROOT / "data" / "orsa_stackmora_3_12_markhojd.tif"
WORKAREA_PATH = ROOT / "data" / "orsa_stackmora_3_12_workarea.geojson"
OUT_GEOJSON = ROOT / "data" / "orsa_stackmora_3_12_tower_site.geojson"
OUT_METADATA = ROOT / "data" / "orsa_stackmora_3_12_tower_site_metadata.json"


def raster_crs_for(src: rasterio.io.DatasetReader) -> CRS:
    if src.crs and "SWEREF99" in src.crs.to_wkt():
        return CRS.from_epsg(3006)
    if not src.crs:
        raise ValueError(f"Missing CRS in {DEM_PATH}")
    return src.crs


def load_workarea_geometries() -> list[dict[str, Any]]:
    data = json.loads(WORKAREA_PATH.read_text(encoding="utf-8"))
    return [feature["geometry"] for feature in data["features"]]


def find_highest_point() -> dict[str, Any]:
    with rasterio.open(DEM_PATH) as src:
        crs = raster_crs_for(src)
        geoms_src = [transform_geom("EPSG:4326", crs, geom) for geom in load_workarea_geometries()]
        arr, out_transform = mask(src, geoms_src, crop=True, filled=False)
        band = arr[0]

        valid = ~band.mask if hasattr(band, "mask") else np.ones(band.shape, dtype=bool)
        if src.nodata is not None:
            valid &= band != src.nodata
        if not valid.any():
            raise ValueError("No valid elevation pixels inside workarea")

        values = np.asarray(band)
        row, col = np.unravel_index(np.argmax(np.where(valid, values, -np.inf)), values.shape)
        elevation_m = float(values[row, col])
        easting, northing = rasterio.transform.xy(out_transform, row, col, offset="center")
        lon, lat = transform(crs, "EPSG:4326", [easting], [northing])

    return {
        "longitude": float(lon[0]),
        "latitude": float(lat[0]),
        "elevation_m": elevation_m,
        "sweref99_tm_easting": float(easting),
        "sweref99_tm_northing": float(northing),
    }


def write_outputs(point: dict[str, Any]) -> None:
    properties = {
        "name": "Tornplats - hogsta punkt",
        "role": "tower_site",
        "source": DEM_PATH.relative_to(ROOT).as_posix(),
        "basis": "Highest valid elevation cell inside property workarea.",
        **point,
    }
    geojson = {
        "type": "FeatureCollection",
        "name": OUT_GEOJSON.stem,
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point["longitude"], point["latitude"]],
                },
                "properties": properties,
            }
        ],
    }
    metadata = {
        "output": OUT_GEOJSON.relative_to(ROOT).as_posix(),
        "metadata": OUT_METADATA.relative_to(ROOT).as_posix(),
        "workarea": WORKAREA_PATH.relative_to(ROOT).as_posix(),
        "dem": DEM_PATH.relative_to(ROOT).as_posix(),
        "tower_site_rule": "Use the highest valid DEM cell inside the property workarea as the tower anchor.",
        **point,
    }
    OUT_GEOJSON.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    point = find_highest_point()
    write_outputs(point)
    print(
        "Tower site: "
        f"{point['latitude']:.9f}, {point['longitude']:.9f}, "
        f"{point['elevation_m']:.2f} m"
    )


if __name__ == "__main__":
    main()
