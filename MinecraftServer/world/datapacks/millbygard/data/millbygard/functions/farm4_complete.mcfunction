# Complete 4:1 Millbygard build according to the local plan.
# Builds the dry farm model, then overlays official/context layers.
function millbygard:farm4_zone
function millbygard:farm4_buildings
function millbygard:farm4_data_overlay
tp @a[tag=!millbygard_no_auto_tp,distance=..900] 360 125 -160 0 35
tellraw @a [{"text":"4:1 Millbygard komplett: gard + planlager. Inget vatten har lagts ut.","color":"gold"}]
