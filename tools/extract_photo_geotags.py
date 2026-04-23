from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from struct import unpack_from
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHOTO_DIR = ROOT / "Foton"
DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_DIRECTION_LENGTH_M = 20.0

GPS_TAGS = {
    1: "GPSLatitudeRef",
    2: "GPSLatitude",
    3: "GPSLongitudeRef",
    4: "GPSLongitude",
    5: "GPSAltitudeRef",
    6: "GPSAltitude",
    7: "GPSTimeStamp",
    16: "GPSImgDirectionRef",
    17: "GPSImgDirection",
    29: "GPSDateStamp",
}

IFD_TAGS = {
    0x010F: "Make",
    0x0110: "Model",
    0x0112: "Orientation",
    0x0132: "DateTime",
    0x8769: "ExifIFDPointer",
    0x8825: "GPSInfoIFDPointer",
}

EXIF_TAGS = {
    0x829A: "ExposureTime",
    0x829D: "FNumber",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x920A: "FocalLength",
}

TYPE_SIZES = {
    1: 1,  # BYTE
    2: 1,  # ASCII
    3: 2,  # SHORT
    4: 4,  # LONG
    5: 8,  # RATIONAL
    7: 1,  # UNDEFINED
    9: 4,  # SLONG
    10: 8,  # SRATIONAL
}


def find_exif_segment(path: Path) -> bytes | None:
    data = path.read_bytes()
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None

    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            break
        marker = data[offset + 1]
        offset += 2
        if marker in (0xD9, 0xDA):
            break
        if offset + 2 > len(data):
            break
        segment_length = int.from_bytes(data[offset : offset + 2], "big")
        segment_start = offset + 2
        segment_end = offset + segment_length
        if marker == 0xE1 and data[segment_start : segment_start + 6] == b"Exif\0\0":
            return data[segment_start + 6 : segment_end]
        offset = segment_end
    return None


