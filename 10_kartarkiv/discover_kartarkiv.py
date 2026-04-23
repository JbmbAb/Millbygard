import base64
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
SOURCE_DIR = ROOT / "01_kallor"
INDEX_DIR = ROOT / "02_lagerindex"

SOURCES = [
    {
        "id": "lantmateriet_historiska_ortofoton",
        "name": "Lantmateriet historiska ortofoton",
        "type": "WMS",
        "auth": "lantmateriet_basic",
        "url": "https://maps.lantmateriet.se/historiska-ortofoton/wms/v1?SERVICE=WMS&REQUEST=GetCapabilities",
        "note": "Behorighetsstyrd visningstjanst. Bra for historiska flygbilder.",
    },
    {
        "id": "sgu_jordarter_25_100",
        "name": "SGU jordarter 25-100",
        "type": "WMS",
        "url": "https://resource.sgu.se/service/wms/130/jordarter-25-100-tusen?service=WMS&request=GetCapabilities",
        "note": "Oppet WMS-lager for jordarter.",
    },
    {
        "id": "sgu_jorddjupsmodell",
        "name": "SGU jorddjupsmodell",
        "type": "WMS",
        "url": "https://resource.sgu.se/service/wms/130/jorddjupsmodell?service=WMS&request=GetCapabilities",
        "note": "Oppet WMS-lager for jorddjup.",
    },
    {
        "id": "sgu_grundvattenmagasin",
        "name": "SGU grundvattenmagasin",
        "type": "WMS",
        "url": "https://resource.sgu.se/service/wms/130/grundvattenmagasin?service=WMS&request=GetCapabilities",
        "note": "Oppet WMS-lager for grundvattenmagasin.",
    },
    {
        "id": "sgu_forutsattning_skred",
        "name": "SGU forutsattning for skred i finkornig jordart",
        "type": "WMS",
        "url": "https://resource.sgu.se/service/wms/130/forutsattning-skred-finkornig-jordart?service=WMS&request=GetCapabilities",
        "note": "Oppet WMS-lager for skredforutsattningar.",
    },
    {
        "id": "sgu_berggrund_50_250",
        "name": "SGU berggrund 50-250",
        "type": "WMS",
        "url": "https://resource.sgu.se/service/wms/130/berggrund-50-250-tusen?service=WMS&request=GetCapabilities",
        "note": "Oppet WMS-lager for berggrund.",
    },
    {
        "id": "naturvardsverket_naturvardsregistret",
        "name": "Naturvardsverket naturvardsregistret",
        "type": "WMS",
        "url": "https://geodata.naturvardsverket.se/naturvardsregistret/wms?service=WMS&request=GetCapabilities",
        "note": "Naturvardsregister och skyddad natur.",
    },
    {
        "id": "naturvardsverket_andra_skydd",
        "name": "Naturvardsverket andra skydd",
        "type": "WMS",
        "url": "https://geodata.naturvardsverket.se/andra_skydd/wms?service=WMS&request=GetCapabilities",
        "note": "Andra skydd och naturvardslager.",
    },
    {
        "id": "naturvardsverket_geoserver",
        "name": "Naturvardsverket geoserver",
        "type": "WMS",
        "url": "https://nvgis.naturvardsverket.se/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities",
        "note": "Bredare geoserver-endpoint; kan innehalla manga lager.",
    },
    {
        "id": "lansstyrelsen_publikt",
        "name": "Lansstyrelserna publika geodata",
        "type": "WMS",
        "url": "https://ext-geoservices.lansstyrelsen.se/arcgis/services/Publikt/Publikt/MapServer/WMSServer?service=WMS&request=GetCapabilities",
        "note": "Publika lansstyrelselager. Kan vara langsam.",
    },
    {
        "id": "skogsstyrelsen_publikt",
        "name": "Skogsstyrelsen publika geodata",
        "type": "WMS",
        "url": "https://geodata.skogsstyrelsen.se/arcgis/services/Publikt/MapServer/WMSServer?service=WMS&request=GetCapabilities",
        "note": "Skogliga lager; endpointen kan krava annan atkomst.",
    },
    {
        "id": "raa_kulturmiljo",
        "name": "Riksantikvarieambetet kulturmiljo",
        "type": "WMS",
        "url": "https://karta.raa.se/geoserver/ows?service=WMS&request=GetCapabilities",
        "note": "Kulturmiljo/Fornsok-spar; endpoint kan behova justeras.",
    },
]

