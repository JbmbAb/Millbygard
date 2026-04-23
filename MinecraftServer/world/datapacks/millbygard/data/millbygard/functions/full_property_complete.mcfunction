# Scheduled complete full-property build.
# Uses all 1 m markhojd terrain cells, ythojd building support, property overlay and labels.
schedule clear millbygard:full_property_stage_00
schedule function millbygard:full_property_stage_00 1t replace
tellraw @a [{"text":"Startar full fastighetsbyggnad i 98 etapper. Lat servern arbeta klart innan ni gar in.","color":"gold"}]
