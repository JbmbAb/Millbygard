# Red physical launch pad near spawn/origin height.
kill @e[type=text_display,tag=millbygard_launch_pad]
fill -3 124 -3 3 127 3 minecraft:air
fill -3 123 -3 3 123 3 minecraft:red_concrete
setblock 0 123 0 minecraft:command_block{Command:"execute as @p[distance=..4] at @s run function millbygard:jump_to_tower",auto:0b}
setblock 0 124 0 minecraft:crimson_pressure_plate
summon text_display 0 127 -3 {Tags:["millbygard_launch_pad"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,transformation:{scale:[2f,2f,2f]},text:'{"text":"HOPPA PA RODA PLATTAN -> TORN","color":"red","bold":true}'}
tellraw @a [{"text":"Rod launch-platta skapad vid 0 124 0. Hoppa eller stall dig pa plattan for att bygga och aka till tornet.","color":"red"}]
