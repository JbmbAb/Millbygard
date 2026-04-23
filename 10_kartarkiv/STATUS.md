# Status for kartarkivet

Uppdaterad: 2026-04-13

## Kort lage

Kartarkivet ar startat och ligger separat fran Minecraft-pipelinen. Forsta automatiska discovery-rundan har testat 12 WMS-kallor och hittat 160 namngivna WMS-lager.

Lantmateriets avblockerade Atom-API:er har ocksa testats. Rootfloden for 7 Atom-kallor svarade och gav 12 topposter. Ett extra steg ner hittade Orsa-poster for byggnad, marktacke och ortnamn, men direkt ZIP-nedladdning av datasetfilen ar fortfarande inte lost.

## Kallor som svarade

- Lantmateriet historiska ortofoton: 41 lager.
- SGU jordarter 25-100: 9 lager.
- SGU jorddjupsmodell: 7 lager.
- SGU grundvattenmagasin: 48 lager.
- SGU forutsattning for skred i finkornig jordart: 3 lager.
- SGU berggrund 50-250: 22 lager.
- Naturvardsverket naturvardsregistret: 14 lager.
- Naturvardsverket andra skydd: 3 lager.
- Naturvardsverket geoserver: 13 lager.

## Kallor som behover ny kontroll

- Lansstyrelserna publika geodata: svarade inte inom timeout vid forsta forsoket.
- Skogsstyrelsen publika geodata: gav 401 vid forsta forsoket; endpoint eller atkomstmodell behover kontrolleras.
- Riksantikvarieambetet kulturmiljo: anslutningen stangdes vid forsta forsoket; endpoint eller User-Agent/URL behover kontrolleras.

## Sparade filer

- WMS-status: `10_kartarkiv/02_lagerindex/wms_sources_status.json`
- WMS-lagerindex: `10_kartarkiv/02_lagerindex/wms_layers.json`
- Atom-status: `10_kartarkiv/02_lagerindex/atom_sources_status.json`
- Atom-topposter: `10_kartarkiv/02_lagerindex/atom_entries.json`
- Atom-Orsa-status: `10_kartarkiv/02_lagerindex/atom_orsa_sources_status.json`
- Atom-Orsa-poster: `10_kartarkiv/02_lagerindex/atom_orsa_entries.json`
- Google Millbygard-status: `10_kartarkiv/02_lagerindex/google_millbygard_status.json`
- Capabilities XML: `10_kartarkiv/01_kallor/`
- Historisk ortofoto-preview: `10_kartarkiv/03_previewbilder/lantmateriet_historiska_ortofoton_OI.Histortho_color_2005.png`

## Google for Millbygard

Google ar anvandbart som referens for Millbygard, men inte som auktoritativ GIS-kalla:

- Static satellite finns sparat for alla tre delytor.
- Street View finns for `ORSA STACKMORA 3:12>1` och `ORSA STACKMORA 3:12>2`, med datum 2024-05 i manifestet.
- Street View saknas for `ORSA STACKMORA 3:12>3` vid testade centroidpunkter.
- Elevation API svarar for alla tre delytor, men med grov upplosning jamfort med Lantmateriets markhojd.

## Minecraft-sparet efter detta

Minecraft-basen ska fortsatta anvanda:

- `data/orsa_stackmora_3_12_markhojd.tif` for huvudterrang.
- `03_heightmap/orsa_stackmora_3_12_heightmap_16bit.png` for heightmap.
- `01_data_raw/laserdata_skog/20D026_677_48_7500.laz` som mojligt senare detaljstod.
- `data/topografi/orsa_stackmora_3_12_topografi_vagar_2km.geojson` for forsta vagutkast runt garden och narmiljon.
- `data/topografi/orsa_stackmora_3_12_topografi_mark_2km.geojson` for forsta markutkast runt garden och narmiljon.

2 km-uttaget fran Topografiska kartor gav 444 vagfeatures och 340 markfeatures. Det ar battre som narmiljounderlag an 500 m-uttaget, men 500 m-uttaget finns kvar for snabbare detaljkontroll nara fastigheten.

Snabbkarta for Minecraft ar genererad som datapack-funktionen `millbygard:topografi_2km`. Den ritar en grov 2 km-karta vid `x=-105..105`, `y=90..94`, `z=211..429`; se `10_kartarkiv/MINECRAFT_SNABBKARTA.md`.

Foljande saknas fortfarande for den gamla pipeline-kontrollen:

- `data/orsa_stackmora_3_12_ortofoto.tif`
- `data/orsa_stackmora_3_12_byggnader.geojson`
- `data/orsa_stackmora_3_12_fastighet.gpkg`
