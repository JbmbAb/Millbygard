# Miollbygard: Next Steps

Detta ar nasta fas for det fristaende Millbygard-sidoprojektet.

Projektet ska inte blandas ihop med Miljobeslut-plattformen. Den enda avsiktliga kopplingen ar att hamta/exportera underlagsdata fran PostGIS till lokala filer.

## Nuvarande lage

Klart:

- fastighetsdelar `ORSA STACKMORA 3:12>1..3`
- sammanslagen `workarea`
- lokala meterkoordinater
- sammanfattningsfiler i `exports/`
- separat projektstruktur for radata, QGIS, heightmap, byggnader och anteckningar
- cirkel- och skalzoner for mjuk 4:1 -> 1:1-overgang utan att ersatta fastighetsgransen

Geotorget-orderinventering finns sparad i:

- `data/geotorget_orders_manifest.json`

Viktigast for Millbygard just nu ar orderraderna for ortofoto, byggnader, fastighetsindelning och Topografi 10. Grid 50+ finns redan som grovt uttag, och 1 m-markhojd finns som huvudkalla.

Inte klart:

- fastighetslager som arbetsfil
- QGIS-projekt
- full terrangexport till Minecraft fran heightmap
- uppdaterad fotokarta efter varje ny batch fastighetskort

## Verifierad status

Senaste kontrollen med `python check_inputs.py` visar:

Klart:

- `data/orsa_stackmora_3_12_split.geojson`
- `data/orsa_stackmora_3_12_workarea.geojson`
- `data/orsa_stackmora_3_12_live_lookup.json`
- `data/orsa_stackmora_3_12_ortofoto.tif`
- `data/orsa_stackmora_3_12_markhojd.tif`
- `data/orsa_stackmora_3_12_workarea_circle.geojson`
- `data/orsa_stackmora_3_12_workarea_circle_overlay.geojson`
- `data/orsa_stackmora_3_12_scale_transition_zones.geojson`

Saknas:

- `data/orsa_stackmora_3_12_fastighet.gpkg`

Notering: `data/orsa_stackmora_3_12_byggnader.geojson` ar nu ersatt med klippta Lantmateriet-byggnadspolygoner fran `Byggnad nedladdning, vektor`. Dessa ger bra planmatt. Forsta tak-/ythojdsstod finns i `output/building_surface_heights_20260416.json`, men ska fortfarande fotokontrolleras manuellt.

## Skala och mjuk overgang

Nuvarande strategi ar en detaljlins, inte en ersattning av fastighetsgransen:

- fastighetsgransen bestar i `data/orsa_stackmora_3_12_workarea.geojson`
- overlay med cirkel + grans finns i `data/orsa_stackmora_3_12_workarea_circle_overlay.geojson`
- skalzoner finns i `data/orsa_stackmora_3_12_scale_transition_zones.geojson`

Skalzonerna ar:

- 0-80 m fran gardscentrum: 4:1
- 80-140 m: mjuk overgang fran 4:1 till 1:1
- 140-255.79 m: 1:1 kontextzon som tacker hela fastigheten

Generatorer:

```powershell
python tools/create_workarea_circle.py
python tools/create_scale_transition_zones.py
```

Mer detaljerad checklista finns i `docs/scale-transition-and-map-layers.md`.

## Upplosta officiella lager

Senaste korningen med `fetch_lantmateriet_layers.py` hittade exakta officiella item-id:n for arbetsytan:

- ortofoto: `orto-q2-2024` / `o67775_4800_25_mr24`
- markhojd: `mhm-67_4` / `677_48_7500`
- byggnader: `byggnader` / `2034`
- fastighet: `fastighetsindelning` / `2034`

Detta finns sparat i:

- `data/orsa_stackmora_3_12_layer_resolution.json`
- `01_data_raw/ortofoto/orsa_stackmora_3_12_ortofoto_item.json`
- `01_data_raw/markhojd/orsa_stackmora_3_12_markhojd_item.json`
- `01_data_raw/byggnader/orsa_stackmora_3_12_byggnader_item.json`
- `01_data_raw/fastighet/orsa_stackmora_3_12_fastighet_item.json`

Publik metadata och preview-bilder finns ocksa lokalt for ortofoto och markhojd.

## Laserdata skog

Order `LM2026/051784` verkar vara en stor leverans av `Laserdata Nedladdning, skog` runt 668 GB. Hamta inte allt for Millbygard.

For Orsa Stackmora 3:12 racker det att plocka ut samma 2,5 km-ruta som markhojden:

- produktionsomrade: `20D026`
- status: `Pa lager (Klass 3)`
- indexruta: `677_48_7500`
- forvantad LAZ-fil: `67775_4800_25.laz`
- lokal notering: `data/orsa_stackmora_3_12_laserdata_skog_selection.json`

Praktiskt: ga in i Laserdata Skog-leveransen/Geotorget, valj ratt ar/omrade `20D026` och hamta bara `67775_4800_25.laz`.

## Topografiska kartor

Topografiska kartor finns i `Kartor` som en separat Geotorget-leverans:

- mapp: `C:\Users\jimmy\Desktop\Kartor\29b34f2e-9bcf-4a40-b62d-bd487c94cd43`
- zip: `C:\Users\jimmy\Desktop\Kartor\29b34f2e-9bcf-4a40-b62d-bd487c94cd43.zip`
- format: GeoPackage-filer inuti zip-arkiv
- CRS: `EPSG:3006`
- lokal notering: `data/orsa_stackmora_3_12_topografiska_kartor_selection.json`

Relevanta lager for Millbygard:

- `byggnadsverk_sverige.zip` for byggnader/anlaggningar
- `kommunikation_sverige.zip` for vagar/stigar
- `hydrografi_sverige.zip` for vattenlinjer och diken
- `mark_sverige.zip` for marktacke/sankmark, men den ar stor och bor klippas selektivt
- `text_sverige.zip` for ortnamn/kartetiketter

Ladda inte in hela Sverige-lagren i onodan. Klipp valda tabeller mot `data/orsa_stackmora_3_12_workarea.geojson` eller en liten buffer nar GIS-verktyg finns tillgangliga.

Kvarvarande blockerare:

- ortofoto ar nedladdat och klippt till `data/orsa_stackmora_3_12_ortofoto.tif`
- `dl1.lantmateriet.se` svarar `401` utan auth
- `dl1.lantmateriet.se` svarar `206` med Basic Auth for ortofoto och markhojd
- `dl1.lantmateriet.se` svarar `403` med dagens bearer-token
- byggnad och fastighet svarar fortfarande `403` med nuvarande Basic Auth

## Hard prioritet

### 1. Ortofoto

Malfil:

- `data/orsa_stackmora_3_12_ortofoto.tif`

Behovs for:

- byggnaders lage
- gardsplan
- vagar
- trad
- staketlinjer
- markmonster

### 2. Markhojdmodell

Malfil:

- `data/orsa_stackmora_3_12_markhojd.tif`

Kompletterande grid 50+-underlag finns ocksa fran `Kartor`-leveransen:

- kalla: `C:\Users\jimmy\Desktop\Kartor\4100b5a8-af76-46c4-be10-b052b0fda64c\67_4.zip`
- intern fil: `67_4.xyz`
- lokalt uttag for Millbygard-rutan: `data/orsa_stackmora_3_12_markhojd_grid50_677_48_7500.xyz`
- metadata: `data/orsa_stackmora_3_12_markhojd_grid50_selection.json`

Anvand grid 50+ som grovt stod eller kontroll. Den klippta 1 m-filen `data/orsa_stackmora_3_12_markhojd.tif` ar fortfarande huvudkallan for terrang/heightmap.

Behovs for:

- terrang
- slanter
- gardsnivaer
- senare export till `16-bit PNG`

### 3. Byggnadslager

Malfil:

- `data/orsa_stackmora_3_12_byggnader.geojson`
- `output/building_measurements_20260416.csv`

Behovs for:

- huvudhus
- lada
- uthus
- byggnadsvolymer i Minecraft

Status:

- raw zip finns: `01_data_raw/byggnader/byggnader.zip`
- klippta byggnadspolygoner finns
- planmatt finns i CSV/JSON
- byggnadshojder saknas fortfarande

### 4. Fastighetslager

Malfil:

- `data/orsa_stackmora_3_12_fastighet.gpkg`

Behovs for:

- stodlager i QGIS
- orientering och kontroll
- kontroll mot delytor och workarea

## Praktisk ordning

1. Behall `orsa_stackmora_3_12_workarea.geojson` som mastergrans.
2. Hamta ortofoto som tacker hela workarea.
3. Hamta markhojd som tacker hela workarea.
4. Hamta byggnadslager.
5. Hamta eller exportera fastighetslager.
6. Importera allt i QGIS.
7. Klipp allt mot workarea.
8. Exportera forsta heightmap.

## Rekommenderad byggordning for Minecraft

Borja inte med hela Orsa i detalj. Gor en grov regional bas forst och detaljzonen runt Millbygard sedan.

Nedladdningsprioritet:

