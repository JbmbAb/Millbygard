import argparse
import base64
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "01_data_raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve Millbygard layer items from Lantmateriet STAC.")
    parser.add_argument(
        "--env-root",
        type=Path,
        default=None,
        help="Optional path containing .env files with Lantmateriet credentials.",
    )
    parser.add_argument(
        "--layers",
        nargs="+",
        choices=["all", "ortofoto", "markhojd", "byggnader", "fastighet"],
        default=["all"],
        help="Limit raw downloads to selected layers. Default: all.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Resolve items and probe protected assets without downloading raw files.",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Overwrite existing raw files. By default existing non-empty files are kept.",
    )
    return parser.parse_args()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def load_candidate_envs(env_root: Path | None) -> None:
    candidates: list[Path] = []
    if env_root is not None:
        candidates.extend(
            [
                env_root / ".env",
                env_root / ".env.local",
                env_root / ".env.development",
                env_root / ".env.staging",
            ]
        )
    candidates.extend(
        [
            ROOT / ".env",
            ROOT / ".env.local",
            ROOT / ".env.development",
            ROOT / ".env.staging",
        ]
    )
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        load_env_file(candidate)


def http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    body = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = Request(url, data=body, method=method, headers=request_headers)
    with urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def http_bytes(url: str, *, headers: dict[str, str] | None = None) -> bytes:
    req = Request(url, method="GET", headers=headers or {})
    with urlopen(req, timeout=60) as response:
        return response.read()


def compute_bbox(workarea_path: Path) -> list[float]:
    data = json.loads(workarea_path.read_text(encoding="utf-8"))
    coords = data["features"][0]["geometry"]["coordinates"]
    flat: list[list[float]] = []
    for polygon in coords:
        for ring in polygon:
            for lon, lat in ring:
                flat.append([lon, lat])
    min_lon = min(pt[0] for pt in flat)
    min_lat = min(pt[1] for pt in flat)
    max_lon = max(pt[0] for pt in flat)
    max_lat = max(pt[1] for pt in flat)
    return [min_lon, min_lat, max_lon, max_lat]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def selected_layers(raw_layers: list[str]) -> set[str]:
    if "all" in raw_layers:
        return {"ortofoto", "markhojd", "byggnader", "fastighet"}
    return set(raw_layers)


def choose_vector_item(features: list[dict[str, Any]], municipality_name: str) -> dict[str, Any] | None:
    wanted = municipality_name.lower()
    for feature in features:
        title = str(feature.get("properties", {}).get("title", "")).lower()
        if wanted in title:
            return feature
    return features[0] if features else None


def first_env(*keys: str) -> str | None:
    for key in keys:
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return None


def subscription_key() -> str | None:
    return first_env("LANTMATERIET_API_KEY", "LANTMATERIET_SUBSCRIPTION_KEY")


