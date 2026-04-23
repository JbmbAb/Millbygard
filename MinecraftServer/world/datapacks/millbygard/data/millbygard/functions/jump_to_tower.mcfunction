# Run as the player standing on the red launch pad.
playsound minecraft:block.note_block.pling master @s ~ ~ ~ 1 1.4
particle minecraft:cloud ~ ~1 ~ 0.5 0.2 0.5 0.02 25 force @s
function millbygard:tower
effect give @s minecraft:slow_falling 20 0 true
tp @s 20 119 -176 0 35
