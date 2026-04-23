# Millbygard tower control panel.
# Physical launch buttons with hidden command blocks, plus clickable chat controls.
kill @e[type=text_display,tag=millbygard_control_panel]
fill 16 119 -180 24 121 -178 minecraft:air
fill 16 119 -180 24 119 -178 minecraft:polished_deepslate
fill 16 120 -180 16 120 -179 minecraft:red_concrete
fill 18 120 -180 18 120 -179 minecraft:red_concrete
fill 20 120 -180 20 120 -179 minecraft:red_concrete
fill 22 120 -180 22 120 -179 minecraft:red_concrete
fill 24 120 -180 24 120 -179 minecraft:red_concrete
setblock 16 119 -179 minecraft:command_block{Command:"function millbygard:ortofoto_surface",auto:0b}
setblock 18 119 -179 minecraft:command_block{Command:"function millbygard:ortofoto_nearzone_500",auto:0b}
setblock 20 119 -179 minecraft:command_block{Command:"function millbygard:signs",auto:0b}
setblock 22 119 -179 minecraft:command_block{Command:"function millbygard:visual_start",auto:0b}
setblock 24 119 -179 minecraft:command_block{Command:"function millbygard:topografi_2km",auto:0b}
setblock 16 120 -179 minecraft:red_concrete
setblock 18 120 -179 minecraft:red_concrete
setblock 20 120 -179 minecraft:red_concrete
setblock 22 120 -179 minecraft:red_concrete
setblock 24 120 -179 minecraft:red_concrete
setblock 16 121 -179 minecraft:crimson_button[face=floor,facing=north]
setblock 18 121 -179 minecraft:crimson_button[face=floor,facing=north]
setblock 20 121 -179 minecraft:crimson_button[face=floor,facing=north]
setblock 22 121 -179 minecraft:crimson_button[face=floor,facing=north]
setblock 24 121 -179 minecraft:crimson_button[face=floor,facing=north]
summon text_display 16.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"ORTO","color":"red","bold":true}'}
summon text_display 18.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"500M","color":"red","bold":true}'}
summon text_display 20.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"SKYLT","color":"red","bold":true}'}
summon text_display 22.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"START","color":"red","bold":true}'}
summon text_display 24.5 122 -180.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"TOPO","color":"red","bold":true}'}
summon text_display 20 123 -178.5 {Tags:["millbygard_control_panel"],billboard:"center",text:'{"text":"MILLBYGARD CONTROL","color":"gold","bold":true}'}
tellraw @s [{"text":"\n=== MILLBYGARD CONTROL PANEL ===\n","color":"gold","bold":true},{"text":"De roda knapparna inne i tornet kor launch-kommandon. Chatten finns kvar som reserv.\n","color":"white"}]
tellraw @s [{"text":"[STOR ROD KNAPP: ORTOFOTO 1:1]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:ortofoto_surface"},"hoverEvent":{"action":"show_text","contents":"Ritar den platta 1:1-ytan fran ortofoto pa y=64."}}]
tellraw @s [{"text":"[STOR ROD KNAPP: NARZON 500M 1:1]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:ortofoto_nearzone_500"},"hoverEvent":{"action":"show_text","contents":"Ritar 500 x 500 meter i 1:1 fran raw highres-ortofoto."}}]
tellraw @s [{"text":"[STOR ROD KNAPP: SKYLTAR]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:signs"},"hoverEvent":{"action":"show_text","contents":"Lagger ut Millbygard-skyltar."}}]
tellraw @s [{"text":"[STOR ROD KNAPP: VISUELL START]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:visual_start"},"hoverEvent":{"action":"show_text","contents":"Kor ortofoto-ytan och skyltarna tillsammans."}}]
tellraw @s [{"text":"[STOR ROD KNAPP: TOPOGRAFI 2 KM]","color":"red","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:topografi_2km"},"hoverEvent":{"action":"show_text","contents":"Bygger grov topografikarta i 20 m/block-skala."}}]
tellraw @s [{"text":"[MANIFEST]","color":"gold","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:manifest"}},{"text":"  [SKYLTAR]","color":"aqua","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:signs"}},{"text":"  [TILL TORN]","color":"green","bold":true,"clickEvent":{"action":"run_command","value":"/function millbygard:tower"}}]
