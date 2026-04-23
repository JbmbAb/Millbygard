import json
import sys
from pathlib import Path

import numpy as np

try:
    import rasterio
except ImportError:
    print("Fel: rasterio saknas.")
    print("Kor detta i terminalen: pip install rasterio")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
HEIGHTMAP_DIR = ROOT / "03_heightmap"


def main() -> int:
    src_path = DATA_DIR / "orsa_stackmora_3_12_markhojd.tif"
    out_path = HEIGHTMAP_DIR / "orsa_stackmora_3_12_heightmap_16bit.png"
    meta_path = HEIGHTMAP_DIR / "orsa_stackmora_3_12_heightmap_16bit.json"

    if not src_path.exists():
        print(f"Fel: saknar {src_path}")
        return 1

    HEIGHTMAP_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(src_path) as src:
        data = src.read(1, masked=True).astype("float32")
        valid = data.compressed()
        if valid.size == 0:
            print("Fel: markhojd-rastret innehaller inga giltiga pixlar.")
            return 1

        min_z = float(valid.min())
        max_z = float(valid.max())
        span = max(max_z - min_z, 0.001)
        normalized = ((data.filled(min_z) - min_z) / span * 65535.0).clip(0, 65535)
        heightmap = normalized.astype("uint16")

        profile = {
            "driver": "PNG",
            "height": src.height,
            "width": src.width,
            "count": 1,
            "dtype": "uint16",
        }
        with rasterio.open(out_path, "w", **profile) as dest:
            dest.write(heightmap, 1)

        metadata = {
            "source": str(src_path.relative_to(ROOT)),
            "output": str(out_path.relative_to(ROOT)),
            "encoding": "16-bit grayscale PNG",
            "height_units": "meters",
            "min_z": min_z,
            "max_z": max_z,
            "z_range": span,
            "width": src.width,
            "height": src.height,
            "source_crs": str(src.crs),
            "source_bounds": {
                "left": src.bounds.left,
                "bottom": src.bounds.bottom,
                "right": src.bounds.right,
                "top": src.bounds.top,
            },
            "note": "Draft terrain base from markhojdmodell. Later ythojd/ortofoto/building layers can refine trees, buildings and visual placement.",
        }
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Sparade heightmap: {out_path}")
    print(f"Sparade metadata: {meta_path}")
    print(f"Z-intervall: {min_z:.2f} m till {max_z:.2f} m ({span:.2f} m)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
