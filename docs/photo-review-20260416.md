# Photo review 2026-04-16

## Current batch

Open Camera photos in `Foton/` are now being used as placement and validation input.

Generated layers:

- `output/foton_geotaggar_alla.geojson` - 88 photos with GPS from 141 scanned files.
- `output/foton_geotaggar_alla_riktningar.geojson` - direction lines where compass metadata exists.
- `output/foton_geotaggar_opencamera_20260416.geojson` - 57 GPS points from 65 Open Camera files.
- `output/foton_geotaggar_opencamera_20260416_riktningar.geojson` - 57 usable GPS + direction lines.
- `output/foton_geotaggar_nya_24.geojson` - 24 GPS points from the latest 24 files.
- `output/foton_geotaggar_nya_24_riktningar.geojson` - 24 direction lines from the latest 24 files.

## Why GPS is missing

The current missing GPS files are mostly:

- early test shots before the phone had a solid GPS lock
- panorama images, where the camera app may not keep GPS consistently
- screenshots, which normally do not contain true camera GPS metadata

Current Open Camera missing GPS list:

- `IMG_20260416_070843.jpg`
- `IMG_20260416_071158.jpg`
- `IMG_20260416_071244.jpg`
- `IMG_20260416_071806.jpg`
- `IMG_20260416_082742_PANO.jpg`
- `IMG_20260416_082843_PANO.jpg`
- `IMG_20260416_082859_PANO.jpg`
- `Screenshot_20260416_070539_Open Camera.jpg`

## Capture rule going forward

For each important place, take:

- one normal still photo with GPS and compass
- optional panorama
- one more normal still photo from almost the same spot

The still photos act as anchors for the panorama and for non-geotagged reference images.

Best next targets:

- confirm tower high point from ground level, 4 directions
- house front/back/sides, especially roof edge and foundation height
- barn/outbuilding front/back/sides
- road/driveway edges and slope breaks
- stone rows, stone piles, ditches, and forest boundary
