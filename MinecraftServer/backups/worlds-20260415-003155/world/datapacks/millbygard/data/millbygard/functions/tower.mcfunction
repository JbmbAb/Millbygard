# Millbygard observation tower.
# Safe view point for watching build scripts run over the 1:1 ortofoto surface.
fill 16 65 -180 24 125 -172 minecraft:air
setblock 20 64 -176 minecraft:smooth_stone
fill 20 65 -176 20 117 -176 minecraft:scaffolding
fill 16 118 -180 24 118 -172 minecraft:glass
fill 16 119 -180 24 121 -180 minecraft:glass
fill 16 119 -172 24 121 -172 minecraft:glass
fill 16 119 -180 16 121 -172 minecraft:glass
fill 24 119 -180 24 121 -172 minecraft:glass
fill 17 119 -179 23 121 -173 minecraft:air
setblock 20 118 -176 minecraft:glowstone
function millbygard:control_panel
effect give @s minecraft:slow_falling 20 0 true
tp @s 20 119 -176 0 35
tellraw @s [{"text":"Millbygard observationstorn med kontrollpanel klart. Kor launch-knapparna harifran sa ser du arbetet utan att sta i vagen.","color":"green"}]
