from __future__ import annotations

import json
import math
import os
from importlib.util import find_spec
from pathlib import Path
from typing import Iterable

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
from affine import Affine
from pyproj import Transformer
from rasterio.features import MergeAlg, rasterize
from rasterio.windows import Window, from_bounds
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform as shapely_transform
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
ORTHO_PATH = ROOT / "01_data_raw" / "ortofoto" / "orsa_stackmora_3_12_ortofoto_highres.tif"
WORKAREA_PATH = ROOT / "data" / "orsa_stackmora_3_12_workarea.geojson"
CIRCLE_PATH = ROOT / "data" / "orsa_stackmora_3_12_workarea_circle.geojson"
TOWER_PATH = ROOT / "data" / "orsa_stackmora_3_12_tower_site.geojson"
PHOTO_POINTS_PATH = ROOT / "output" / "foton_geotaggar_alla.geojson"
OUT_PATH = ROOT / "output" / "photo_review" / "photo_coverage_map_20260416.png"
OUT_METADATA_PATH = ROOT / "output" / "photo_review" / "photo_coverage_map_20260416_metadata.json"

TARGET_CRS = "EPSG:3006"
OUTPUT_MAX_PX = 1800
MAP_MARGIN_M = 25
COVERAGE_DISTANCE_M = 55
COVERAGE_HALF_ANGLE_DEG = 37.5
COVERAGE_MIN_OVERLAP = 2
DIRECTION_LINE_LENGTH_M = 22

WGS84_TO_TARGET = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)


def load_geojson(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def project_geometry(geometry):
    return shapely_transform(WGS84_TO_TARGET.transform, geometry)


def feature_geometries(path: Path):
    return [shape(feature["geometry"]) for feature in load_geojson(path)["features"]]


def geometry_bounds_with_margin(geometry, margin_m: float) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = geometry.bounds
    return minx - margin_m, miny - margin_m, maxx + margin_m, maxy + margin_m


def output_shape_for_window(window: Window) -> tuple[int, int]:
    width = float(window.width)
    height = float(window.height)
    scale = min(OUTPUT_MAX_PX / width, OUTPUT_MAX_PX / height, 1.0)
    return max(1, round(height * scale)), max(1, round(width * scale))


def read_ortho_crop(path: Path, bounds: tuple[float, float, float, float]):
    with rasterio.open(path) as src:
        raw_window = from_bounds(*bounds, transform=src.transform)
        full = Window(0, 0, src.width, src.height)
        window = raw_window.round_offsets().round_lengths().intersection(full)
        out_height, out_width = output_shape_for_window(window)
        indexes = [1, 2, 3] if src.count >= 3 else [1]
        data = src.read(indexes=indexes, window=window, out_shape=(len(indexes), out_height, out_width))
        transform = src.window_transform(window) * Affine.scale(window.width / out_width, window.height / out_height)

    if data.shape[0] == 1:
        image = np.repeat(data, 3, axis=0)
    else:
        image = data[:3]

    if image.dtype != np.uint8:
        converted = np.zeros_like(image, dtype=np.uint8)
        for band_index in range(3):
            band = image[band_index].astype("float32")
            valid = band[np.isfinite(band)]
            if valid.size:
                low, high = np.percentile(valid, [2, 98])
                if high <= low:
                    high = low + 1
                band = np.clip((band - low) / (high - low), 0, 1) * 255
            converted[band_index] = band.astype(np.uint8)
        image = converted

    return np.moveaxis(image, 0, -1).copy(), transform


def raster_mask(geometries: Iterable, shape_: tuple[int, int], transform, value=1, dtype="uint8"):
    return rasterize(
        ((geom, value) for geom in geometries if not geom.is_empty),
        out_shape=shape_,
        transform=transform,
        fill=0,
        dtype=dtype,
        all_touched=True,
    )


def alpha_blend(image: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], alpha: float) -> None:
    selected = mask.astype(bool)
    if not selected.any():
        return
    color_array = np.array(color, dtype=np.float32)
    image[selected] = (image[selected].astype(np.float32) * (1 - alpha) + color_array * alpha).astype(np.uint8)


def directional_sector(point: Point, bearing_deg: float, distance_m: float, half_angle_deg: float):
    coords = [(point.x, point.y)]
    start = bearing_deg - half_angle_deg
    end = bearing_deg + half_angle_deg
    steps = 12
    for i in range(steps + 1):
        angle_deg = start + (end - start) * i / steps
        angle_rad = math.radians(angle_deg)
        x = point.x + math.sin(angle_rad) * distance_m
        y = point.y + math.cos(angle_rad) * distance_m
        coords.append((x, y))
    coords.append((point.x, point.y))
    return shape({"type": "Polygon", "coordinates": [coords]})