def read_ascii(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("utf-8", errors="replace").strip()


def rational_to_float(value: tuple[int, int] | tuple[int, int, int, int]) -> float | None:
    if len(value) == 2:
        numerator, denominator = value
    else:
        numerator, denominator = value[0], value[1]
    if denominator == 0:
        return None
    return numerator / denominator


def decode_value(
    tiff: bytes,
    endian: str,
    tiff_base: int,
    value_type: int,
    count: int,
    value_or_offset: bytes,
) -> Any:
    type_size = TYPE_SIZES.get(value_type)
    if type_size is None:
        return None

    total_size = type_size * count
    if total_size <= 4:
        value_data = value_or_offset[:total_size]
    else:
        value_offset = int.from_bytes(value_or_offset, "little" if endian == "<" else "big")
        start = tiff_base + value_offset
        value_data = tiff[start : start + total_size]

    if value_type == 2:
        return read_ascii(value_data)
    if value_type == 3:
        fmt = endian + f"{count}H"
        values = unpack_from(fmt, value_data)
        return values[0] if count == 1 else list(values)
    if value_type == 4:
        fmt = endian + f"{count}I"
        values = unpack_from(fmt, value_data)
        return values[0] if count == 1 else list(values)
    if value_type == 5:
        values = []
        for idx in range(count):
            numerator, denominator = unpack_from(endian + "II", value_data, idx * 8)
            values.append((numerator, denominator))
        return values[0] if count == 1 else values
    if value_type == 9:
        fmt = endian + f"{count}i"
        values = unpack_from(fmt, value_data)
        return values[0] if count == 1 else list(values)
    if value_type == 10:
        values = []
        for idx in range(count):
            numerator, denominator = unpack_from(endian + "ii", value_data, idx * 8)
            values.append((numerator, denominator))
        return values[0] if count == 1 else values
    if value_type in (1, 7):
        return value_data[0] if count == 1 else list(value_data)
    return None


def parse_ifd(
    tiff: bytes,
    endian: str,
    tiff_base: int,
    ifd_offset: int,
    tag_names: dict[int, str],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    start = tiff_base + ifd_offset
    if start + 2 > len(tiff):
        return result

    entry_count = unpack_from(endian + "H", tiff, start)[0]
    cursor = start + 2
    for _ in range(entry_count):
        if cursor + 12 > len(tiff):
            break
        tag, value_type, count = unpack_from(endian + "HHI", tiff, cursor)
        value_or_offset = tiff[cursor + 8 : cursor + 12]
        if tag in tag_names:
            result[tag_names[tag]] = decode_value(
                tiff,
                endian,
                tiff_base,
                value_type,
                count,
                value_or_offset,
            )
        cursor += 12
    return result


def parse_exif(path: Path) -> dict[str, Any]:
    segment = find_exif_segment(path)
    if not segment:
        return {}

    if segment[:2] == b"II":
        endian = "<"
    elif segment[:2] == b"MM":
        endian = ">"
    else:
        return {}

    if unpack_from(endian + "H", segment, 2)[0] != 42:
        return {}

    first_ifd_offset = unpack_from(endian + "I", segment, 4)[0]
    ifd0 = parse_ifd(segment, endian, 0, first_ifd_offset, IFD_TAGS)
    exif_ifd = {}
    gps_ifd = {}

    exif_offset = ifd0.get("ExifIFDPointer")
    if isinstance(exif_offset, int):
        exif_ifd = parse_ifd(segment, endian, 0, exif_offset, EXIF_TAGS)

    gps_offset = ifd0.get("GPSInfoIFDPointer")
    if isinstance(gps_offset, int):
        gps_ifd = parse_ifd(segment, endian, 0, gps_offset, GPS_TAGS)

    return {**ifd0, **exif_ifd, **gps_ifd}


def dms_to_decimal(value: Any, ref: str | None) -> float | None:
    if not isinstance(value, list) or len(value) != 3:
        return None

    parts = [rational_to_float(item) for item in value]
    if any(part is None for part in parts):
        return None

    degrees, minutes, seconds = parts
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def rationals_to_text(value: Any) -> str:
    if isinstance(value, tuple):
        numeric = rational_to_float(value)
        return "" if numeric is None else f"{numeric:.8g}"
    if isinstance(value, list):
        parts = []
        for item in value:
            numeric = rational_to_float(item) if isinstance(item, tuple) else item
            parts.append("" if numeric is None else str(numeric))
        return ";".join(parts)
    return "" if value is None else str(value)


def parse_photo_datetime(exif: dict[str, Any], path: Path) -> str:
    raw = exif.get("DateTimeOriginal") or exif.get("DateTime") or ""
    if isinstance(raw, str) and raw:
        try:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S").isoformat(sep=" ")
        except ValueError:
            return raw
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(sep=" ", timespec="seconds")


def gps_date_time(exif: dict[str, Any]) -> str:
    date_stamp = exif.get("GPSDateStamp")
    time_stamp = exif.get("GPSTimeStamp")
    if not date_stamp or not isinstance(time_stamp, list):
        return ""
    parts = [rational_to_float(item) for item in time_stamp]
    if any(part is None for part in parts):
        return str(date_stamp)
    hour, minute, second = parts
    return f"{date_stamp} {int(hour):02d}:{int(minute):02d}:{second:06.3f}Z"


def photo_record(path: Path) -> dict[str, Any]:
    exif = parse_exif(path)
    latitude = dms_to_decimal(exif.get("GPSLatitude"), exif.get("GPSLatitudeRef"))
    longitude = dms_to_decimal(exif.get("GPSLongitude"), exif.get("GPSLongitudeRef"))
    altitude = rational_to_float(exif["GPSAltitude"]) if "GPSAltitude" in exif else None
    if exif.get("GPSAltitudeRef") == 1 and altitude is not None:
        altitude = -altitude
    direction = (
        rational_to_float(exif["GPSImgDirection"])
        if "GPSImgDirection" in exif
        else None
    )

    return {
        "file": path.name,
        "path": str(path),
        "photo_time": parse_photo_datetime(exif, path),
        "gps_time": gps_date_time(exif),
        "latitude": latitude,
        "longitude": longitude,
        "altitude_m": altitude,
        "direction_deg": direction,
        "has_direction": direction is not None,
        "make": exif.get("Make", ""),
        "model": exif.get("Model", ""),
        "orientation": exif.get("Orientation", ""),
        "focal_length": rationals_to_text(exif.get("FocalLength")),
        "has_gps": latitude is not None and longitude is not None,
    }


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "file",
        "photo_time",
        "gps_time",
        "latitude",
        "longitude",
        "altitude_m",
        "direction_deg",
        "has_direction",
        "make",
        "model",
        "orientation",
        "focal_length",
        "has_gps",
        "path",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fieldnames})


