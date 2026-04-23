# Miollbygard

Detta ar ett separat sidoprojekt for Millbygard.

## Status

Workspacet ar fristaende fran Miljobeslut-plattformen. Den enda avsiktliga kopplingen ar datahamtning/export fran PostGIS till lokala GeoJSON-filer.

Det som finns lokalt nu:

- `data/orsa_stackmora_3_12_split.geojson`
- `data/orsa_stackmora_3_12_split_summary.json`
- `data/orsa_stackmora_3_12_live_lookup.json`
- `data/orsa_stackmora_3_12_workarea.geojson`

## Vad skriptet gor

`Millbygard.py` anvander inga externa Python-paket.

Det laser GeoJSON-filerna i `data/` och skapar:

- `exports/millbygard_local_parcels.json`
- `exports/millbygard_parcel_summary.json`
- `exports/millbygard_parcel_summary.md`

Syftet ar att ge lokala meterkoordinater som gar att anvanda vidare for Minecraft-planering med ungefarlig skala `1 block = 1 meter`.

For detaljbygge finns nu ocksa ett mjukt skalupplagg:

- fastighetsgransen bestar som master i `data/orsa_stackmora_3_12_workarea.geojson`
- cirkeltackning finns i `data/orsa_stackmora_3_12_workarea_circle.geojson`
- overlay med cirkel + fastighetsgrans finns i `data/orsa_stackmora_3_12_workarea_circle_overlay.geojson`
- 4:1 -> 1:1-zoner finns i `data/orsa_stackmora_3_12_scale_transition_zones.geojson`

Detaljer finns i `docs/scale-transition-and-map-layers.md`.

## Projektstruktur

Den separata projektstrukturen finns nu pa plats:

```text
01_data_raw/
  ortofoto/
  markhojd/
  byggnader/
  fastighet/
02_qgis/
03_heightmap/
04_references/
05_buildings/
06_schematics/
07_exports/
08_prompts/
09_notes/
```

Nuvarande arbetsfiler ligger kvar i `data/`, `exports/` och `docs/`.

## Foto- och kartlagerstrategi

Nya fastighetskort ska hamna i `Foton/`. Baste foton for placering har GPS, hojd och kompassriktning fran Open Camera. Foton anvands for fasader, tornplats, vagar, stenrosen och kontroll av terrang; Lantmateriets markhojdmodell ar fortfarande huvudkallan for hojd.

Aktuella fotolager finns i `output/foton_geotaggar_alla.*`, `output/foton_geotaggar_opencamera_20260416.*` och `output/foton_geotaggar_nya_24.*`. Filer med `_riktningar.geojson` innehaller kompasslinjer som visar vart kameran pekade.

Tornplatsen ar satt till hogsta giltiga markhojdscell inom fastighetsytan: `data/orsa_stackmora_3_12_tower_site.geojson` (61.133607499, 14.665000889, 250.90 m).

Byggnadsvektorn ar nu hamtad och klippt: `data/orsa_stackmora_3_12_byggnader.geojson`. Utraknade byggnadsmatt finns i `output/building_measurements_20260416.csv` och `.json`; matt beskriver framst takkant/footprint, inte faktisk fasadmatt eller hojd.

Ythojdmodellen ar uppackad och nyttjad. Klippta filer finns som `data/orsa_stackmora_3_12_ythojd_dsm.tif`, `data/orsa_stackmora_3_12_ythojd_trueortho.tif`, `data/orsa_stackmora_3_12_ythojd_class.tif` och `data/orsa_stackmora_3_12_ythojd_above_ground.tif`. Byggnaders forsta tak-/ythojdsstod finns i `output/building_surface_heights_20260416.csv`.

Kartlager som redan finns eller ar inventerade:

- Lantmateriet ortofoto highres och klippt arbetsfil
- Lantmateriet markhojd 1 m highres och klippt arbetsfil
- Grid 50+ som grov hojdkontroll
- Laserdata skog for selektiv detaljkontroll
- Topografi 10 for vagar, mark, byggnadsverk, hydrografi och text
- PostGIS/SGU-underlag for jord, grundvatten och avrinningsomrade
- fastighetsgrans fran workarea/split-exporter

## Korning

```powershell
python "Millbygård.py"
python check_inputs.py
python fetch_lantmateriet_layers.py --env-root "c:\Users\jimmy\Desktop\Examens arbete\Kod\Ny mapp\remix_-copy-of-miljöbeslut.se-portal"
```

Enklare samlad korning finns i `millbygard_launcher.py`:

```powershell
python millbygard_launcher.py status
python millbygard_launcher.py ortofoto
python millbygard_launcher.py datapack
python millbygard_launcher.py verify
```

## Upplosta lager

`fetch_lantmateriet_layers.py` laser `workarea`, slar upp exakta STAC-items for ortofoto, markhojd, byggnader och fastighet och sparar:

- item-json under `01_data_raw/`
- publik metadata och thumbnails for ortofoto och markhojd
- sammanstallning i `data/orsa_stackmora_3_12_layer_resolution.json`

Nuvarande lage: ortofoto och markhojd kan hamtas med Basic Auth. Ortofoto ar nedladdat som highres-radata och klippt till lokal arbetsfil. Byggnad och fastighet ar fortfarande blockerade med `403` i nuvarande auth.

Viktigt om auth:

- `LANTMATERIET_CONSUMER_KEY` och `LANTMATERIET_CONSUMER_SECRET` racker for att hamta ett OAuth-token
- det tokenet verkar inte ensam ge nedladdning av rafilerna fran `dl1.lantmateriet.se`
- skriptet stoder nu aven en separat portalnyckel via `LANTMATERIET_ACCESS_TOKEN` eller `LANTMATERIET_AUTHORIZATION_KEY`
- om du hittar en faktisk subscription key kan den laggas som `LANTMATERIET_SUBSCRIPTION_KEY`

Kort sagt: STAC-katalogen fungerar redan. For saker korning kan `fetch_lantmateriet_layers.py --layers ortofoto` anvandas for att bara hamta ortofoto utan att forsoka dra hem alla lager.

## Nasta sak som saknas

For att ga vidare fran fastighetsgeometri till byggbar varld behovs fortfarande:

- `data/orsa_stackmora_3_12_byggnader.geojson`
- `data/orsa_stackmora_3_12_fastighet.gpkg`
- QGIS-projekt som klipper allt mot `workarea`

## Minecraft ortofoto-yta

`generate_minecraft_ortofoto_surface.py` laser det klippta Lantmateriet-ortofotot och skapar en 1:1 visuell markyta som datapack-funktion:

```powershell
python generate_minecraft_ortofoto_surface.py
```

I Minecraft:

```text
/reload
/function millbygard:launch
```

Launch-menyn i spelet har klickbara val for ortofoto-yta, skyltar, topografi-oversikt och visuell start. Direktkommandot for hela visuella startlagret ar:

```text
/function millbygard:visual_start
```

Direktkommandot for bara ortofoto-ytan ar:

```text
/function millbygard:ortofoto_surface
```

Preview finns i `04_references/orsa_stackmora_3_12_ortofoto_blocks_preview.png` och metadata i `data/minecraft_ortofoto_surface_manifest.json`.

Se ocksa:

- `docs/next-steps.md`
- `docs/scale-transition-and-map-layers.md`
- `data/data_manifest.json`
