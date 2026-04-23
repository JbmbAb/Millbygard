# Scheduled full-property build stage 98/98.
function millbygard:signs
tp @a[tag=!millbygard_no_auto_tp,distance=..900] 0 115 -100 0 35
tellraw @a [{"text":"Full property build ready: all markhojd points used, ythojd building support applied, property boundary visible.","color":"gold"}]
