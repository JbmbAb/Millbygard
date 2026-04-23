# Minecraft-kommandon for Millbygard

Kortaste vagen nar servern redan ar igang:

```text
reload
function millbygard:launch_pad
```

Skriv kommandona ovan i serverfonstret pa datorn. I Minecraft-chatten skriver du samma sak med slash:

```text
/reload
/function millbygard:launch_pad
```

Efter det behover du inte skriva mer: hoppa eller stall dig pa den roda plattan vid `0 124 0`.
Den bygger tornet och skickar spelaren dit.

Magisk 4:1-gardszon:

```text
function millbygard:farm4_gate
```

Hoppa eller stall dig pa portens roda platta vid `8 124 0`. Den skickar spelaren till en separat gardzon dar `1 meter = 4 block`.

Planerad mjuk overgang:

```text
data/orsa_stackmora_3_12_scale_transition_zones.geojson
```

Detta ar just nu ett GIS-/planeringslager: 0-80 m ar 4:1, 80-140 m glider mjukt till 1:1 och ytterzonen ar 1:1. Fastighetsgransen ska fortfarande visas separat som rod linje/block ovanpa underlaget.

## Enkla startkommandon

```text
function millbygard:quick_start
```

Bygger launch-platta, torn och trygg startvy: ortofoto, fastighetsgranser och skyltar.

```text
function millbygard:launch_pad
```

Bygger en rod fysisk platta vid spawn/origin. Hoppa pa den for att bygga tornet och aka dit.

```text
function millbygard:farm4_gate
function millbygard:farm4_complete
function millbygard:farm4_data_overlay
function millbygard:full_property_complete
```

Bygger porten, den kompletta torra 4:1-zonen, planlagret med fastighetsgrans, byggnadsvektor, hojdankare, fotopunkter, vagar, grundvattenmarkering under markytan och tornpunkt.

`full_property_complete` bygger hela fastigheten i 1:1-terrang fran alla 29 080 anvandbara 1 m-markhojdpunkter. Den kor 98 stegade etapper, lagger byggnadsstod fran ythojd och ritar fastighetsgransen synligt ovanpa terrangen. Den skapar inga vattenblock.

```text
function millbygard:visual_start
```

Bygger ortofoto, fastighetsgranser och skyltar utan att bygga om tornet.

```text
function millbygard:tower
```

Bygger observationstorn och kontrollpanel.

## Kartlager

```text
function millbygard:ortofoto_surface
function millbygard:property_1to1
function millbygard:signs
function millbygard:topografi_2km
```

`property_1to1` visar fastighetsgranserna som roda block ovanpa ortofotot.

## Tunga testkommandon

```text
function millbygard:ortofoto_nearzone_500
```

Bygger en stor 500 x 500 meter 1:1-yta. Den ar tyngre och kan ta en stund.

## Teleport

```text
tp .VoicedGecko75 20 119 -176
tp .NewCobra9911119 20 119 -176
```

Teleporterar spelarna till tornet.

## Roda tryckplattor i tornet

```text
ORTO  = ortofoto-yta
500M  = stor 500 x 500 m-yta
SKYLT = skyltar
START = ortofoto + fastighetsgranser + skyltar
TOPO  = topografi-oversikt
```

Hoppa eller stall dig pa en rod tryckplatta. Det fungerar battre pa Xbox an att sikta pa smala knappar.