ATOM_SOURCES = [
    {
        "id": "lm_admin_indelning_inspire_atom",
        "name": "Administrativ indelning Inspire Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/administrativindelning/atom/v1.1/",
        "note": "Avblockerad oppen data enligt API-portalen.",
    },
    {
        "id": "lm_belagenhetsadress_inspire_atom",
        "name": "Belagenhetsadress Inspire Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/belagenhetsadress/atom/v1.2",
        "note": "Avblockerad oppen data enligt API-portalen.",
    },
    {
        "id": "lm_byggnad_inspire_atom",
        "name": "Byggnad Inspire Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/byggnad/atom/v1.1",
        "note": "Kan vara snabbare vag till byggnadsdata an Geotorget-order for Byggnad nedladdning, vektor.",
    },
    {
        "id": "lm_hydrografi_atom",
        "name": "Hydrografi Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/hydrografi/atom/v1.1/",
        "note": "Avblockerad oppen data enligt API-portalen.",
    },
    {
        "id": "lm_marktacke_inspire_atom",
        "name": "Marktacke Inspire Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/marktacke/atom/v1.1",
        "note": "Avblockerad oppen data enligt API-portalen.",
    },
    {
        "id": "lm_ortnamn_inspire_atom",
        "name": "Ortnamn Inspire Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/ortnamn/atom/v1",
        "note": "Avblockerad oppen data enligt API-portalen.",
    },
    {
        "id": "lm_tyngdkraft_atom",
        "name": "Tyngdkraft Nedladdning",
        "type": "ATOM",
        "auth": "lantmateriet_basic",
        "url": "https://api.lantmateriet.se/tyngdkraft-nedladdning/atom/v1",
        "note": "Avblockerad oppen data enligt API-portalen, lag prioritet for Minecraft.",
    },
]


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"").strip("'"))


def headers_for(source: dict[str, str]) -> dict[str, str]:
    headers = {
        "Accept": "application/xml,text/xml,*/*",
        "User-Agent": "Millbygard-kartarkiv/0.1",
    }
    if source.get("auth") == "lantmateriet_basic":
        user = os.environ.get("LANTMATERIET_SYSTEM_USER", "").strip()
        password = os.environ.get("LANTMATERIET_SYSTEM_PASSWORD", "").strip()
        if user and password:
            token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
    return headers


def fetch_capabilities(source: dict[str, str]) -> tuple[dict[str, Any], bytes | None]:
    request = Request(source["url"], headers=headers_for(source), method="GET")
    try:
        with urlopen(request, timeout=45) as response:
            payload = response.read()
            return (
                {
                    "id": source["id"],
                    "name": source["name"],
                    "type": source["type"],
                    "url": source["url"],
                    "note": source["note"],
                    "ok": True,
                    "status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "bytes": len(payload),
                },
                payload,
            )
    except HTTPError as error:
        return (
            {
                "id": source["id"],
                "name": source["name"],
                "type": source["type"],
                "url": source["url"],
                "note": source["note"],
                "ok": False,
                "status": error.code,
                "content_type": error.headers.get("Content-Type"),
                "error": "HTTPError",
            },
            None,
        )
    except URLError as error:
        return (
            {
                "id": source["id"],
                "name": source["name"],
                "type": source["type"],
                "url": source["url"],
                "note": source["note"],
                "ok": False,
                "error": f"URLError: {error.reason}",
            },
            None,
        )
    except Exception as error:
        return (
            {
                "id": source["id"],
                "name": source["name"],
                "type": source["type"],
                "url": source["url"],
                "note": source["note"],
                "ok": False,
                "error": f"{type(error).__name__}: {error}",
            },
            None,
        )


