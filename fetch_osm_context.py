import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OSM_DIR = DATA_DIR / "osm"
REFERENCE_DIR = ROOT / "04_references" / "osm"

WORKAREA_GEOJSON = DATA_DIR / "orsa_stackmora_3_12_workarea.geojson"
ROADS_GEOJSON = OSM_DIR / "orsa_stackmora_3_12_osm_roads.geojson"
LANDCOVER_GEOJSON = OSM_DIR / "orsa_stackmora_3_12_osm_landcover.geojson"
MANIFEST_JSON = OSM_DIR / "orsa_stackmora_3_12_osm_context_manifest.json"
PREVIEW_SVG = REFERENCE_DIR / "orsa_stackmora_3_12_osm_roads_landcover_preview.svg"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

BUFFER_DEGREES = 0.012


def load_geojson(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_lon_lat_pairs(geometry: dict[str, Any]):
    coordinates = geometry.get("coordinates", [])
    geometry_type = geometry.get("type")
    if geometry_type == "Polygon":
        for ring in coordinates:
            for lon, lat in ring:
                yield lon, lat
    elif geometry_type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                for lon, lat in ring:
                    yield lon, lat
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")


def workarea_bbox() -> tuple[float, float, float, float]:
    workarea = load_geojson(WORKAREA_GEOJSON)
    points = list(iter_lon_lat_pairs(workarea["features"][0]["geometry"]))
    min_lon = min(lon for lon, _ in points)
    min_lat = min(lat for _, lat in points)
    max_lon = max(lon for lon, _ in points)
    max_lat = max(lat for _, lat in points)
    return (
        min_lon - BUFFER_DEGREES,
        min_lat - BUFFER_DEGREES,
        max_lon + BUFFER_DEGREES,
        max_lat + BUFFER_DEGREES,
    )


def overpass_query(bbox: tuple[float, float, float, float]) -> str:
    west, south, east, north = bbox
    return f"""
[out:json][timeout:90];
(
  way["highway"]({south},{west},{north},{east});
  way["landuse"]({south},{west},{north},{east});
  way["natural"]({south},{west},{north},{east});
  way["leisure"]({south},{west},{north},{east});
  way["amenity"="grave_yard"]({south},{west},{north},{east});
  way["waterway"]({south},{west},{north},{east});
);
out geom;
"""


def fetch_overpass(query: str) -> dict[str, Any]:
    body = urllib.parse.urlencode({"data": query}).encode("utf-8")
    last_error: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        request = urllib.request.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Millbygard-osm-context/0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Overpass request failed: {last_error}")


def make_feature(element: dict[str, Any]) -> dict[str, Any] | None:
    geometry = element.get("geometry") or []
    if len(geometry) < 2:
        return None

    coords = [[point["lon"], point["lat"]] for point in geometry]
    is_closed = coords[0] == coords[-1]
    tags = element.get("tags", {})
    has_area_tag = any(key in tags for key in ("landuse", "natural", "leisure", "amenity"))

    if is_closed and has_area_tag:
        geom = {"type": "Polygon", "coordinates": [coords]}
    else:
        geom = {"type": "LineString", "coordinates": coords}

    return {
        "type": "Feature",
        "geometry": geom,
        "properties": {
            "osm_type": element.get("type"),
            "osm_id": element.get("id"),
            **tags,
        },
    }


def split_features(overpass_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    roads = []
    landcover = []

    for element in overpass_data.get("elements", []):
        feature = make_feature(element)
        if not feature:
            continue
        properties = feature["properties"]
        if "highway" in properties or "waterway" in properties:
            roads.append(feature)
        if any(key in properties for key in ("landuse", "natural", "leisure", "amenity")):
            landcover.append(feature)

    return roads, landcover


def write_geojson(path: Path, features: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "name": path.stem,
        "features": features,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def project(lon: float, lat: float, bbox: tuple[float, float, float, float], width: int, height: int) -> tuple[float, float]:
    west, south, east, north = bbox
    x = (lon - west) / (east - west) * width
    y = height - ((lat - south) / (north - south) * height)
    return x, y


def path_data_for_geometry(geometry: dict[str, Any], bbox: tuple[float, float, float, float], width: int, height: int) -> str:
    geometry_type = geometry["type"]
    if geometry_type == "LineString":
        coords = geometry["coordinates"]
    elif geometry_type == "Polygon":
        coords = geometry["coordinates"][0]
    else:
        return ""
    parts = []
    for index, (lon, lat) in enumerate(coords):
        x, y = project(lon, lat, bbox, width, height)
        command = "M" if index == 0 else "L"
        parts.append(f"{command}{x:.1f},{y:.1f}")
    if geometry_type == "Polygon":
        parts.append("Z")
    return " ".join(parts)


def svg_style(properties: dict[str, Any], geometry_type: str) -> str:
    if "highway" in properties:
        highway = properties.get("highway")
        width = {"primary": 4, "secondary": 3, "tertiary": 2.5, "residential": 2, "service": 1.6, "track": 1.4}.get(highway, 1.2)
        return f'fill="none" stroke="#f7f0d5" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'
    if "waterway" in properties:
        return 'fill="none" stroke="#3a8ec8" stroke-width="1.4" stroke-linecap="round"'
    if geometry_type == "Polygon":
        if properties.get("landuse") == "forest" or properties.get("natural") == "wood":
            return 'fill="#4f8b5f" fill-opacity="0.42" stroke="#2f5d3b" stroke-width="0.7"'
        if properties.get("landuse") in {"farmland", "meadow", "grass"} or properties.get("natural") in {"grassland", "scrub"}:
            return 'fill="#c6d88d" fill-opacity="0.45" stroke="#7b8f45" stroke-width="0.7"'
        if properties.get("natural") == "water" or properties.get("waterway"):
            return 'fill="#73aeda" fill-opacity="0.55" stroke="#2f79a8" stroke-width="0.7"'
        return 'fill="#d7d7c4" fill-opacity="0.32" stroke="#8b8b78" stroke-width="0.6"'
    return 'fill="none" stroke="#767676" stroke-width="1"'


def write_preview_svg(
    path: Path,
    bbox: tuple[float, float, float, float],
    roads: list[dict[str, Any]],
    landcover: list[dict[str, Any]],
) -> None:
    width, height = 1200, 900
    workarea = load_geojson(WORKAREA_GEOJSON)
    paths = [
        f'<rect width="{width}" height="{height}" fill="#f4f2e8"/>',
    ]

    for feature in landcover:
        path_data = path_data_for_geometry(feature["geometry"], bbox, width, height)
        if path_data:
            paths.append(f'<path d="{path_data}" {svg_style(feature["properties"], feature["geometry"]["type"])}/>')

    for feature in roads:
        path_data = path_data_for_geometry(feature["geometry"], bbox, width, height)
        if path_data:
            paths.append(f'<path d="{path_data}" {svg_style(feature["properties"], feature["geometry"]["type"])}/>')

    for feature in workarea["features"]:
        geometry = feature["geometry"]
        for polygon in geometry["coordinates"]:
            for ring in polygon:
                path_data = path_data_for_geometry({"type": "Polygon", "coordinates": [ring]}, bbox, width, height)
                paths.append(f'<path d="{path_data}" fill="none" stroke="#d62728" stroke-width="2.2" stroke-dasharray="8 5"/>')

    legend = (
        '<g transform="translate(24,24)">'
        '<rect x="0" y="0" width="360" height="104" fill="white" fill-opacity="0.86" stroke="#b7b7a4"/>'
        '<text x="16" y="28" font-family="Arial" font-size="18" fill="#222">Millbygard OSM-utkast</text>'
        '<text x="16" y="54" font-family="Arial" font-size="14" fill="#333">Gult/vitt = vagar, gront = mark, rott = fastighetsyta</text>'
        '<text x="16" y="78" font-family="Arial" font-size="13" fill="#555">Kalla: OpenStreetMap contributors, ODbL. Utkast.</text>'
        "</g>"
    )
    paths.append(legend)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        + "\n".join(paths)
        + "\n</svg>\n",
        encoding="utf-8",
    )


def main() -> int:
    bbox = workarea_bbox()
    query = overpass_query(bbox)
    overpass_data = fetch_overpass(query)
    roads, landcover = split_features(overpass_data)

    write_geojson(ROADS_GEOJSON, roads)
    write_geojson(LANDCOVER_GEOJSON, landcover)
    write_preview_svg(PREVIEW_SVG, bbox, roads, landcover)

    highway_counts: dict[str, int] = {}
    landcover_counts: dict[str, int] = {}
    for feature in roads:
        value = feature["properties"].get("highway") or feature["properties"].get("waterway") or "other"
        highway_counts[value] = highway_counts.get(value, 0) + 1
    for feature in landcover:
        for key in ("landuse", "natural", "leisure", "amenity"):
            if key in feature["properties"]:
                value = f"{key}={feature['properties'][key]}"
                landcover_counts[value] = landcover_counts.get(value, 0) + 1
                break

    manifest = {
        "project": "Millbygard",
        "source": "OpenStreetMap Overpass API",
        "license": "Open Database License (ODbL); attribution required: OpenStreetMap contributors",
        "usage_note": "Draft context for roads and land cover around the farm. Replace/refine with Lantmateriet Topografi/Marktacke when available.",
        "bbox_wgs84": {
            "west": bbox[0],
            "south": bbox[1],
            "east": bbox[2],
            "north": bbox[3],
            "buffer_degrees": BUFFER_DEGREES,
        },
        "outputs": {
            "roads_geojson": str(ROADS_GEOJSON),
            "landcover_geojson": str(LANDCOVER_GEOJSON),
            "preview_svg": str(PREVIEW_SVG),
        },
        "feature_counts": {
            "roads": len(roads),
            "landcover": len(landcover),
            "highway_or_waterway_by_type": dict(sorted(highway_counts.items())),
            "landcover_by_type": dict(sorted(landcover_counts.items())),
        },
        "overpass_query": query.strip(),
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Sparade vagar: {ROADS_GEOJSON} ({len(roads)} features)")
    print(f"Sparade mark: {LANDCOVER_GEOJSON} ({len(landcover)} features)")
    print(f"Sparade preview: {PREVIEW_SVG}")
    print(f"Sparade manifest: {MANIFEST_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
