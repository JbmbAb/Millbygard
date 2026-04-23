# Kallor for kartarkivet

Detta ar en levande lista. "Katalogiserad" betyder att vi har lagt in kallan i discovery-flodet eller dokumenterat hur den ska sokas. "Lokal data" betyder att ett faktiskt utdrag eller en anvandbar fil redan finns i projektet.

## Lantmateriet / Geotorget

- Markhojdmodell Nedladdning: lokal 1 m TIFF finns och anvands som huvudterrang.
- Markhojdmodell Nedladdning, grid 50+: lokalt 50 m-grid finns som grovt stod.
- Laserdata Nedladdning, skog: relevant 2,5 x 2,5 km LAZ-ruta finns lokalt.
- Ortofoto historiska Visning: WMS fungerar och preview finns lokalt.
- Topografiska kartor: lokal leverans finns och anvands nu for forsta vag-/markutkast runt garden.
- Ortofoto Nedladdning: lokal highres-TIFF finns och klippt arbetsortofoto finns i `data/`.
- Byggnad nedladdning, vektor: hog prioritet, men lokal byggnads-GeoJSON saknas.
- Fastighetsindelning nedladdning, vektor: hog prioritet, men lokal GPKG saknas.
- Topografi 10 Nedladdning, vektor: relevant for vagar, vatten, mark och bebyggelse nar leverans fungerar.
- Ythojdmodell Nedladdning, fran flygbilder i farg: relevant senare for trad/byggnadsytor, men ersatter inte markhojd.

Tekniska spar:

- Geotorget nedladdning API: https://api.lantmateriet.se/geotorget/nedladdning/v1
- Historiska ortofoton WMS: https://maps.lantmateriet.se/historiska-ortofoton/wms/v1?
- Historiska kartor, manuell arkivsokning: https://historiskakartor.lantmateriet.se/

## SGU

SGU har oppna WMS-tjanster som kan ge geologi och markinformation over Orsa:

- Jordarter 1:25 000 - 1:100 000
- Jorddjupsmodell
- Grundvattenmagasin
- Forutsattning for skred i finkornig jordart
- Berggrund 1:50 000 - 1:250 000

Dessa ar relevanta for historik/naturgrund och landskapsforstaelse, aven om de inte ar primara Minecraft-lager.

## Naturvardsverket

Naturvardsverkets geodata kan ge skyddad natur, naturvardsregister och andra natur-/miljolager. Dessa ar intressanta for Orsa kommun och landskapet runt Millbygard.

## Lansstyrelserna

Lansstyrelsernas publika geodata kan innehalla riksintressen, naturvarden, kulturmiljo, vatten, bevarandeomraden och planeringsunderlag. Endpointar kan vara langsamma eller varierande, sa de bor testas och dokumenteras separat.

## Riksantikvarieambetet / Kulturmiljoregistret

Fornsok/Kulturmiljoregistret kan innehalla lamningar och kulturhistoriska objekt. Detta ar en viktig icke-Lantmateriet-kalla for aldre lager och platsens historiska kontext.

## Riksarkivet och andra arkiv

Riksarkivet kan ha skannade historiska kartor eller handlingar som inte finns som WMS. Dessa maste ofta sokas manuellt pa kartnamn, socken, by eller fastighetsnamn:

- Orsa
- Stackmora
- Orsa Stackmora
- Millbygard / Millby

## Kommunkallor och andra karttjanster

Orsa kommun, regionala kartportaler och andra offentliga aktorer kan ha egna karttjanster. Dessa ar inte fullt inventerade annu och ska laggas till nar vi hittar fungerande endpoints.

## Google Maps Platform

Google kan bidra som visuell kontroll och referens, men ska inte vara huvudkalla for lokala GIS-lager eller Minecraft-terrang.

Mojligt anvandbart:

- Maps Static API / satellitbild: snabb visuell kontroll av gard, vagar, vegetation och byggnadsplacering.
- Street View Static API: fasad-/vagreferenser om Street View finns pa platsen.
- Map Tiles API: road/satellite/terrain tiles och Street View tiles for kartvisning i en app.
- Photorealistic 3D Tiles: kan vara intressant for visuell 3D-referens om omradet har tackning.
- Elevation API: kan ge punktvis hojd, men ska inte ersatta Lantmateriets markhojd.

Begransning:

- Google Maps-innehall far normalt inte bulk-laddas, cachelagras, hostas om eller anvandas for att skapa egna dataset.
- Det ar sarskilt olampligt att rita av byggnader/vagar eller bygga terrangmodell fran Google Maps/Elevation for Minecraft-underlaget.

Lokalt finns redan enkla referensskript:

- `fetch_google_satellite.py`
- `fetch_streetview.py`

Rekommendation:

- Anvand Google som manuell visuell referens och for smabilder i `exports/`.
- Anvand Lantmateriet, SGU, Naturvardsverket och andra oppna/offentliga geodatakallor for faktiska kartlager och genererade Minecraft-data.
