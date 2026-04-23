# Millbygard tower control panel.
# Physical launch buttons with hidden command blocks, plus clickable chat controls.
kill @e[type=text_display,tag=millbygard_control_panel]
fill 16 119 -180 24 121 -172 minecraft:air
fill 16 119 -180 24 119 -172 minecraft:polished_deepslate
setblock 16 120 -179 minecraft:red_concrete
setblock 20 120 -179 minecraft:red_concrete
setblock 24 120 -179 minecraft:red_concrete
setblock 16 120 -173 minecraft:red_concrete
setblock 24 120 -173 minecraft:red_concrete
setblock 16 120 -179 minecraft:command_block{Command:"execute as @p[distance=..5] at @s run function millbygard:button_ortofoto",auto:0b}
setblock 20 120 -179 minecraft:command_block{Command:"execute as @p[distance=..5] at @s run function millbygard:button_500m",auto:0b}
setblock 24 120 -179 minecraft:command_block{Command:"execute as @p[distance=..5] at @s run function millbygard:button_signs",auto:0b}
setblock 16 120 -173 minecraft:command_block{Command:"execute as @p[distance=..5] at @s run function millbygard:button_start",auto:0b}
setblock 24 120 -173 minecraft:command_block{Command:"execute as @p[distance=..5] at @s run function millbygard:button_topo",auto:0b}
setblock 16 121 -179 minecraft:crimson_pressure_plate
setblock 20 121 -179 minecraft:crimson_pressure_plate
setblock 24 121 -179 minecraft:crimson_pressure_plate
setblock 16 121 -173 minecraft:crimson_pressure_plate
setblock 24 121 -173 minecraft:crimson_pressure_plate
summon text_display 16.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"ORTO","color":"red","bold":true}'}
summon text_display 20.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"500M","color":"red","bold":true}'}
summon text_display 24.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"SKYLT","color":"red","bold":true}'}
summon text_display 16.5 122 -172.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"START","color":"red","bold":true}'}
summon text_display 24.5 122 -172.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"TOPO","color":"red","bold":true}'}
summon text_display 20 123 -176.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"MILLBYGARD CONTROL","color":"gold","bold":true}'}
tellraw @a [{"text":"\n=== MILLBYGARD CONTROL PANEL ===\n","color":"gold","bold":true},{"text":"Plattorna ar isar och startar bara nar du gar pa exakt knapp. Ga av plattan innan nasta tryck.\n","color":"white"}]
tellraw @a [{"text":"[STOR ROD KNAPP: ORTOFOTO 1:1]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:ortofoto_surface"},"hoverEvent":{"action":"show_text","contents":"Ritar den platta 1:1-ytan fran ortofoto pa y=64."}}]
tellraw @a [{"text":"[STOR ROD KNAPP: NARZON 500M 1:1]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:ortofoto_nearzone_500"},"hoverEvent":{"action":"show_text","contents":"Ritar 500 x 500 meter i 1:1 fran raw highres-ortofoto."}}]
tellraw @a [{"text":"[STOR ROD KNAPP: SKYLTAR]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:signs"},"hoverEvent":{"action":"show_text","contents":"Lagger ut Millbygard-skyltar."}}]
tellraw @a [{"text":"[STOR ROD KNAPP: VISUELL START]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:visual_start"},"hoverEvent":{"action":"show_text","contents":"Kor ortofoto-ytan, fastighetsgranserna och skyltarna tillsammans."}}]
tellraw @a [{"text":"[STOR ROD KNAPP: TOPOGRAFI 2 KM]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:topografi_2km"},"hoverEvent":{"action":"show_text","contents":"Bygger grov topografikarta i 20 m/block-skala."}}]
tellraw @a [{"text":"[MANIFEST]","color":"gold","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:manifest"}},{"text":"  [GRANS 1:1]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:property_1to1"}},{"text":"  [SKYLTAR]","color":"aqua","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:signs"}},{"text":"  [TILL TORN]","color":"green","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:tower"}}]
