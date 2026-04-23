from pathlib import Path


ROOT = Path(__file__).resolve().parent

FILES_TO_CHECK = [
    ROOT / "01_data_raw" / "markhojd" / "orsa_stackmora_3_12_markhojd_highres.tif",
    ROOT / "data" / "orsa_stackmora_3_12_markhojd.tif",
    ROOT / "01_data_raw" / "ortofoto" / "orsa_stackmora_3_12_ortofoto_highres.tif",
    ROOT / "data" / "orsa_stackmora_3_12_ortofoto.tif",
]


def main() -> None:
    for path in FILES_TO_CHECK:
        relative_path = path.relative_to(ROOT)
        if not path.exists():
            print(f"MISSING {relative_path}")
            continue

        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"OK      {relative_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
