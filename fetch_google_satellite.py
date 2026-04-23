import json
import urllib.request
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPORTS_DIR = ROOT / "exports"
PARCELS_JSON = EXPORTS_DIR / "millbygard_local_parcels.json"
SATELLITE_DIR = EXPORTS_DIR / "satellite"

def load_env():
    """Laddar in variabler från .env-filen."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))

load_env()
API_KEY = os.environ.get("GOOGLE_API_KEY", "")

def parse_wkt_point(wkt_str):
    clean = wkt_str.replace("POINT(", "").replace(")", "")
    lon_str, lat_str = clean.split(" ")
    return float(lat_str), float(lon_str)

def main():
    if not API_KEY:
        print("STOPP: Hittade ingen GOOGLE_API_KEY i din .env-fil!")
        return

    if not PARCELS_JSON.exists():
        print(f"Fel: Hittade inte filen {PARCELS_JSON}")
        return

    SATELLITE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PARCELS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    for parcel in data.get("parcels", []):
        wkt = parcel.get("centroid_wkt")
        if wkt:
            lat, lon = parse_wkt_point(wkt)
            designation = parcel.get("designation", "Okand").replace(":", "_").replace(">", "_").replace(" ", "_")
            url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=20&size=640x640&maptype=satellite&key={API_KEY}"
            filepath = SATELLITE_DIR / f"{designation}_satellite.jpg"
            print(f"Laddar ner Google Satellitbild för {designation}...")
            urllib.request.urlretrieve(url, filepath)
            print(f" -> Sparad: {filepath.name}")

if __name__ == "__main__":
    main()