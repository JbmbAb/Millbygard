import json
import argparse
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.ops import transform


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "topografi"
REFERENCE_DIR = ROOT / "04_references" / "topografi"

WORKAREA_GEOJSON = DATA_DIR / "orsa_stackmora_3_12_workarea.geojson"
TOPO_SELECTION = DATA_DIR / "orsa_stackmora_3_12_topografiska_kartor_selection.json"

DEFAULT_BUFFER_M = 500.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract roads and land cover around Millbygard from Topografiska kartor.")
    parser.add_argument(
        "--buffer-m",
        type=float,
        default=DEFAULT_BUFFER_M,
        help="Buffer around the Millbygard workarea in meters. Use 1000-2000 for local context.",
    )
    parser.add_argument(
        "--suffix",
        default=None,
        help="Optional output suffix. Defaults to e.g. 500m or 2km based on the buffer.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def topografi_delivery_folder() -> Path:
    selection = load_json(TOPO_SELECTION)
    folder = Path(selection["delivery_folder"])
    if not folder.exists():
        raise FileNotFoundError(f"Topografi delivery folder not found: {folder}")
    return folder


def source_gpkg_path(folder: Path, product_name: str) -> str:
    gpkg_name = f"{product_name}.gpkg"
    unpacked_path = folder / product_name / gpkg_name
    if unpacked_path.exists():
        return str(unpacked_path)

    zip_path = folder / f"{product_name}.zip"
    if zip_path.exists():
        return f"/vsizip/{zip_path}/{gpkg_name}"

    packed_zip_path = folder.parent / "_packade_zip_filer" / folder.name / f"{product_name}.zip"
    if packed_zip_path.exists():
        return f"/vsizip/{packed_zip_path}/{gpkg_name}"

    raise FileNotFoundError(f"Missing unpacked GPKG or ZIP for topografi product: {product_name}")


def workarea_3006():
    workarea = load_json(WORKAREA_GEOJSON)
    geometry = shape(workarea["features"][0]["geometry"])
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    return transform(transformer.transform, geometry)


def clipped_layer(src: str, layer: str, clip_box) -> gpd.GeoDataFrame:
    bbox = clip_box.bounds
    gdf = gpd.read_file(src, layer=layer, bbox=bbox, engine="pyogrio")
    if gdf.empty:
        return gdf
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:3006")
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.intersection(clip_box)
    gdf = gdf[~gdf.geometry.is_empty].copy()
    return gdf


def combine_layers(layers: list[gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    non_empty = [layer for layer in layers if not layer.empty]
    if not non_empty:
        crs = next((layer.crs for layer in layers if layer.crs is not None), "EPSG:3006")
        return gpd.GeoDataFrame(geometry=[], crs=crs)
    return gpd.GeoDataFrame(pd.concat(non_empty, ignore_index=True), crs=non_empty[0].crs)


def write_outputs(gdf: gpd.GeoDataFrame, name: str) -> dict[str, str | int]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gpkg_path = OUTPUT_DIR / f"{name}_3006.gpkg"
    geojson_path = OUTPUT_DIR / f"{name}.geojson"

    if gpkg_path.exists():
        gpkg_path.unlink()
    gdf.to_file(gpkg_path, driver="GPKG", layer=name, engine="pyogrio")

    wgs84 = gdf.to_crs("EPSG:4326")
    wgs84.to_file(geojson_path, driver="GeoJSON", engine="pyogrio")

    return {
        "feature_count": int(len(gdf)),
        "gpkg_3006": str(gpkg_path),
        "geojson_wgs84": str(geojson_path),
    }


def write_root_geojson(gdf: gpd.GeoDataFrame, path: Path) -> dict[str, str | int]:
    if path.exists():
        path.unlink()
    if gdf.empty:
        gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    gdf.to_file(path, driver="GeoJSON", engine="pyogrio")
    return {"feature_count": int(len(gdf)), "geojson_wgs84": str(path)}


def summarize_values(gdf: gpd.GeoDataFrame, column: str) -> dict[str, int]:
    if column not in gdf.columns or gdf.empty:
        return {}
    counts = gdf[column].fillna("(tomt)").astype(str).value_counts()
    return {key: int(value) for key, value in counts.items()}


def write_preview_svg(roads: gpd.GeoDataFrame, land: gpd.GeoDataFrame, clip_box, suffix: str) -> Path:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = REFERENCE_DIR / f"orsa_stackmora_3_12_topografi_mark_vagar_{suffix}_preview.svg"
    width, height = 1200, 900
    minx, miny, maxx, maxy = clip_box.bounds

    def project(x: float, y: float) -> tuple[float, float]:
        px = (x - minx) / (maxx - minx) * width
        py = height - ((y - miny) / (maxy - miny) * height)
        return px, py

    def geom_to_paths(geom) -> list[str]:
        if geom.is_empty:
            return []
        if geom.geom_type == "LineString":
            coords = list(geom.coords)
            return [coords_to_path(coords, close=False)]
        if geom.geom_type == "MultiLineString":
            return [coords_to_path(list(part.coords), close=False) for part in geom.geoms]
        if geom.geom_type == "Polygon":
            return [coords_to_path(list(geom.exterior.coords), close=True)]
        if geom.geom_type == "MultiPolygon":
            return [coords_to_path(list(part.exterior.coords), close=True) for part in geom.geoms]
        return []

    def coords_to_path(coords, close: bool) -> str:
        parts = []
        for index, (x, y) in enumerate(coords):
            px, py = project(x, y)
            parts.append(("M" if index == 0 else "L") + f"{px:.1f},{py:.1f}")
        if close:
            parts.append("Z")
        return " ".join(parts)

    elements = [f'<rect width="{width}" height="{height}" fill="#f4f2e8"/>']

    for _, row in land.iterrows():
        land_type = str(row.get("objekttyp", ""))
        if "Skog" in land_type:
            style = 'fill="#4f8b5f" fill-opacity="0.45" stroke="#2f5d3b" stroke-width="0.8"'
        elif "Öppen" in land_type or "Oppen" in land_type:
            style = 'fill="#cadc96" fill-opacity="0.48" stroke="#7d904b" stroke-width="0.8"'
        else:
            style = 'fill="#dad6b8" fill-opacity="0.36" stroke="#938b66" stroke-width="0.7"'
        for d in geom_to_paths(row.geometry):
            elements.append(f'<path d="{d}" {style}/>')

    for _, row in roads.iterrows():
        road_type = str(row.get("objekttyp", ""))
        width_px = "4.2" if "Landsväg" in road_type or "Landsvag" in road_type else "2.2"
        for d in geom_to_paths(row.geometry):
            elements.append(
                f'<path d="{d}" fill="none" stroke="#f7f0d5" stroke-width="{width_px}" stroke-linecap="round" stroke-linejoin="round"/>'
            )
            elements.append(
                f'<path d="{d}" fill="none" stroke="#4b4736" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round" opacity="0.55"/>'
            )

    workarea = workarea_3006()
    for d in geom_to_paths(workarea):
        elements.append(f'<path d="{d}" fill="none" stroke="#d62728" stroke-width="2.5" stroke-dasharray="8 5"/>')

    elements.append(
        '<g transform="translate(24,24)">'
        '<rect x="0" y="0" width="390" height="110" fill="white" fill-opacity="0.88" stroke="#b7b7a4"/>'
        '<text x="16" y="28" font-family="Arial" font-size="18" fill="#222">Millbygard topografi-utkast</text>'
        '<text x="16" y="54" font-family="Arial" font-size="14" fill="#333">Kalla: Lantmateriet Topografiska kartor</text>'
        '<text x="16" y="78" font-family="Arial" font-size="13" fill="#555">Gront = mark, ljust = vag, rott = fastighetsyta</text>'
        "</g>"
    )

    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        + "\n".join(elements)
        + "\n</svg>\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    args = parse_args()
    buffer_m = args.buffer_m
    suffix = args.suffix or (f"{int(buffer_m / 1000)}km" if buffer_m >= 1000 and buffer_m % 1000 == 0 else f"{int(buffer_m)}m")

    folder = topografi_delivery_folder()
    communication_src = source_gpkg_path(folder, "kommunikation_sverige")
    land_src = source_gpkg_path(folder, "mark_sverige")
    buildings_src = source_gpkg_path(folder, "byggnadsverk_sverige")
    hydro_src = source_gpkg_path(folder, "hydrografi_sverige")
    text_src = source_gpkg_path(folder, "text_sverige")

    area = workarea_3006()
    minx, miny, maxx, maxy = area.bounds
    clip_box = box(minx - buffer_m, miny - buffer_m, maxx + buffer_m, maxy + buffer_m)

    roads = combine_layers([
        clipped_layer(communication_src, "vaglinje", clip_box),
        clipped_layer(communication_src, "ovrig_vag", clip_box),
        clipped_layer(communication_src, "vagpunkt", clip_box),
    ])

    land = combine_layers([
        clipped_layer(land_src, "mark", clip_box),
        clipped_layer(land_src, "sankmark", clip_box),
        clipped_layer(land_src, "markkantlinje", clip_box),
        clipped_layer(land_src, "markframkomlighet", clip_box),
    ])

    buildings = combine_layers([
        clipped_layer(buildings_src, "byggnad", clip_box),
        clipped_layer(buildings_src, "byggnadspunkt", clip_box),
        clipped_layer(buildings_src, "byggnadsanlaggningslinje", clip_box),
        clipped_layer(buildings_src, "byggnadsanlaggningspunkt", clip_box),
    ])
    building_focus_area = area.buffer(10)
    buildings_workarea = combine_layers([
        clipped_layer(buildings_src, "byggnad", building_focus_area),
        clipped_layer(buildings_src, "byggnadspunkt", building_focus_area),
        clipped_layer(buildings_src, "byggnadsanlaggningslinje", building_focus_area),
        clipped_layer(buildings_src, "byggnadsanlaggningspunkt", building_focus_area),
    ])

    hydro = combine_layers([
        clipped_layer(hydro_src, "hydrolinje", clip_box),
        clipped_layer(hydro_src, "hydropunkt", clip_box),
        clipped_layer(hydro_src, "hydrografiskt_intressant_plats", clip_box),
        clipped_layer(hydro_src, "hydroanlaggningslinje", clip_box),
        clipped_layer(hydro_src, "hydroanlaggningspunkt", clip_box),
    ])

    text = combine_layers([
        clipped_layer(text_src, "textpunkt", clip_box),
        clipped_layer(text_src, "textlinje", clip_box),
    ])

    roads_output = write_outputs(roads, f"orsa_stackmora_3_12_topografi_vagar_{suffix}")
    land_output = write_outputs(land, f"orsa_stackmora_3_12_topografi_mark_{suffix}")
    buildings_output = write_outputs(buildings, f"orsa_stackmora_3_12_topografi_byggnadsverk_{suffix}")
    buildings_workarea_output = write_root_geojson(buildings_workarea, DATA_DIR / "orsa_stackmora_3_12_byggnader.geojson")
    hydro_output = write_outputs(hydro, f"orsa_stackmora_3_12_topografi_hydrografi_{suffix}")
    text_output = write_outputs(text, f"orsa_stackmora_3_12_topografi_text_{suffix}")
    preview_path = write_preview_svg(roads, land, clip_box, suffix)

    manifest = {
        "project": "Millbygard",
        "source": "Lantmateriet Topografiska kartor",
        "delivery_folder": str(folder),
        "crs_working": "EPSG:3006",
        "buffer_m": buffer_m,
        "clip_bbox_3006": {
            "minx": clip_box.bounds[0],
            "miny": clip_box.bounds[1],
            "maxx": clip_box.bounds[2],
            "maxy": clip_box.bounds[3],
        },
        "building_focus_buffer_m": 10,
        "outputs": {
            "roads": roads_output,
            "land": land_output,
            "buildings": buildings_output,
            "buildings_workarea": buildings_workarea_output,
            "hydro": hydro_output,
            "text": text_output,
            "preview_svg": str(preview_path),
        },
        "summaries": {
            "roads_objekttyp": summarize_values(roads, "objekttyp"),
            "land_objekttyp": summarize_values(land, "objekttyp"),
            "buildings_objekttyp": summarize_values(buildings, "objekttyp"),
            "hydro_objekttyp": summarize_values(hydro, "objekttyp"),
            "text_text": summarize_values(text, "text"),
        },
        "notes": [
            "This is the preferred first draft for roads and land around Millbygard.",
            "Use these layers before the OpenStreetMap fallback.",
            "Later refine with newer Topografi 10 or other product-specific deliveries if needed.",
        ],
    }
    manifest_path = OUTPUT_DIR / f"orsa_stackmora_3_12_topografi_context_{suffix}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Sparade vägar: {roads_output['geojson_wgs84']} ({roads_output['feature_count']} features)")
    print(f"Sparade mark: {land_output['geojson_wgs84']} ({land_output['feature_count']} features)")
    print(f"Sparade byggnadsverk: {buildings_output['geojson_wgs84']} ({buildings_output['feature_count']} features)")
    print(f"Sparade byggnader i workarea: {buildings_workarea_output['geojson_wgs84']} ({buildings_workarea_output['feature_count']} features)")
    print(f"Sparade hydrografi: {hydro_output['geojson_wgs84']} ({hydro_output['feature_count']} features)")
    print(f"Sparade text: {text_output['geojson_wgs84']} ({text_output['feature_count']} features)")
    print(f"Sparade preview: {preview_path}")
    print(f"Sparade manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
