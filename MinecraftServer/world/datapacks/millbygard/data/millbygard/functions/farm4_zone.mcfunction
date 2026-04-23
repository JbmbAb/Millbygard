# Millbygard 4:1 zone shell.
# Center 360 80 -160. Scale: 1 real meter = 4 Minecraft blocks. No water.
kill @e[type=text_display,tag=millbygard_farm4]
fill 240 80 -280 360 80 -40 minecraft:grass_block
fill 361 80 -280 480 80 -40 minecraft:grass_block
fill 240 81 -280 480 83 -280 minecraft:amethyst_block
fill 240 81 -40 480 83 -40 minecraft:amethyst_block
fill 240 81 -280 240 83 -40 minecraft:amethyst_block
fill 480 81 -280 480 83 -40 minecraft:amethyst_block
fill 240 84 -280 480 88 -280 minecraft:purple_stained_glass
fill 240 84 -40 480 88 -40 minecraft:purple_stained_glass
fill 240 84 -280 240 88 -40 minecraft:purple_stained_glass
fill 480 84 -280 480 88 -40 minecraft:purple_stained_glass
fill 360 81 -280 360 81 -40 minecraft:white_concrete
fill 240 81 -160 480 81 -160 minecraft:white_concrete
fill 356 81 -164 364 81 -156 minecraft:gold_block
fill 360 82 -160 360 85 -160 minecraft:glowstone
fill 360 81 -160 400 81 -160 minecraft:yellow_concrete
setblock 360 81 -276 minecraft:command_block{Command:"execute as @p[distance=..4] at @s run function millbygard:farm4_return",auto:0b}
setblock 360 82 -276 minecraft:crimson_pressure_plate
function millbygard:farm4_buildings
summon text_display 360 88 -160 {Tags:["millbygard_farm4"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"MILLBYGARD 4:1","color":"light_purple","bold":true}'}
summon text_display 360 86 -154 {Tags:["millbygard_farm4"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"1 meter = 4 block. Inget vatten. Gul linje = 10 m.","color":"white"}'}
summon text_display 360 85 -276 {Tags:["millbygard_farm4"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"RETUR TILL TORN","color":"red","bold":true}'}
tellraw @a [{"text":"4:1-zonen ar klar och torr: gard, skala och returplatta.","color":"light_purple"}]