1. `Ortofoto Nedladdning` - viktigast for visuell kontroll av gard, vagar, trad, staket och ytmonster.
2. `Byggnad nedladdning, vektor` - viktigast for hus/lador/uthus.
3. `Fastighetsindelning nedladdning, vektor` - stodlager for grans och orientering.
4. `Topografi 10 Nedladdning, vektor` - vagar, vatten, mark, text och struktur for storre omgivning.
5. `Ythojdmodell` - mottagen och nyttjad for DSM/trueortho/class samt forsta tak-/ythojdsstod.
6. `Laserdata skog` - bara selektiv ruta/omrade, inte hela leveransen.

Varldsstrategi:

- Skapa forst en grov bas runt Millbygard, exempelvis 2 x 2 km eller 3 x 3 km.
- Hall storomradet grovt: terrang, huvudvagar, vatten, skog/oppen mark.
- Hall Millbygard-zonen detaljerad: cirka 500 x 500 m runt garden.
- Behall samma origin och skala: `1 block = 1 meter`, x osterut och z norrut enligt parcel-exporten.
- For detaljbygge: anvand skalzonerna som planeringslager dar garden far 4:1 och ytteromradet gar tillbaka till 1:1 med mjuk overgang.

Google-underlag finns redan lokalt som referensbilder:

- `exports/satellite/`
- `exports/streetview/`

Anvand Google for visuell kontroll av tak, fasader, trad och infarter. Anvand inte Google som huvudkalla for automatisk kartgenerering nar Lantmateriets ortofoto/topografi finns eller ar pa vag.

## Korbara hjalpkommandon

Kontroll av vad som finns och saknas:

```powershell
python check_inputs.py
```

Samlad lokal launcher:

```powershell
python millbygard_launcher.py status
python millbygard_launcher.py datapack
python millbygard_launcher.py verify
```

Skapa 1:1 ortofoto-yta som Minecraft-datapack:

```powershell
python generate_minecraft_ortofoto_surface.py
```

Kor sedan i Minecraft:

```text
/reload
/function millbygard:launch
```

Eller kor hela visuella startlagret direkt:

```text
/function millbygard:visual_start
```

Direktkommando for bara ortofoto-ytan:

```text
/function millbygard:ortofoto_surface
```

Uppdatering av lokala parcel-exporter:

```powershell
python "Millbygård.py"
```

## Resultat vi vill ha efter nasta fas

- `data/orsa_stackmora_3_12_ortofoto.tif`
- `data/orsa_stackmora_3_12_markhojd.tif`
- `data/orsa_stackmora_3_12_ythojd_dsm.tif`
- `data/orsa_stackmora_3_12_ythojd_above_ground.tif`
- `data/orsa_stackmora_3_12_tower_site.geojson`
- `data/orsa_stackmora_3_12_byggnader.geojson`
- `data/orsa_stackmora_3_12_fastighet.gpkg`
- ett QGIS-projekt som anvander dessa tillsammans med workarea
- uppdaterad fotogeotaggning med GPS + kompassriktning for nya `IMG_...`-bilder: klart for senaste batchen i `output/foton_geotaggar_opencamera_20260416.*` och `output/foton_geotaggar_nya_24.*`

## Minecraft completion layer

Aktuell komplett Minecraft-planexport ar:

```text
function millbygard:farm4_complete
```

Den bygger den torra 4:1-garden och lagger ovanpa:

- fastighetsgrans och delgranser
- 4:1-, overgangs- och kontextmarkeringar
- byggnadsfotavtryck fran Lantmateriets byggnadsvektor
- tornplats fran hogsta markhojdpunkt
- foto-GPS och kompassriktningar
- Topografi-vagar och hydrografi/grundvatten som cyan markering under markytan utan vattenblock
- markhojdankare

Manifestet finns i `data/minecraft_finish_layers_manifest.json`.

## Full 1:1-fastighetsterrang

Den spelbara fullversionen utan live-push byggs med:

```text
function millbygard:full_property_complete
```

Den genereras av:

```powershell
python tools/generate_minecraft_full_property_terrain.py
```

Aktuell export anvander alla 29 080 giltiga 1 m-markhojdpunkter inne i fastigheten/workarea. Markhojdens 32,99 m hojdskillnad bevaras som 1 block per meter, med Minecraft-yta y=70..103. Ythojd anvands selektivt for byggnadsstod/roof-height, inte som full 0,25 m terrang, for att halla varlden spelbar.

Bygget ar uppdelat i 98 etapper med cirka 1 sekund mellan varje etapp. Fastighetsgransen ritas som rod betong ovanpa den skapade terrangen och inga vattenblock genereras.

Manifestet finns i `data/minecraft_full_property_terrain_manifest.json`.