def load_photo_points_and_sectors():
    photo_points = []
    sectors = []
    direction_lines = []
    for feature in load_geojson(PHOTO_POINTS_PATH)["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        point = project_geometry(Point(lon, lat))
        photo_points.append(point)
        direction = feature.get("properties", {}).get("direction_deg")
        if direction is None:
            continue
        sector = directional_sector(
            point,
            float(direction),
            COVERAGE_DISTANCE_M,
            COVERAGE_HALF_ANGLE_DEG,
        )
        sectors.append(sector)
        bearing_rad = math.radians(float(direction))
        end = (
            point.x + math.sin(bearing_rad) * DIRECTION_LINE_LENGTH_M,
            point.y + math.cos(bearing_rad) * DIRECTION_LINE_LENGTH_M,
        )
        direction_lines.append(LineString([(point.x, point.y), end]))
    return photo_points, sectors, direction_lines


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    workarea = unary_union([project_geometry(geom) for geom in feature_geometries(WORKAREA_PATH)])
    circle = project_geometry(feature_geometries(CIRCLE_PATH)[0])
    tower = project_geometry(feature_geometries(TOWER_PATH)[0])
    photo_points, sectors, direction_lines = load_photo_points_and_sectors()

    bounds = geometry_bounds_with_margin(circle, MAP_MARGIN_M)
    image, transform = read_ortho_crop(ORTHO_PATH, bounds)
    height, width = image.shape[:2]
    shape_ = (height, width)

    clipped_sectors = [sector.intersection(workarea) for sector in sectors]
    sector_count = rasterize(
        ((geom, 1) for geom in clipped_sectors if not geom.is_empty),
        out_shape=shape_,
        transform=transform,
        fill=0,
        dtype="uint16",
        merge_alg=MergeAlg.add,
        all_touched=True,
    )
    coverage_mask = sector_count >= COVERAGE_MIN_OVERLAP
    alpha_blend(image, coverage_mask, (46, 190, 76), 0.48)

    alpha_blend(image, raster_mask([line.buffer(0.55) for line in direction_lines], shape_, transform), (255, 255, 255), 0.70)

    photo_masks = [point.buffer(2.5) for point in photo_points]
    alpha_blend(image, raster_mask(photo_masks, shape_, transform), (255, 223, 64), 0.95)

    alpha_blend(image, raster_mask([circle.boundary.buffer(1.1)], shape_, transform), (25, 185, 255), 0.95)
    alpha_blend(image, raster_mask([workarea.boundary.buffer(1.4)], shape_, transform), (255, 32, 32), 0.98)
    alpha_blend(image, raster_mask([tower.buffer(4.5)], shape_, transform), (255, 0, 220), 0.98)

    with rasterio.open(
        OUT_PATH,
        "w",
        driver="PNG",
        height=height,
        width=width,
        count=3,
        dtype="uint8",
    ) as dst:
        dst.write(np.moveaxis(image, -1, 0))

    metadata = {
        "output": OUT_PATH.relative_to(ROOT).as_posix(),
        "base_ortho": ORTHO_PATH.relative_to(ROOT).as_posix(),
        "workarea_boundary": WORKAREA_PATH.relative_to(ROOT).as_posix(),
        "coverage_circle": CIRCLE_PATH.relative_to(ROOT).as_posix(),
        "tower_site": TOWER_PATH.relative_to(ROOT).as_posix(),
        "photo_points": PHOTO_POINTS_PATH.relative_to(ROOT).as_posix(),
        "legend": {
            "green": f"Area inside property seen by at least {COVERAGE_MIN_OVERLAP} camera direction sectors.",
            "red": "Property boundary.",
            "cyan": "Whole-property coverage circle.",
            "yellow": "Camera GPS points.",
            "white": "Approximate camera view directions.",
            "magenta": "Tower site / highest DEM point.",
        },
        "coverage_distance_m": COVERAGE_DISTANCE_M,
        "coverage_half_angle_deg": COVERAGE_HALF_ANGLE_DEG,
        "photo_points_count": len(photo_points),
        "direction_sector_count": len(sectors),
        "direction_line_length_m": DIRECTION_LINE_LENGTH_M,
    }
    OUT_METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_PATH)


if __name__ == "__main__":
    main()