def fetch_bearer_token() -> str | None:
    direct_token = first_env("LANTMATERIET_ACCESS_TOKEN", "LANTMATERIET_AUTHORIZATION_KEY")
    if direct_token:
        return direct_token

    consumer_key = os.environ.get("LANTMATERIET_CONSUMER_KEY", "").strip()
    consumer_secret = os.environ.get("LANTMATERIET_CONSUMER_SECRET", "").strip()
    token_url = os.environ.get("LANTMATERIET_TOKEN_URL", "").strip()
    scope = os.environ.get("LANTMATERIET_SCOPE", "").strip()
    if not consumer_key or not consumer_secret or not token_url:
        return None

    auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode("utf-8")).decode("ascii")
    body = urlencode(
        {
            "grant_type": "client_credentials",
            **({"scope": scope} if scope else {}),
        }
    ).encode("utf-8")
    req = Request(
        token_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return str(payload.get("access_token") or "").strip() or None
    except Exception:
        return None


def auth_attempts(api_key: str | None, bearer_token: str | None, url: str) -> list[tuple[str, dict[str, str], str]]:
    attempts: list[tuple[str, dict[str, str], str]] = [("none", {}, url)]

    user = os.environ.get("LANTMATERIET_SYSTEM_USER", "").strip()
    password = os.environ.get("LANTMATERIET_SYSTEM_PASSWORD", "").strip()
    if user and password:
        auth_str = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
        attempts.append(("basic", {"Authorization": f"Basic {auth_str}"}, url))

    if bearer_token:
        attempts.append(("bearer", {"Authorization": f"Bearer {bearer_token}"}, url))

    if api_key:
        attempts.extend(
            [
                ("subscription_header", {"Ocp-Apim-Subscription-Key": api_key}, url),
                ("subscription_query", {}, f"{url}{'&' if '?' in url else '?'}subscription-key={api_key}"),
            ]
        )

    return attempts


def probe_asset(url: str, api_key: str | None, bearer_token: str | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for mode, headers, attempt_url in auth_attempts(api_key, bearer_token, url):
        req_headers = {"Range": "bytes=0-0", **headers}
        req = Request(attempt_url, method="GET", headers=req_headers)
        try:
            with urlopen(req, timeout=60) as response:
                results.append(
                    {
                        "mode": mode,
                        "url": url,
                        "status": response.status,
                        "contentType": response.headers.get("Content-Type"),
                    }
                )
        except HTTPError as error:
            results.append(
                    {
                        "mode": mode,
                        "url": url,
                        "status": error.code,
                        "contentType": error.headers.get("Content-Type"),
                    }
                )
        except URLError as error:
            results.append({"mode": mode, "url": url, "error": str(error)})
    return results


def save_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def download_public_file(url: str, path: Path) -> dict[str, Any]:
    try:
        payload = http_bytes(url)
        ensure_dir(path.parent)
        path.write_bytes(payload)
        return {"ok": True, "path": str(path), "bytes": len(payload)}
    except HTTPError as error:
        return {"ok": False, "status": error.code, "path": str(path)}
    except URLError as error:
        return {"ok": False, "error": str(error), "path": str(path)}

def download_authenticated_file(url: str, path: Path, api_key: str | None, bearer_token: str | None) -> dict[str, Any]:
    """Download a protected file by trying the configured Lantmateriet credentials."""
    ensure_dir(path.parent)
    temp_path = path.with_name(f"{path.name}.part")
    errors: list[dict[str, Any]] = []

    for mode, headers, attempt_url in auth_attempts(api_key, bearer_token, url):
        try:
            if temp_path.exists():
                temp_path.unlink()
            req = Request(attempt_url, method="GET", headers=headers)
            bytes_downloaded = 0
            with urlopen(req, timeout=600) as response, open(temp_path, "wb") as out_file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    bytes_downloaded += len(chunk)
            temp_path.replace(path)
            return {"ok": True, "mode": mode, "path": str(path), "bytes": bytes_downloaded}
        except HTTPError as error:
            errors.append({"mode": mode, "status": error.code})
        except URLError as error:
            errors.append({"mode": mode, "error": str(error)})
        finally:
            if temp_path.exists():
                temp_path.unlink()

    return {"ok": False, "path": str(path), "attempts": errors}


def download_layer(
    label: str,
    url: str,
    path: Path,
    api_key: str | None,
    bearer_token: str | None,
    *,
    force: bool,
) -> dict[str, Any]:
    if path.exists() and path.stat().st_size > 0 and not force:
        return {"ok": True, "skipped": True, "path": str(path), "bytes": path.stat().st_size}
    print(f"\nLaddar ner {label} (detta kan ta en stund)...")
    return download_authenticated_file(url, path, api_key, bearer_token)

def main() -> int:
    args = parse_args()
    load_candidate_envs(args.env_root)
    layers_to_download = selected_layers(args.layers)

    bbox = compute_bbox(DATA_DIR / "orsa_stackmora_3_12_workarea.geojson")
    municipality_name = "Orsa"

    image_search = http_json(
        "https://api.lantmateriet.se/stac-bild/v1/search",
        method="POST",
        payload={"bbox": bbox, "limit": 5},
    )
    height_search = http_json(
        "https://api.lantmateriet.se/stac-hojd/v1/search",
        method="POST",
        payload={"bbox": bbox, "limit": 5},
    )
    building_search = http_json(
        "https://api.lantmateriet.se/stac-vektor/v1/search",
        method="POST",
        payload={"collections": ["byggnader"], "bbox": bbox, "limit": 10},
    )
    property_search = http_json(
        "https://api.lantmateriet.se/stac-vektor/v1/search",
        method="POST",
        payload={"collections": ["fastighetsindelning"], "bbox": bbox, "limit": 10},
    )

    ortho_item = image_search["features"][0]
    height_item = height_search["features"][0]
    building_item = choose_vector_item(building_search.get("features", []), municipality_name)
    property_item = choose_vector_item(property_search.get("features", []), municipality_name)

    ensure_dir(RAW_DIR / "ortofoto")
    ensure_dir(RAW_DIR / "markhojd")
    ensure_dir(RAW_DIR / "byggnader")
    ensure_dir(RAW_DIR / "fastighet")

    save_json(RAW_DIR / "ortofoto" / "orsa_stackmora_3_12_ortofoto_item.json", ortho_item)
    save_json(RAW_DIR / "markhojd" / "orsa_stackmora_3_12_markhojd_item.json", height_item)
    save_json(RAW_DIR / "byggnader" / "orsa_stackmora_3_12_byggnader_item.json", building_item)
    save_json(RAW_DIR / "fastighet" / "orsa_stackmora_3_12_fastighet_item.json", property_item)

    public_downloads = {
        "ortofoto_metadata": download_public_file(
            ortho_item["assets"]["metadata"]["href"],
            RAW_DIR / "ortofoto" / "orsa_stackmora_3_12_ortofoto_metadata.json",
        ),
        "ortofoto_thumbnail": download_public_file(
            ortho_item["assets"]["thumbnail"]["href"],
            RAW_DIR / "ortofoto" / "orsa_stackmora_3_12_ortofoto_thumbnail.jpg",
        ),
        "markhojd_metadata": download_public_file(
            height_item["assets"]["metadata"]["href"],
            RAW_DIR / "markhojd" / "orsa_stackmora_3_12_markhojd_metadata.json",
        ),
        "markhojd_thumbnail": download_public_file(
            height_item["assets"]["thumbnail"]["href"],
            RAW_DIR / "markhojd" / "orsa_stackmora_3_12_markhojd_thumbnail.jpg",
        ),
    }

    api_key = subscription_key()
    bearer_token = fetch_bearer_token()
    probes = {
        "ortofoto": probe_asset(ortho_item["assets"]["data"]["href"], api_key, bearer_token),
        "markhojd": probe_asset(height_item["assets"]["data"]["href"], api_key, bearer_token),
        "byggnader": probe_asset(building_item["assets"]["data"]["href"], api_key, bearer_token),
        "fastighet": probe_asset(property_item["assets"]["data"]["href"], api_key, bearer_token),
    }

    summary = {
        "project": "Millbygard",
        "designation": "ORSA STACKMORA 3:12 (1)(2)(3)",
        "technicalDesignation": "ORSA STACKMORA 3:12>1..3",
        "bboxWgs84": bbox,
        "resolvedItems": {
            "ortofoto": {
                "collection": ortho_item["collection"],
                "id": ortho_item["id"],
                "dataHref": ortho_item["assets"]["data"]["href"],
            },
            "markhojd": {
                "collection": height_item["collection"],
                "id": height_item["id"],
                "dataHref": height_item["assets"]["data"]["href"],
            },
            "byggnader": {
                "collection": building_item["collection"],
                "id": building_item["id"],
                "dataHref": building_item["assets"]["data"]["href"],
            },
            "fastighet": {
                "collection": property_item["collection"],
                "id": property_item["id"],
                "dataHref": property_item["assets"]["data"]["href"],
            },
        },
        "publicDownloads": public_downloads,
        "rawAssetProbe": probes,
        "downloadSelection": {
            "layers": sorted(layers_to_download),
            "noDownload": args.no_download,
        },
    }
    save_json(DATA_DIR / "orsa_stackmora_3_12_layer_resolution.json", summary)

    downloads = [
        (
            "ortofoto",
            "Ortofoto",
            ortho_item["assets"]["data"]["href"],
            RAW_DIR / "ortofoto" / "orsa_stackmora_3_12_ortofoto_highres.tif",
        ),
        (
            "markhojd",
            "Markhojd",
            height_item["assets"]["data"]["href"],
            RAW_DIR / "markhojd" / "orsa_stackmora_3_12_markhojd_highres.tif",
        ),
        (
            "byggnader",
            "Byggnader",
            building_item["assets"]["data"]["href"],
            RAW_DIR / "byggnader" / "byggnader.zip",
        ),
        (
            "fastighet",
            "Fastighet",
            property_item["assets"]["data"]["href"],
            RAW_DIR / "fastighet" / "fastighet.zip",
        ),
    ]
    if args.no_download:
        print("Skipping raw downloads because --no-download was set.")
    for layer_key, name, url, path in downloads:
        if args.no_download or layer_key not in layers_to_download:
            continue
        dl_result = download_layer(name, url, path, api_key, bearer_token, force=args.force_download)
        if dl_result.get("ok"):
            mb_size = dl_result["bytes"] / (1024 * 1024)
            if dl_result.get("skipped"):
                print(f"{name} finns redan ({mb_size:.1f} MB): {path}")
            else:
                print(f"Success! {name} sparat ({mb_size:.1f} MB) pa: {path}")
        else:
            print(f"Kunde inte ladda ner {name}: {dl_result}")
    print()

    print("Resolved layer items and saved public metadata.")
    print(json.dumps(summary["resolvedItems"], ensure_ascii=False, indent=2))

    blocked = {
        key: not any(result.get("status") in (200, 206) for result in value)
        for key, value in probes.items()
        if key in layers_to_download
    }
    print("Raw asset probe:")
    print(json.dumps(probes, ensure_ascii=False, indent=2))
    if any(blocked.values()):
        print("One or more raw assets are still blocked by current auth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
