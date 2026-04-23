import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
EXPORTS_DIR = ROOT / "exports"
SERVER_DIR = ROOT / "MinecraftServer"

DATAPACK_DIR = SERVER_DIR / "world" / "datapacks" / "millbygard"
FUNCTION_DIR = DATAPACK_DIR / "data" / "millbygard" / "functions"

EARTH_RADIUS_M = 6378137.0


def lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat):
    """Convert WGS84 lon/lat to local meter coordinates."""
    lat0_rad = math.radians(origin_lat)
    x = EARTH_RADIUS_M * math.radians(lon - origin_lon) * math.cos(lat0_rad)
    z = EARTH_RADIUS_M * math.radians(lat - origin_lat)
    return x, z


def setup_datapack():
    FUNCTION_DIR.mkdir(parents=True, exist_ok=True)
    pack_mcmeta = DATAPACK_DIR / "pack.mcmeta"
    if not pack_mcmeta.exists():
        pack_mcmeta.write_text(
            json.dumps(
                {
                    "pack": {
                        "pack_format": 26,
                        "description": "Millbygard information signs (Text Displays)",
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def clean_text(text):
    return str(text).replace("'", "").replace('"', "").replace("\n", " ")


def load_geopandas():
    try:
        import geopandas as gpd
    except ImportError:
        print(
            "Hoppar over vektorskyltar: geopandas saknas. "
            "Kor pip install geopandas om byggnads-/SGU-lager ska lasas."
        )
        return None

    return gpd


def add_building_signs(commands, origin_lon, origin_lat):
    buildings_file = DATA_DIR / "orsa_stackmora_3_12_byggnader.geojson"
    if not buildings_file.exists():
        return

    gpd = load_geopandas()
    if gpd is None:
        return

    gdf_b = gpd.read_file(buildings_file).to_crs(epsg=4326)
    for _, row in gdf_b.iterrows():
        lon, lat = row.geometry.centroid.x, row.geometry.centroid.y
        x, z = lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat)
        purpose = clean_text(row.get("andamal_1", row.get("andamal", "Byggnad")))
        text_nbt = f'{{"text":"Byggnad:\\n{purpose}","color":"white"}}'
        commands.append(
            f"summon text_display {int(x)} 65 {-int(z)} "
            f"{{text:'{text_nbt}',billboard:\"center\"}}"
        )


def add_groundwater_signs(commands, origin_lon, origin_lat):
    gw_file = DATA_DIR / "orsa_stackmora_3_12_groundwater.geojson"
    if not gw_file.exists():
        return

    gpd = load_geopandas()
    if gpd is None:
        return

    gdf_gw = gpd.read_file(gw_file).to_crs(epsg=4326)
    for _, row in gdf_gw.iterrows():
        lon, lat = row.geometry.centroid.x, row.geometry.centroid.y
        x, z = lon_lat_to_local_meters(lon, lat, origin_lon, origin_lat)
        mag_pos = clean_text(row.get("magasinsposition", "Grundvattenmagasin"))
        if len(mag_pos) > 50:
            mag_pos = mag_pos[:47] + "..."

        text_nbt = f'{{"text":"SGU Grundvatten\\n{mag_pos}","color":"aqua"}}'
        commands.append(
            f"summon text_display {int(x)} 65 {-int(z)} "
            f"{{text:'{text_nbt}',billboard:\"center\"}}"
        )


def main():
    setup_datapack()

    parcels_file = EXPORTS_DIR / "millbygard_local_parcels.json"
    if not parcels_file.exists():
        print(f"Fel: Saknar {parcels_file}. Kor Millbygard.py forst.")
        return

    with parcels_file.open("r", encoding="utf-8") as f:
        parcel_data = json.load(f)

    origin_lon = parcel_data["coordinate_basis"]["origin_lon"]
    origin_lat = parcel_data["coordinate_basis"]["origin_lat"]

    commands = ["kill @e[type=text_display]"]
    y_level = 65

    for parcel in parcel_data.get("parcels", []):
        designation = clean_text(parcel.get("designation", "Okand fastighet"))
        wkt = parcel.get("centroid_wkt")
        if wkt:
            lon_str, lat_str = wkt.replace("POINT(", "").replace(")", "").split(" ")
            x, z = lon_lat_to_local_meters(float(lon_str), float(lat_str), origin_lon, origin_lat)
            text_nbt = f'{{"text":"Fastighet:\\n{designation}","color":"gold","bold":true}}'
            commands.append(
                f"summon text_display {int(x)} {y_level} {-int(z)} "
                f"{{text:'{text_nbt}',billboard:\"center\"}}"
            )

    add_building_signs(commands, origin_lon, origin_lat)
    add_groundwater_signs(commands, origin_lon, origin_lat)

    mcfunction_file = FUNCTION_DIR / "signs.mcfunction"
    mcfunction_file.write_text("\n".join(commands), encoding="utf-8")

    print(f"\nSkapade {len(commands) - 1} hologram-skyltar fran lokala kartlager.")
    print(f"Datapacket sparades till: {FUNCTION_DIR}")
    print("\nI Minecraft:")
    print("1. Skriv /reload i chatten")
    print("2. Skriv /function millbygard:signs i chatten")


if __name__ == "__main__":
    main()
