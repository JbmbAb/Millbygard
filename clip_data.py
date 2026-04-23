import os
import sys
import zipfile
import tempfile
import importlib.util
from pathlib import Path


def prefer_rasterio_proj_data() -> None:
    spec = importlib.util.find_spec("rasterio")
    if spec is None or spec.origin is None:
        return
    proj_data = Path(spec.origin).resolve().parent / "proj_data"
    if not (proj_data / "proj.db").exists():
        return

    current = os.environ.get("PROJ_LIB", "")
    current_db = Path(current) / "proj.db" if current else None
    if not current_db or not current_db.exists() or "PostgreSQL" in current:
        os.environ["PROJ_LIB"] = str(proj_data)
        os.environ["PROJ_DATA"] = str(proj_data)


prefer_rasterio_proj_data()

try:
    import geopandas as gpd
    import rasterio
    from rasterio.mask import mask
except ImportError:
    print("Fel: Nödvändiga bibliotek för kartklippning saknas.")
    print("Kör detta i din terminal:")
    print("pip install geopandas rasterio shapely")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "01_data_raw"

def clip_raster(in_path, out_path, shapes_3006, target_crs):
    if not in_path.exists():
        print(f"Hoppar över raster: {in_path.name} (finns inte ännu)")
        return
    
    print(f"Klipper ut {in_path.name} över Millbygård...")
    temp_path = out_path.with_name(f"{out_path.name}.part")
    with rasterio.open(in_path) as src:
        out_image, out_transform = mask(src, shapes_3006, crop=True)
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "crs": target_crs,
        })
        
        # Säkerhetsåtgärd: Ta bort tiling/block-metadata. 
        # Kraschar annars om den utklippta bilden är mindre än originalets blockstorlek.
        for key in ["blockxsize", "blockysize", "tiled"]:
            out_meta.pop(key, None)

        try:
            if temp_path.exists():
                temp_path.unlink()
            with rasterio.open(temp_path, "w", **out_meta) as dest:
                dest.write(out_image)
            temp_path.replace(out_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    print(f" -> Sparade: {out_path.name}")

def clip_vector(in_zip, out_path, workarea_3006):
    if not in_zip.exists():
        print(f"Hoppar över vektor: {in_zip.name} (finns inte ännu)")
        return
        
    print(f"Packar upp och klipper {in_zip.name} över Millbygård...")
    
    # Vi packar upp till en tillfällig mapp så att Geopandas enkelt hittar alla filer
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(in_zip, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
            
        # Hitta rätt lager (GeoPackage eller Shapefile)
        vector_files = list(Path(tmpdir).rglob("*.gpkg"))
        if not vector_files:
            vector_files = list(Path(tmpdir).rglob("*.shp"))
            
        if not vector_files:
            print(f" -> Fel: Inga giltiga vektordata-filer (.gpkg / .shp) i zippen.")
            return
            
        # Läs in den stora filen
        gdf = gpd.read_file(vector_files[0])
        
        # Matchar Lantmäteriets koordinatsystem (SWEREF 99 TM / EPSG:3006)
        if gdf.crs != workarea_3006.crs:
            gdf = gdf.to_crs(workarea_3006.crs)
            
        # Klipp bort allt som är utanför fastigheten!
        clipped = gpd.clip(gdf, workarea_3006)
        
        if out_path.suffix == '.geojson':
            clipped = clipped.to_crs(epsg=4326) # Minecraft/GeoJSON-standard är WGS84
            clipped.to_file(out_path, driver="GeoJSON")
        else:
            clipped.to_file(out_path, driver="GPKG")
            
        print(f" -> Sparade: {out_path.name}")

def main():
    workarea_path = DATA_DIR / "orsa_stackmora_3_12_workarea.geojson"
    if not workarea_path.exists():
        print("Fel: Skapa en 'workarea.geojson' först!")
        return

    print("Läser in pepparkaksformen (workarea)...")
    workarea_4326 = gpd.read_file(workarea_path)
    workarea_3006 = workarea_4326.to_crs(epsg=3006)
    shapes_3006 = [geom for geom in workarea_3006.geometry]
    
    # Använd __geo_interface__ för att garantera att rasterio alltid förstår geometrin
    shapes_3006 = [geom.__geo_interface__ for geom in workarea_3006.geometry]

    clip_raster(
        RAW_DIR / "ortofoto" / "orsa_stackmora_3_12_ortofoto_highres.tif",
        DATA_DIR / "orsa_stackmora_3_12_ortofoto.tif",
        shapes_3006,
        "EPSG:3006",
    )
    clip_raster(
        RAW_DIR / "markhojd" / "orsa_stackmora_3_12_markhojd_highres.tif",
        DATA_DIR / "orsa_stackmora_3_12_markhojd.tif",
        shapes_3006,
        "EPSG:3006",
    )
    clip_vector(RAW_DIR / "byggnader" / "byggnader.zip", DATA_DIR / "orsa_stackmora_3_12_byggnader.geojson", workarea_3006)
    clip_vector(RAW_DIR / "fastighet" / "fastighet.zip", DATA_DIR / "orsa_stackmora_3_12_fastighet.gpkg", workarea_3006)

if __name__ == "__main__":
    main()
