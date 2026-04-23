# Millbygard scale transition and map layer checklist

This document records the current build strategy so the property boundary, scale zones, photos and map layers do not drift apart.

## Scale strategy

Keep the cadastral/property geometry as the master boundary:

- `data/orsa_stackmora_3_12_workarea.geojson`
- `data/orsa_stackmora_3_12_split.geojson`

Do not replace the property boundary with a circle. The boundary must remain visible as an overlay, normally as a red line/block layer.

Use circles as coverage and scale-control layers:

- `data/orsa_stackmora_3_12_workarea_circle.geojson` covers the whole property from a minimum enclosing circle.
- `data/orsa_stackmora_3_12_workarea_circle_overlay.geojson` contains both the coverage circle and the property boundary.
- `data/orsa_stackmora_3_12_scale_transition_zones.geojson` contains the 4:1 detail zone, soft transition ring, 1:1 context ring and property boundary.

Current scale-zone defaults:

```text
Center source: data/orsa_stackmora_3_12_byggnader.geojson
Center:        61.134543558, 14.664974135
0-80 m:        4:1 detail zone around the farm
80-140 m:      smooth transition from 4:1 to 1:1
140-255.79 m:  1:1 context zone covering the full property
```

The soft transition formula is:

```text
if d <= 80: scale = 4.0
elif d >= 140: scale = 1.0
else:
  t = (d - 80) / 60
  s = t*t*(3 - 2*t)
  scale = 4.0 + (1.0 - 4.0) * s
```

Regenerate the zones after changing building center, radius choices or property geometry:

```powershell
python tools/create_workarea_circle.py
python tools/create_scale_transition_zones.py
```

## Tower site

Use the highest valid DEM cell inside the property workarea as the tower anchor unless field photos override it later.

Current tower point:

```text
Layer:      data/orsa_stackmora_3_12_tower_site.geojson
Latitude:   61.133607499
Longitude:  14.665000889
Elevation:  250.90 m
Source:     data/orsa_stackmora_3_12_markhojd.tif
```

Regenerate after changing DEM or property geometry:

```powershell
python tools/extract_tower_site_highest_point.py
```

## Photo workflow

New property photos are expected and should be used as validation/detail input, not as the main height source.

Use Open Camera with:

```text
Store location data
Store compass direction
Require location data
```

Photos should land in:

```text
Foton/
```

For each useful photo, preserve:

- GPS position
- altitude if present
- compass direction
- short note: facade, road, tower, slope, stone row, back side, detail

Current generated photo layers:

- `output/foton_geotaggar_alla.geojson` - all photos with readable GPS.
- `output/foton_geotaggar_alla_riktningar.geojson` - camera direction lines where compass metadata exists.
- `output/foton_geotaggar_opencamera_20260416.geojson` - Open Camera batch from 2026-04-16.
- `output/foton_geotaggar_opencamera_20260416_riktningar.geojson` - Open Camera direction lines.
- `output/foton_geotaggar_nya_24.geojson` - latest 24 photos; all have GPS and compass direction.
- `output/foton_geotaggar_nya_24_riktningar.geojson` - latest 24 direction lines.

GPS gaps in the current Open Camera batch are mostly early test shots before GPS lock and panorama files. Use normal still photos before/after panorama shots as anchor points.

## Map layer inventory

Core property and workarea:

- `data/orsa_stackmora_3_12_workarea.geojson` - master merged property boundary.
- `data/orsa_stackmora_3_12_split.geojson` - individual property parts.
- `exports/millbygard_local_parcels.json` - local meter coordinates for Minecraft support.

Official Lantmateriet/STAC layers:

- Ortofoto: `01_data_raw/ortofoto/orsa_stackmora_3_12_ortofoto_highres.tif`, clipped copy `data/orsa_stackmora_3_12_ortofoto.tif`.
- Markhojd 1 m: `01_data_raw/markhojd/orsa_stackmora_3_12_markhojd_highres.tif`, clipped copy `data/orsa_stackmora_3_12_markhojd.tif`.
- Ythojdmodell 0.25 m: raw zip is `01_data_raw/ythojd/orsa_stackmora_3_12_ythojd_677_48_7500_2024.zip`; unpacked delivery is under `C:\Users\jimmy\Desktop\MiljoBeslut_Produktdata\Kartor\Ythojd_677_48_7500_2024`.
- Ythojd clipped outputs: `data/orsa_stackmora_3_12_ythojd_dsm.tif`, `data/orsa_stackmora_3_12_ythojd_trueortho.tif`, `data/orsa_stackmora_3_12_ythojd_class.tif`, `data/orsa_stackmora_3_12_ythojd_above_ground.tif`.
- Byggnader: downloaded from `Byggnad nedladdning, vektor`, clipped output is `data/orsa_stackmora_3_12_byggnader.geojson`.
- Building measurements: `output/building_measurements_20260416.csv` and `.json` contain approximate length, width and area from the clipped polygons.
- Building surface heights: `output/building_surface_heights_20260416.csv` and `.json` contain first-pass roof/surface heights from ythojd DSM minus markhojd.
- Fastighet: resolved item exists, but `data/orsa_stackmora_3_12_fastighet.gpkg` is still missing.

Height and terrain:

- `03_heightmap/orsa_stackmora_3_12_heightmap_16bit.png` and `.json` are the current draft heightmap.
- `data/orsa_stackmora_3_12_markhojd_grid50_677_48_7500.xyz` is a coarse Grid 50+ control layer.
- `01_data_raw/laserdata_skog/20D026_677_48_7500.laz` is available as detailed laser/forest support.
- `data/orsa_stackmora_3_12_ythojd_above_ground.tif` supports roofs, trees and other above-ground detail; it is not the ground terrain source.

Topografi context:

- Roads: `data/topografi/orsa_stackmora_3_12_topografi_vagar_2km.geojson`
- Land: `data/topografi/orsa_stackmora_3_12_topografi_mark_2km.geojson`
- Buildings/structures: `data/topografi/orsa_stackmora_3_12_topografi_byggnadsverk_2km.geojson`
- Hydrography: `data/topografi/orsa_stackmora_3_12_topografi_hydrografi_2km.geojson`
- Text labels: `data/topografi/orsa_stackmora_3_12_topografi_text_2km.geojson`

Environmental/PostGIS support:

- SGU ground layer, groundwater, groundwater magazine, permeability and catchment layers are under `data/postgis_import/`.
- These are context/control layers, not first-pass Minecraft geometry.

## Minecraft finish export

The Minecraft completion layer is generated by:

```powershell
python tools/generate_minecraft_finish_layers.py
```

It writes:

- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/farm4_complete.mcfunction`
- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/farm4_data_overlay.mcfunction`
- `data/minecraft_finish_layers_manifest.json`

Included in the completion layer:

- red master property boundary and red glass split-boundaries
- green/orange/light-blue scale rings for 4:1 detail, smooth transition and full-property context
- Lantmateriet building vector footprints
- tower site from the highest DEM point
- photo GPS points and compass direction lines
- Topografi road lines and hydrography/groundwater as cyan glass cues below the surface, not water blocks
- Markhojd height anchor points

The 4:1 farm remains a readable Minecraft model. The overlay is the plan/control layer that ties the model back to the official and photo-derived data.

## Full 1:1 terrain export

The full-property terrain export is generated by:

```powershell
python tools/generate_minecraft_full_property_terrain.py
```

It writes a staged Minecraft build:

- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/full_property_complete.mcfunction`
- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/full_property_stage_*.mcfunction`
- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/full_property_terrain_*.mcfunction`
- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/full_property_buildings.mcfunction`
- `MinecraftServer/world/datapacks/millbygard/data/millbygard/functions/full_property_boundary.mcfunction`
- `data/minecraft_full_property_terrain_manifest.json`

Current export uses all 29,080 valid 1 m Markhojd cells inside the property/workarea. Elevation is preserved at 1 block per meter from y=70 to y=103. Ythojd is used only as selective building roof/surface-height support, because using every 0.25 m DSM point as blocks would be too heavy for a playable first pass.

The property boundary remains visible as red concrete on top of the generated terrain. Hydrology/groundwater is not rendered as surface water in this full terrain export.

## Not missed, but still pending

- Rebuild heightmap coverage using the scale/context area if the current clipped heightmap does not cover the tower/property context.
- `data/orsa_stackmora_3_12_fastighet.gpkg` is still missing as a standalone working file, although the local workarea/split GeoJSON boundary is available and used.
- Full 1:1 terrain is now exported as staged Minecraft functions. Later work can improve material classification and add more photo-confirmed detail, but the height surface is no longer only anchors.
- New incoming property photos should still be rerun through the geotag/compass extractor before they are treated as final evidence.