def parse_layers(source_id: str, payload: bytes) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    layers: list[dict[str, Any]] = []
    for layer in root.iter():
        if not re.sub(r"^\{.*\}", "", layer.tag).lower().endswith("layer"):
            continue
        name = None
        title = None
        abstract = None
        for child in list(layer):
            tag = re.sub(r"^\{.*\}", "", child.tag).lower()
            if tag == "name" and child.text:
                name = child.text.strip()
            elif tag == "title" and child.text:
                title = child.text.strip()
            elif tag == "abstract" and child.text:
                abstract = " ".join(child.text.split())
        if name:
            layers.append(
                {
                    "source_id": source_id,
                    "name": name,
                    "title": title or name,
                    "abstract": abstract,
                }
            )
    return layers


def parse_atom_entries(source_id: str, payload: bytes) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    entries: list[dict[str, Any]] = []
    for entry in root.iter():
        if re.sub(r"^\{.*\}", "", entry.tag).lower() != "entry":
            continue
        title = None
        entry_id = None
        links: list[dict[str, str]] = []
        for child in list(entry):
            tag = re.sub(r"^\{.*\}", "", child.tag).lower()
            if tag == "title" and child.text:
                title = child.text.strip()
            elif tag == "id" and child.text:
                entry_id = child.text.strip()
            elif tag == "link":
                href = child.attrib.get("href")
                if href:
                    links.append(
                        {
                            "href": href,
                            "rel": child.attrib.get("rel", ""),
                            "type": child.attrib.get("type", ""),
                            "title": child.attrib.get("title", ""),
                        }
                    )
        entries.append(
            {
                "source_id": source_id,
                "id": entry_id,
                "title": title or entry_id,
                "links": links,
            }
        )
    return entries


def main() -> int:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    load_env(PROJECT_ROOT / ".env")

    statuses: list[dict[str, Any]] = []
    all_layers: list[dict[str, Any]] = []
    atom_statuses: list[dict[str, Any]] = []
    atom_entries: list[dict[str, Any]] = []

    for source in SOURCES:
        status, payload = fetch_capabilities(source)
        statuses.append(status)
        if payload:
            cap_path = SOURCE_DIR / f"{source['id']}_capabilities.xml"
            cap_path.write_bytes(payload)
            status["capabilities_path"] = str(cap_path)
            layers = parse_layers(source["id"], payload)
            status["layer_count"] = len(layers)
            all_layers.extend(layers)
        else:
            status["layer_count"] = 0

    for source in ATOM_SOURCES:
        status, payload = fetch_capabilities(source)
        atom_statuses.append(status)
        if payload:
            atom_path = SOURCE_DIR / f"{source['id']}_feed.xml"
            atom_path.write_bytes(payload)
            status["feed_path"] = str(atom_path)
            entries = parse_atom_entries(source["id"], payload)
            status["entry_count"] = len(entries)
            atom_entries.extend(entries)
        else:
            status["entry_count"] = 0

    (INDEX_DIR / "wms_sources_status.json").write_text(
        json.dumps(statuses, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (INDEX_DIR / "wms_layers.json").write_text(
        json.dumps(all_layers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (INDEX_DIR / "atom_sources_status.json").write_text(
        json.dumps(atom_statuses, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (INDEX_DIR / "atom_entries.json").write_text(
        json.dumps(atom_entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Sparade status for {len(statuses)} kallor.")
    print(f"Hittade {len(all_layers)} namngivna WMS-lager.")
    print(f"Sparade status for {len(atom_statuses)} Atom-kallor.")
    print(f"Hittade {len(atom_entries)} Atom-poster.")
    print(f"Status: {INDEX_DIR / 'wms_sources_status.json'}")
    print(f"Lager:  {INDEX_DIR / 'wms_layers.json'}")
    print(f"Atom-status: {INDEX_DIR / 'atom_sources_status.json'}")
    print(f"Atom-poster: {INDEX_DIR / 'atom_entries.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
