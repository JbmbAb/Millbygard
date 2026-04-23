import json
import math
import sys
from pathlib import Path
from PIL import Image
from mcpi.minecraft import Minecraft

ROOT = Path(__file__).resolve().parent
EXPORTS_DIR = ROOT / "exports"
PARCELS_JSON = EXPORTS_DIR / "millbygard_local_parcels.json"
SATELLITE_DIR = EXPORTS_DIR / "satellite"

EARTH_RADIUS_M = 6378137.0

# Färgpalett för att översätta bildens RGB-färger till Minecraft-block.
# Format: ((R, G, B), Block-ID, Block-Data)
PALETTE = [
    ((60, 90, 50), 2, 0),     # GRÄS (mörkgrönt)
    ((90, 130, 60), 18, 0),   # LÖV (ljusgrönt/träd)
    ((70, 70, 70), 1, 0),     # STEN (mörkgrå asfalterade tak/vägar)
    ((140, 140, 140), 13, 0), # GRUS (ljusgrå grusgångar)
    ((110, 80, 60), 3, 0),    # JORD (åker/brun mark)
    ((140, 50, 40), 45, 0),   # TEGEL (Falu rödfärg/röda tak)
    ((50, 60, 90), 9, 0),     # VATTEN (blått)
    ((200, 200, 200), 35, 0), # VIT ULL (vita husknutar/ljusa detaljer)
    ((30, 30, 30), 49, 0),    # OBSIDIAN (djupa skuggor)
]

def closest_block(r, g, b):
    """Hittar det Minecraft-block som matchar RGB-färgen bäst."""
    best_dist = 999999
    best_block = (2, 0)
    for (pr, pg, pb), blk_id, blk_data in PALETTE:
        dist = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
        if dist < best_dist:
            best_dist = dist
            best_block = (blk_id, blk_data)
    return best_block

def parse_wkt_point(wkt_str):
    clean = wkt_str.replace("POINT(", "").replace(")", "")
    lon_str, lat_str = clean.split(" ")
    return float(lat_str), float(lon_str)

def lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat):
    lat0_rad = math.radians(origin_lat)
    x = EARTH_RADIUS_M * math.radians(lon - origin_lon) * math.cos(lat0_rad)
    z = EARTH_RADIUS_M * math.radians(lat - origin_lat)
    return x, z

def main():
    if not PARCELS_JSON.exists():
        print(f"Fel: Hittade inte filen {PARCELS_JSON}")
        sys.exit(1)

    with open(PARCELS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    origin_lon = data["coordinate_basis"]["origin_lon"]
    origin_lat = data["coordinate_basis"]["origin_lat"]

    try:
        mc = Minecraft.create()
        mc.postToChat("Ritar ut satellitbilder over Millbygard...")
    except ConnectionRefusedError:
        print("Kunde inte ansluta till Minecraft. Kontrollera servern.")
        sys.exit(1)

    # Vi lägger kartan på Y=62 (precis under guldlinjerna på Y=63)
    Y_LEVEL = 62 

    for parcel in data.get("parcels", []):
        wkt = parcel.get("centroid_wkt")
        if not wkt: continue
        
        lat, lon = parse_wkt_point(wkt)
        cx, cz = lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat)
        
        designation = parcel.get("designation", "Okand").replace(":", "_").replace(">", "_").replace(" ", "_")
        img_path = SATELLITE_DIR / f"{designation}_satellite.jpg"
        
        if not img_path.exists():
            print(f"Bild saknas för {designation}, hoppar över...")
            continue
            
        print(f"Målar ut satellitkarta för {designation}...")
        img = Image.open(img_path).convert("RGB")
        width, height = img.size
        
        # Zoom 20 vid latitud 61.13 motsvarar ca 0.072 meter per pixel
        meters_per_pixel = 0.07206 
        half_w = int((width * meters_per_pixel) / 2)
        half_h = int((height * meters_per_pixel) / 2)
        
        # Rita blocken i en kvadrat runt mittpunkten
        for dx in range(-half_w, half_w):
            for dz in range(-half_h, half_h):
                # Översätt Minecrafts block-koordinat tillbaka till bildens pixel-koordinat
                px = int((dx + half_w) / meters_per_pixel)
                py = int((half_h - dz) / meters_per_pixel)
                
                # Håll pixeln inom bildens ramar
                px = max(0, min(width - 1, px))
                py = max(0, min(height - 1, py))
                
                r, g, b = img.getpixel((px, py))
                blk_id, blk_data = closest_block(r, g, b)
                
                # Invertera Z (-Z är norrut i Minecraft)
                mc.setBlock(int(cx + dx), Y_LEVEL, -int(cz + dz), blk_id, blk_data)

    mc.postToChat("Satellitkartan ar fardigmalad!")

if __name__ == "__main__":
    main()