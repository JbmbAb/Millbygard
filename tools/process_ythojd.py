from __future__ import annotations

import json
import os
import tempfile
import zipfile
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import numpy as np


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
from rasterio.mask import mask
from rasterio.warp import transform_geom
from rasterio.warp import Resampling, reproject
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[1]
KARTOR_EXTRACT_DIR = Path(
    r"C:\Users\jimmy\Desktop\MiljoBeslut_Produktdata\Kartor\Ythojd_677_48_7500_2024"
)
RAW_ZIP = ROOT / "01_data_raw" / "ythojd" / "orsa_stackmora_3_12_ythojd_677_48_7500_2024.zip"
WORKAREA = ROOT / "data" / "orsa_stackmora_3_12_workarea.geojson"
MARKHOJD = ROOT / "data" / "orsa_stackmora_3_12_markhojd.tif"
OUT_DSM = ROOT / "data" / "orsa_stackmora_3_12_ythojd_dsm.tif"
OUT_TRUEORTHO = ROOT / "data" / "orsa_stackmora_3_12_ythojd_trueortho.tif"
OUT_CLASS = ROOT / "data" / "orsa_stackmora_3_12_ythojd_class.tif"
OUT_MISSING = ROOT / "data" / "orsa_stackmora_3_12_ythojd_missing_areas.tif"
OUT_ABOVE_GROUND = ROOT / "data" / "orsa_stackmora_3_12_ythojd_above_ground.tif"
OUT_SUMMARY = ROOT / "data" / "orsa_stackmora_3_12_ythojd_summary.json"


def ythojd_root() -> Path | tempfile.TemporaryDirectory[str]:
    if (KARTOR_EXTRACT_DIR / "67_4" / "677_48_7500_2024_dsm.tif").exists():
        return KARTOR_EXTRACT_DIR
    temp = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(RAW_ZIP, "r") as archive:
        archive.extractall(temp.name)
    return temp


def source_paths(base: Path) -> dict[str, Path]:
    return {
        "dsm": base / "67_4" / "677_48_7500_2024_dsm.tif",
        "trueortho": base / "67_4" / "677_48_7500_2024_trueortho.tif",
        "class": base / "67_4" / "677_48_7500_2024_class.tif",
        "missing": base / "67_4" / "saknade_ytor" / "677_48_7500_2024.tif",
        "tile_metadata": base / "67_4" / "677_48_7500_2024.json",
        "delivery_metadata": base / "leverans.json",
    }


def workarea_shapes() -> list[dict[str, Any]]:
    data = json.loads(WORKAREA.read_text(encoding="utf-8"))
    return [feature["geometry"] for feature in data["features"]]


def clip_raster(src_path: Path, out_path: Path, shapes: list[dict[str, Any]]) -> dict[str, Any]:
    with rasterio.open(src_path) as src:
        raster_shapes = [transform_geom("EPSG:4326", src.crs, geom) for geom in shapes]
        out_image, out_transform = mask(src, raster_shapes, crop=True)
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=out_image.shape[1],
            width=out_image.shape[2],
            transform=out_transform,
            compress="deflate",
            predictor=2 if str(src.dtypes[0]).startswith("float") else 1,
        )
        for key in ["blockxsize", "blockysize", "tiled"]:
            profile.pop(key, None)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(out_image)
    return {
        "path": out_path.relative_to(ROOT).as_posix(),
        "source": src_path.as_posix(),
        "width": int(out_image.shape[2]),
        "height": int(out_image.shape[1]),
    }


def create_above_ground() -> dict[str, Any]:
    with rasterio.open(OUT_DSM) as dsm, rasterio.open(MARKHOJD) as dem:
        dsm_data = dsm.read(1, masked=True).astype("float32")
        dem_resampled = np.empty((dsm.height, dsm.width), dtype="float32")
        reproject(
            source=rasterio.band(dem, 1),
            destination=dem_resampled,
            src_transform=dem.transform,
            src_crs=dem.crs,
            src_nodata=dem.nodata,
            dst_transform=dsm.transform,
            dst_crs=dsm.crs,
            dst_nodata=-9999.0,
            resampling=Resampling.bilinear,
        )
        dem_mask = dem_resampled == -9999.0
        above = np.where(dsm_data.mask | dem_mask, -9999.0, np.asarray(dsm_data) - dem_resampled)
        profile = dsm.profile.copy()
        profile.update(dtype="float32", count=1, nodata=-9999.0, compress="deflate", predictor=2)
        with rasterio.open(OUT_ABOVE_GROUND, "w", **profile) as dst:
            dst.write(above.astype("float32"), 1)
        valid = above[above != -9999.0]
    return {
        "path": OUT_ABOVE_GROUND.relative_to(ROOT).as_posix(),
        "min_m": float(valid.min()) if valid.size else None,
        "max_m": float(valid.max()) if valid.size else None,
        "mean_m": float(valid.mean()) if valid.size else None,
    }


def sample_summary(path: Path) -> dict[str, Any]:
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        valid = data.compressed()
        return {
            "path": path.relative_to(ROOT).as_posix(),
            "crs": str(src.crs),
            "resolution": [float(src.res[0]), float(src.res[1])],
            "width": int(src.width),
            "height": int(src.height),
            "min": float(valid.min()) if valid.size else None,
            "max": float(valid.max()) if valid.size else None,
        }


def main() -> None:
    base_or_temp = ythojd_root()
    try:
        base = Path(base_or_temp.name) if isinstance(base_or_temp, tempfile.TemporaryDirectory) else base_or_temp
        paths = source_paths(base)
        shapes = workarea_shapes()
        outputs = {
            "dsm": clip_raster(paths["dsm"], OUT_DSM, shapes),
            "trueortho": clip_raster(paths["trueortho"], OUT_TRUEORTHO, shapes),
            "class": clip_raster(paths["class"], OUT_CLASS, shapes),
            "missing_areas": clip_raster(paths["missing"], OUT_MISSING, shapes),
        }
        outputs["above_ground"] = create_above_ground()

        tile_metadata = json.loads(paths["tile_metadata"].read_text(encoding="utf-8"))
        properties = tile_metadata["features"][0]["properties"]
        summary = {
            "raw_zip": RAW_ZIP.relative_to(ROOT).as_posix(),
            "kartor_extract_dir": str(KARTOR_EXTRACT_DIR),
            "source_tile": properties,
            "outputs": outputs,
            "dsm_stats": sample_summary(OUT_DSM),
            "above_ground_note": "DSM minus resampled markhojd. Use as first-pass support for tree/building surface heights, not as ground terrain.",
        }
        OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary["outputs"], ensure_ascii=False, indent=2))
    finally:
        if isinstance(base_or_temp, tempfile.TemporaryDirectory):
            base_or_temp.cleanup()


if __name__ == "__main__":
    main()
