import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
EXPORTS_DIR = ROOT / "exports"

SPLIT_GEOJSON = DATA_DIR / "orsa_stackmora_3_12_split.geojson"
WORKAREA_GEOJSON = DATA_DIR / "orsa_stackmora_3_12_workarea.geojson"

EARTH_RADIUS_M = 6378137.0


def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ring_area_square_meters(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0

    total = 0.0
    for index in range(len(points)):
        x1, y1 = points[index]
        x2, y2 = points[(index + 1) % len(points)]
        total += (x1 * y2) - (x2 * y1)
    return abs(total) / 2.0


def lon_lat_to_local_meters(
    lon: float,
    lat: float,
    origin_lon: float,
    origin_lat: float,
) -> tuple[float, float]:
    lat0_rad = math.radians(origin_lat)
    x = EARTH_RADIUS_M * math.radians(lon - origin_lon) * math.cos(lat0_rad)
    z = EARTH_RADIUS_M * math.radians(lat - origin_lat)
    return x, z


def extract_polygon_rings(geometry: dict) -> list[list[list[float]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        return coordinates

    if geometry_type == "MultiPolygon":
        rings: list[list[list[float]]] = []
        for polygon in coordinates:
            rings.extend(polygon)
        return rings

    raise ValueError(f"Unsupported geometry type: {geometry_type}")


def main() -> None:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    split_data = load_geojson(SPLIT_GEOJSON)
    workarea_data = load_geojson(WORKAREA_GEOJSON)

    workarea_feature = workarea_data["features"][0]
    origin_lon, origin_lat = workarea_feature["geometry"]["coordinates"][0][0][0]

    parcel_exports = []
    summary_rows = []

    for feature in split_data["features"]:
        designation = feature["properties"]["designation"]
        rings = extract_polygon_rings(feature["geometry"])

        local_rings = []
        largest_area = 0.0
        largest_ring = []

        for ring in rings:
            local_ring = []
            for lon, lat in ring:
                x, z = lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat)
                local_ring.append(
                    {
                        "lon": lon,
                        "lat": lat,
                        "x_m": round(x, 3),
                        "z_m": round(z, 3),
                        "x_block": int(round(x)),
                        "z_block": int(round(z)),
                    }
                )

            local_rings.append(local_ring)

            planar_points = [(point["x_m"], point["z_m"]) for point in local_ring]
            area = ring_area_square_meters(planar_points[:-1] if planar_points[0] == planar_points[-1] else planar_points)
            if area > largest_area:
                largest_area = area
                largest_ring = local_ring

        x_values = [point["x_m"] for ring in local_rings for point in ring]
        z_values = [point["z_m"] for ring in local_rings for point in ring]

        parcel_export = {
            "designation": designation,
            "municipality_name": feature["properties"]["municipalityName"],
            "source_dataset": feature["properties"]["sourceDataset"],
            "centroid_wkt": feature["properties"]["centroidWkt"],
            "area_sqm_from_source": feature["properties"]["areaSqm"],
            "bbox_local_m": {
                "min_x": round(min(x_values), 3),
                "max_x": round(max(x_values), 3),
                "min_z": round(min(z_values), 3),
                "max_z": round(max(z_values), 3),
            },
            "largest_ring_local": largest_ring,
            "all_rings_local": local_rings,
        }
        parcel_exports.append(parcel_export)

        summary_rows.append(
            {
                "designation": designation,
                "source_area_sqm": feature["properties"]["areaSqm"],
                "derived_area_sqm": round(largest_area, 2),
                "bbox_width_m": round(max(x_values) - min(x_values), 2),
                "bbox_depth_m": round(max(z_values) - min(z_values), 2),
            }
        )

    export_payload = {
        "project": "Millbygard",
        "source": "PostGIS-derived local exports",
        "coordinate_basis": {
            "origin_note": "Origin is the first coordinate of the workarea geometry.",
            "origin_lon": origin_lon,
            "origin_lat": origin_lat,
            "scale_note": "1 block = 1 meter suggested.",
            "axis_note": "x increases east, z increases north.",
        },
        "parcels": parcel_exports,
    }

    local_json_path = EXPORTS_DIR / "millbygard_local_parcels.json"
    summary_json_path = EXPORTS_DIR / "millbygard_parcel_summary.json"
    summary_md_path = EXPORTS_DIR / "millbygard_parcel_summary.md"

    local_json_path.write_text(json.dumps(export_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_json_path.write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Millbygård: Parcel Summary",
        "",
        "Detta underlag är beräknat från lokala GeoJSON-exporter.",
        "",
        f"Origin lon/lat: `{origin_lon}`, `{origin_lat}`",
        "",
        "| Designation | Source area sqm | Derived area sqm | Width m | Depth m |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['designation']} | {row['source_area_sqm']} | {row['derived_area_sqm']} | {row['bbox_width_m']} | {row['bbox_depth_m']} |"
        )

    summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote: {local_json_path}")
    print(f"Wrote: {summary_json_path}")
    print(f"Wrote: {summary_md_path}")


if __name__ == "__main__":
    main()
