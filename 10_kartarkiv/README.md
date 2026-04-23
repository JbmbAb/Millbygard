# Millbygard kartarkiv

## Mal

Samla en tydlig katalog over digitala kartlager som tacker Millbygard / Orsa Stackmora 3:12 och, nar det ar rimligt, Orsa kommun. Det har ar ett bredare kartarkiv an Minecraft-/WorldPainter-pipelinen: historiska kartor, flygbilder, geologi, naturvarden, kulturmiljo, administrativa granser och andra oppna eller behorighetsstyrda karttjanster far finnas med aven om de inte ar direkt anvandbara for bygget.

Principen ar:

- allt som ar digitalt och relevant for platsen far katalogiseras
- aldre kartor och arkivspar ar extra intressanta
- visningstjanster, API:er och nedladdningsfiler hallas isar
- stora rikstackande leveranser laddas inte ner blint; vi sparar i forsta hand metadata, lagerlista och sedan Orsa/Millbygard-urval

## Plats

Projektplats: Orsa Stackmora 3:12 / Millbygard.

Nuvarande arbetsruta fran projektets workarea:

- WGS84 bbox: `14.663559524, 61.133579762, 14.666859266, 61.136740396`
- SWEREF99 TM bbox fran markhojd: `481880, 6777712, 482060, 6778065`

## Mappstruktur

```text
10_kartarkiv/
  README.md                 Den har sammanfattningen.
  KALLOR.md                 Kallor och vad de kan ge.
  discover_kartarkiv.py     Uppdaterar WMS/API-status och lagerlistor.
  01_kallor/                Raa capabilities/XML och kallsvar.
  02_lagerindex/            Sammanstallningar av hittade lager.
  03_previewbilder/         Smabilder/utdrag over Millbygard nar det ar mojligt.
  04_nedladdat/             Framtida lokala Orsa-/Millbygard-klipp.
  05_arkivsppar/            Anteckningar for arkiv som kraver manuell sokning.
```

## Finns lokalt nu

- Markhojdmodell 1 m, anvands som huvudkalla for terrang: `data/orsa_stackmora_3_12_markhojd.tif`
- Markhojdmodell grid 50+, grov stoddata: `data/orsa_stackmora_3_12_markhojd_grid50_677_48_7500.xyz`
- Laserdata skog, Orsa/Stackmora-ruta: `01_data_raw/laserdata_skog/20D026_677_48_7500.laz`
- Historiskt ortofoto via WMS, preview sparad: `04_references/ortofoto_historiska/orsa_stackmora_3_12_OI.Histortho_color_2005.png`
- Fastighets-/workarea-geometri fran tidigare lokal export: `data/orsa_stackmora_3_12_workarea.geojson`
- Geotorget-orderinventering: `data/geotorget_orders_manifest.json`

## Gjort hittills

- Geotorget-status har inventerats for de lager som redan bestallts.
- Markhojdmodell 1 m har laddats ner, klippts och exporterats till heightmap.
- Markhojdmodell grid 50+ har extraherats for relevant ruta.
- Laserdata skog har hittats i den stora leveransen och bara relevant 2,5 x 2,5 km-ruta har laddats ner.
- Historiskt ortofoto som visningstjanst har testats och en preview over Millbygard har sparats.
- Ett separat kartarkiv har skapats sa externa och historiska kartor inte blandas ihop med byggpipelinen.

## Saknas eller vantar

Det har saknas fortfarande som lokala byggfiler:

- `data/orsa_stackmora_3_12_byggnader.geojson`
- `data/orsa_stackmora_3_12_fastighet.gpkg`

Enligt nuvarande inventering ar byggnad och fastighet kopplade till order som fortfarande behandlas eller dar raa nedladdningslankar svarar 401/403. Visningstjanster kan anda fungera under tiden.

## Korning

Uppdatera WMS/API-katalogen:

```powershell
python .\10_kartarkiv\discover_kartarkiv.py
```

Resultat skrivs till:

- `10_kartarkiv/02_lagerindex/wms_sources_status.json`
- `10_kartarkiv/02_lagerindex/wms_layers.json`
- `10_kartarkiv/01_kallor/*_capabilities.xml`

## Nasta steg

1. Lagg till fler kallor i `KALLOR.md` och `discover_kartarkiv.py` nar vi hittar dem.
2. Kor discovery igen och kontrollera vilka tjanster som svarar.
3. For WMS-lager: skapa previewbilder over Millbygard/Orsa innan full nedladdning.
4. For arkiv utan API: dokumentera sokvag, kartnamn, ar och lank i `05_arkivsppar/`.
5. For stora rikstackande nedladdningar: hamta bara kommun-/rut-/bbox-urval om det gar.
