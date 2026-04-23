import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "data" / "data_manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print(f"Project: {manifest['project']}")
    print()

    missing = []
    for group in manifest["required_inputs"]:
        print(f"[{group['name']}]")
        for item in group["files"]:
            path = ROOT / item["path"]
            status = file_status(path)
            print(f"  - {status:7} {item['path']} :: {item['purpose']}")
            if status != "OK":
                missing.append(item["path"])
        print()

    if missing:
        print("Missing files:")
        for path in missing:
            print(f"  - {path}")
    else:
        print("All required inputs are present.")


def file_status(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() in {".geojson", ".json"} and path.name.endswith(".geojson"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return "INVALID"
        if payload.get("type") == "FeatureCollection" and len(payload.get("features", [])) == 0:
            return "EMPTY"
    return "OK"


if __name__ == "__main__":
    main()