def write_geojson(records: list[dict[str, Any]], path: Path) -> None:
    features = []
    for record in records:
        if not record["has_gps"]:
            continue
        properties = {key: value for key, value in record.items() if key not in {"latitude", "longitude"}}
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [record["longitude"], record["latitude"]],
                },
                "properties": properties,
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "name": path.stem,
        "features": features,
    }
    path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")


def destination_point(
    latitude: float,
    longitude: float,
    bearing_deg: float,
    distance_m: float,
) -> tuple[float, float]:
    radius_m = 6378137.0
    angular_distance = distance_m / radius_m
    bearing = math.radians(bearing_deg)
    lat1 = math.radians(latitude)
    lon1 = math.radians(longitude)

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def write_direction_geojson(records: list[dict[str, Any]], path: Path, length_m: float) -> None:
    features = []
    for record in records:
        if not record["has_gps"] or record["direction_deg"] is None:
            continue
        end_lat, end_lon = destination_point(
            float(record["latitude"]),
            float(record["longitude"]),
            float(record["direction_deg"]),
            length_m,
        )
        properties = {key: value for key, value in record.items() if key not in {"latitude", "longitude"}}
        properties["direction_line_m"] = length_m
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [record["longitude"], record["latitude"]],
                        [end_lon, end_lat],
                    ],
                },
                "properties": properties,
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "name": path.stem,
        "features": features,
    }
    path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")


def write_summary(records: list[dict[str, Any]], path: Path) -> None:
    gps_records = [record for record in records if record["has_gps"]]
    direction_records = [record for record in records if record["has_direction"]]
    gps_direction_records = [
        record for record in records if record["has_gps"] and record["has_direction"]
    ]
    missing_gps = [record["file"] for record in records if not record["has_gps"]]
    payload: dict[str, Any] = {
        "photos_scanned": len(records),
        "photos_with_gps": len(gps_records),
        "photos_with_direction": len(direction_records),
        "photos_with_gps_and_direction": len(gps_direction_records),
        "missing_gps": missing_gps,
    }
    if gps_records:
        payload["latitude_range"] = [
            min(record["latitude"] for record in gps_records),
            max(record["latitude"] for record in gps_records),
        ]
        payload["longitude_range"] = [
            min(record["longitude"] for record in gps_records),
            max(record["longitude"] for record in gps_records),
        ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def select_photos(photo_dir: Path, latest: int | None) -> list[Path]:
    photos = sorted(
        [
            path
            for path in photo_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg"}
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if latest is not None:
        photos = photos[:latest]
    return sorted(photos, key=lambda path: path.name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract EXIF GPS metadata from JPG photos.")
    parser.add_argument("--photo-dir", type=Path, default=DEFAULT_PHOTO_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--latest", type=int, default=24, help="Use the latest N photos by modified time.")
    parser.add_argument("--prefix", default="foton_geotaggar_nya_24")
    parser.add_argument("--direction-length-m", type=float, default=DEFAULT_DIRECTION_LENGTH_M)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    photos = select_photos(args.photo_dir, args.latest)
    records = [photo_record(path) for path in photos]

    csv_path = args.output_dir / f"{args.prefix}.csv"
    geojson_path = args.output_dir / f"{args.prefix}.geojson"
    direction_geojson_path = args.output_dir / f"{args.prefix}_riktningar.geojson"
    summary_path = args.output_dir / f"{args.prefix}_summary.json"
    write_csv(records, csv_path)
    write_geojson(records, geojson_path)
    write_direction_geojson(records, direction_geojson_path, args.direction_length_m)
    write_summary(records, summary_path)

    gps_count = sum(1 for record in records if record["has_gps"])
    direction_count = sum(1 for record in records if record["has_direction"])
    print(f"Photos scanned: {len(records)}")
    print(f"Photos with GPS: {gps_count}")
    print(f"Photos with direction: {direction_count}")
    print(f"CSV: {csv_path}")
    print(f"GeoJSON: {geojson_path}")
    print(f"Direction GeoJSON: {direction_geojson_path}")
    print(f"Summary: {summary_path}")
    if gps_count:
        latitudes = [record["latitude"] for record in records if record["has_gps"]]
        longitudes = [record["longitude"] for record in records if record["has_gps"]]
        print(f"Latitude range: {min(latitudes):.8f} .. {max(latitudes):.8f}")
        print(f"Longitude range: {min(longitudes):.8f} .. {max(longitudes):.8f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
