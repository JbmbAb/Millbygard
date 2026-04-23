import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPORTS_DIR = ROOT / "exports"
PARCELS_JSON = EXPORTS_DIR / "millbygard_local_parcels.json"
STREETVIEW_DIR = EXPORTS_DIR / "streetview"
MANIFEST_JSON = STREETVIEW_DIR / "streetview_manifest.json"


def load_env() -> None:
    """Load variables from the local .env file."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


load_env()
API_KEY = os.environ.get("GOOGLE_API_KEY", "")


def parse_wkt_point(wkt_str: str) -> tuple[float, float]:
    """Convert 'POINT(lon lat)' to (lat, lon)."""
    clean = wkt_str.replace("POINT(", "").replace(")", "")
    lon_str, lat_str = clean.split(" ")
    return float(lat_str), float(lon_str)


def build_streetview_params(lat: float, lon: float, heading: int) -> dict[str, str]:
    return {
        "size": "640x640",
        "location": f"{lat},{lon}",
        "fov": "90",
        "heading": str(heading),
        "pitch": "0",
        "key": API_KEY,
    }


def fetch_metadata(lat: float, lon: float, heading: int) -> dict:
    base_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    params = build_streetview_params(lat, lon, heading)
    url = base_url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def download_streetview(lat: float, lon: float, filename: str, heading: int) -> dict:
    """Download a Street View image if metadata says an image exists."""
    metadata = fetch_metadata(lat, lon, heading)
    status = metadata.get("status", "UNKNOWN")

    result = {
        "filename": filename,
        "heading": heading,
        "lat": lat,
        "lon": lon,
        "status": status,
        "pano_id": metadata.get("pano_id"),
        "copyright": metadata.get("copyright"),
        "date": metadata.get("date"),
    }

    if status != "OK":
        print(f" -> Ingen riktig Street View-bild for {filename} ({status})")
        return result

    base_url = "https://maps.googleapis.com/maps/api/streetview"
    params = build_streetview_params(lat, lon, heading)
    url = base_url + "?" + urllib.parse.urlencode(params)
    filepath = STREETVIEW_DIR / filename

    try:
        urllib.request.urlretrieve(url, filepath)
        result["saved_path"] = str(filepath)
        result["bytes"] = filepath.stat().st_size
        print(f" -> Sparad: {filename} ({heading} deg, {result['bytes']} bytes)")
    except Exception as exc:
        result["download_error"] = str(exc)
        print(f" -> Fel vid nedladdning for {filename}: {exc}")

    return result


def main() -> None:
    if not API_KEY:
        print("STOPP: Hittade ingen GOOGLE_API_KEY i din .env-fil.")
        return

    if not PARCELS_JSON.exists():
        print(f"Fel: Hittade inte filen {PARCELS_JSON}")
        return

    STREETVIEW_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(PARCELS_JSON.read_text(encoding="utf-8"))

    directions = {"norr": 0, "oster": 90, "soder": 180, "vaster": 270}
    manifest = {"source": str(PARCELS_JSON), "results": []}

    for parcel in data.get("parcels", []):
        designation = parcel.get("designation", "Okand")
        safe_name = designation.replace(":", "_").replace(">", "_").replace(" ", "_")
        wkt = parcel.get("centroid_wkt")
        if not wkt:
            continue

        lat, lon = parse_wkt_point(wkt)
        print(f"\nKontrollerar Street View for {designation} ({lat}, {lon})...")

        for dir_name, heading in directions.items():
            filename = f"{safe_name}_{dir_name}.jpg"
            result = download_streetview(lat, lon, filename, heading)
            result["designation"] = designation
            result["direction"] = dir_name
            manifest["results"].append(result)

    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest sparad: {MANIFEST_JSON}")


if __name__ == "__main__":
    main()
