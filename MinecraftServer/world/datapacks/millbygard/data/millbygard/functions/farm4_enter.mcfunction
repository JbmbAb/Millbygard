# Enter the 4:1 magic farm zone.
playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 1 1.1
particle minecraft:end_rod ~ ~1 ~ 0.5 0.5 0.5 0.02 40 force @s
function millbygard:farm4_complete
effect give @s minecraft:slow_falling 10 0 true
tp @s 360 125 -160 0 35
