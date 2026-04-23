# Generated Millbygard topografi overview.
# Scale: 1 block = 20 meters. Origin: 0 90 320.
kill @e[type=text_display,tag=millbygard_topografi]
fill -105 90 211 -77 94 429 minecraft:air
fill -76 90 211 -48 94 429 minecraft:air
fill -47 90 211 -19 94 429 minecraft:air
fill -18 90 211 10 94 429 minecraft:air
fill 11 90 211 39 94 429 minecraft:air
fill 40 90 211 68 94 429 minecraft:air
fill 69 90 211 97 94 429 minecraft:air
fill 98 90 211 105 94 429 minecraft:air
fill -105 90 211 40 90 429 minecraft:grass_block
fill 41 90 211 105 90 429 minecraft:grass_block
function millbygard:topografi_2km_land_0
function millbygard:topografi_2km_land_1
function millbygard:topografi_2km_land_2
function millbygard:topografi_2km_land_3
function millbygard:topografi_2km_land_4
function millbygard:topografi_2km_roads
function millbygard:topografi_2km_hydro
function millbygard:topografi_2km_buildings
function millbygard:topografi_2km_property
summon text_display -105 96 208 {Tags:["millbygard_topografi"],billboard:"center",text:'{"text":"Millbygard Topografi 2 km - 1 block = 20 m","color":"gold","bold":true}'}
summon text_display -105 94 208 {Tags:["millbygard_topografi"],billboard:"center",text:'{"text":"Rod linje = fastighet, tegel = byggnad, gra/gul/brun = vagar, bla = vatten, gron = skog","color":"white"}'}
