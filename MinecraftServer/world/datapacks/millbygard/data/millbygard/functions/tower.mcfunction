# Millbygard observation tower.
# Safe view point for watching build scripts run over the 1:1 ortofoto surface.
function millbygard:tower_static
effect give @s minecraft:slow_falling 20 0 true
tp @s 20 119 -176 0 35
tellraw @s [{"text":"Millbygard observationstorn med kontrollpanel klart. Kor launch-knapparna harifran sa ser du arbetet utan att sta i vagen.","color":"green"}]
