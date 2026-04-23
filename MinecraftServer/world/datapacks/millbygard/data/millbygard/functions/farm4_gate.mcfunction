# Physical gate to the 4:1 magic farm zone, near the origin launch pad.
kill @e[type=text_display,tag=millbygard_farm4_gate]
fill 6 123 -3 10 126 3 minecraft:air
fill 6 123 -3 10 123 3 minecraft:amethyst_block
setblock 8 123 0 minecraft:command_block{Command:"execute as @p[distance=..4] at @s run function millbygard:farm4_enter",auto:0b}
setblock 8 124 0 minecraft:crimson_pressure_plate
fill 6 124 -3 6 126 -3 minecraft:purple_stained_glass
fill 10 124 -3 10 126 -3 minecraft:purple_stained_glass
fill 6 126 -3 10 126 -3 minecraft:purple_stained_glass
summon text_display 8 127 -3 {Tags:["millbygard_farm4_gate"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"4:1 MAGIC GARD","color":"light_purple","bold":true}'}
tellraw @a [{"text":"Magisk 4:1-gardsport skapad vid 8 124 0. Stall dig pa den roda plattan for att ga in.","color":"light_purple"}]
