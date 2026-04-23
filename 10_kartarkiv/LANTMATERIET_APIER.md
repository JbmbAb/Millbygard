# Lantmateriet-API:er som ar avblockerade

Uppdaterad fran anvandarens API-lista: 2026-04-13.

## Finns for tillfallet

| API | Status | Plan | Kartarkiv-roll |
| --- | --- | --- | --- |
| Administrativ_indelning_Inspire_Nedladdning v1.1 | AVBLOCKERING | Oppna data | Kommun/lan/rike via Atom/GML. |
| Belagenhetsadress_Nedladdning_Inspire_v1.2 | AVBLOCKERING | Oppna data | Adresser, kan ge platsnamn/adresskontext. |
| Byggnad_Nedladdning_Inspire v1.1 | AVBLOCKERING | Oppna data | Viktig alternativ vag for byggnader. |
| FAPI v1 | AVBLOCKERING | Obegransat | Fastighets-API, utreds separat. |
| Fastighetsomrade v1 | AVBLOCKERING | Obegransat | Direkt/API-vag for fastighetsytor, utreds separat. |
| Geotorget-nedladdning v1 | AVBLOCKERING | Brons | Order- och nedladdningshantering. |
| Hydrografi_Nedladdning v1.1 | AVBLOCKERING | Oppna data | Vattenlager via Atom/GML. |
| Hojd_Direkt v1 | AVBLOCKERING | Guld | Direkt API for hojddata, utreds separat. |
| Markhojd_Direkt v1 | AVBLOCKERING | Guld | Direkt API for markhojd, kan komplettera lokal TIFF. |
| Marktacke_Inspire_Nedladdning v1.1 | AVBLOCKERING | Oppna data | Marktacke/land cover via Atom/GML. |
| OGC-funktioner v1 | AVBLOCKERING | FairUse | OGC API Features, utreds separat. |
| Ortnamn_Inspire_Nedladdning v1 | AVBLOCKERING | Oppna data | Ortnamn via Atom/GML. |
| STAC-bild v1 | AVBLOCKERING | FairUse | Bildkatalog; anvands redan for ortofoto-lookup. |
| STAC-hojd v1 | AVBLOCKERING | FairUse | Hojdkatalog; anvands for markhojd-lookup. |
| STAC-karta v1 | AVBLOCKERING | FairUse | Kartkatalog; utreds for arkiv/kartor. |
| STAC-vektor v1 | AVBLOCKERING | FairUse | Vektorkatalog; anvands for byggnad/fastighet-lookup. |
| Tyngdkraft_Nedladdning v1 | AVBLOCKERING | Oppna data | Lagrar for kartarkivet, lag prioritet for Minecraft. |

## Teknisk startpunkt

Flera Inspire-nedladdningar ar Atomfloden. De testas nu av `discover_kartarkiv.py` och skrivs till:

- `10_kartarkiv/02_lagerindex/atom_sources_status.json`
- `10_kartarkiv/02_lagerindex/atom_entries.json`

Dokumenterade produkt-endpoints fran Lantmateriets tekniska beskrivningar:

- Administrativ indelning: `https://api.lantmateriet.se/administrativindelning/atom/v1.1/`
- Belagenhetsadress: `https://api.lantmateriet.se/belagenhetsadress/atom/v1.2`
- Byggnad: `https://api.lantmateriet.se/byggnad/atom/v1.1`
- Hydrografi: `https://api.lantmateriet.se/hydrografi/atom/v1.1/`
- Marktacke: `https://api.lantmateriet.se/marktacke/atom/v1.1`
- Ortnamn: `https://api.lantmateriet.se/ortnamn/atom/v1`
- Tyngdkraft: `https://api.lantmateriet.se/tyngdkraft-nedladdning/atom/v1`

## Viktig tolkning

Att API-prenumerationen ar avblockerad betyder att API:et finns pa kontot. Det betyder inte automatiskt att de gamla `dl1.lantmateriet.se`-rafilslankarna i Geotorget-orderflodet fungerar for alla produkter. Darfor sparar kartarkivet bada spar:

- API/Atom/STAC som kan fungera direkt
- Geotorget-order och rafilslankar som kan vara under behandling eller ge 401/403 tills leveransen ar klar

## Test 2026-04-13

Atom-rootfloden for administrativ indelning, belagenhetsadress, byggnad, hydrografi, marktacke, ortnamn och tyngdkraft svarar `200`.

Orsa-underfeedar hittades for:

- Byggnad Inspire Buildings, Orsa (2034)
- Marktacke Inspire Land Cover, Orsa (2034)
- Ortnamn Inspire Geographical Names, Orsa (2034)

Dataset-URL:en for Byggnad Orsa EPSG:3006 ar hittad, men direkt ZIP-nedladdning gav fortfarande `401/403` med de autentiseringsmetoder som finns i `.env`. Slutsats: index/underfeed ar tillgangligt, men faktisk datasetfil kan behova annan token/scope/prenumerationsnyckel eller portalnedladdning.

## Konton och miljo

Utifran anvandarens portalutdrag ar `bruc0004` produktionskontot med de relevanta produktionsbehorigheterna. `bruc0003` ar verifieringsmiljo, `bruc0002` saknar behorigheter och `bruc0001` ar NGP-konsument med mer begransat/verifieringsinriktat innehall.

Projektets `.env` innehaller bade ett produktionsblock for `BRUC0004` och ett verifieringsblock for `BRUC0003`. Det kan ge olika resultat beroende pa om en loader anvander forsta eller sista vardet vid dubbla nycklar. Rekommendation: hall Millbygard-produktion pa `BRUC0004` och flytta verifieringsuppgifter till en separat fil, till exempel `.env.ver`, om de ska sparas.
