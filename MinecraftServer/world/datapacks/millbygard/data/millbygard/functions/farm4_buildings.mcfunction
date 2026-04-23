# Millbygard 4:1 complete farm model.
# Scale: 1 real meter = 4 Minecraft blocks. No water.
# Coordinates are a readable farm model, not the 1:1 ortofoto layer.

kill @e[type=text_display,tag=millbygard_farm4_building]

# Reset farm volume in chunks under Minecraft's /fill limit.
fill 292 82 -244 331 93 -190 minecraft:air
fill 292 94 -244 331 105 -190 minecraft:air
fill 292 106 -244 331 116 -190 minecraft:air
fill 292 82 -189 331 93 -135 minecraft:air
fill 292 94 -189 331 105 -135 minecraft:air
fill 292 106 -189 331 116 -135 minecraft:air
fill 292 82 -134 331 93 -80 minecraft:air
fill 292 94 -134 331 105 -80 minecraft:air
fill 292 106 -134 331 116 -80 minecraft:air
fill 332 82 -244 371 93 -190 minecraft:air
fill 332 94 -244 371 105 -190 minecraft:air
fill 332 106 -244 371 116 -190 minecraft:air
fill 332 82 -189 371 93 -135 minecraft:air
fill 332 94 -189 371 105 -135 minecraft:air
fill 332 106 -189 371 116 -135 minecraft:air
fill 332 82 -134 371 93 -80 minecraft:air
fill 332 94 -134 371 105 -80 minecraft:air
fill 332 106 -134 371 116 -80 minecraft:air
fill 372 82 -244 411 93 -190 minecraft:air
fill 372 94 -244 411 105 -190 minecraft:air
fill 372 106 -244 411 116 -190 minecraft:air
fill 372 82 -189 411 93 -135 minecraft:air
fill 372 94 -189 411 105 -135 minecraft:air
fill 372 106 -189 411 116 -135 minecraft:air
fill 372 82 -134 411 93 -80 minecraft:air
fill 372 94 -134 411 105 -80 minecraft:air
fill 372 106 -134 411 116 -80 minecraft:air
fill 412 82 -244 451 93 -190 minecraft:air
fill 412 94 -244 451 105 -190 minecraft:air
fill 412 106 -244 451 116 -190 minecraft:air
fill 412 82 -189 451 93 -135 minecraft:air
fill 412 94 -189 451 105 -135 minecraft:air
fill 412 106 -189 451 116 -135 minecraft:air
fill 412 82 -134 451 93 -80 minecraft:air
fill 412 94 -134 451 105 -80 minecraft:air
fill 412 106 -134 451 116 -80 minecraft:air
fill 452 82 -244 476 93 -190 minecraft:air
fill 452 94 -244 476 105 -190 minecraft:air
fill 452 106 -244 476 116 -190 minecraft:air
fill 452 82 -189 476 93 -135 minecraft:air
fill 452 94 -189 476 105 -135 minecraft:air
fill 452 106 -189 476 116 -135 minecraft:air
fill 452 82 -134 476 93 -80 minecraft:air
fill 452 94 -134 476 105 -80 minecraft:air
fill 452 106 -134 476 116 -80 minecraft:air

# Ground: dry yard, field, forest edge, road and slope cues.
fill 292 81 -244 476 81 -80 minecraft:grass_block
fill 312 81 -226 456 81 -134 minecraft:gravel
fill 344 81 -238 370 81 -80 minecraft:coarse_dirt
fill 292 81 -168 476 81 -154 minecraft:dirt_path
fill 396 82 -180 476 82 -150 minecraft:coarse_dirt
fill 402 83 -174 476 83 -166 minecraft:gravel
fill 292 82 -244 324 82 -228 minecraft:moss_block
fill 292 83 -244 324 83 -228 minecraft:short_grass
fill 292 82 -96 476 82 -80 minecraft:grass_block
fill 292 83 -96 476 83 -80 minecraft:short_grass
fill 292 82 -244 476 82 -244 minecraft:oak_fence
fill 292 82 -80 476 82 -80 minecraft:oak_fence
fill 292 82 -244 292 82 -80 minecraft:oak_fence
fill 476 82 -244 476 82 -80 minecraft:oak_fence
setblock 360 82 -244 minecraft:oak_fence_gate[facing=south]
setblock 361 82 -244 minecraft:oak_fence_gate[facing=south]

# Main house: approx 15.6 x 8.3 m -> 63 x 34 blocks.
fill 329 81 -176 391 81 -143 minecraft:stone_bricks
fill 330 82 -175 390 82 -144 minecraft:spruce_planks
fill 329 83 -176 391 96 -176 minecraft:red_terracotta
fill 329 83 -143 391 96 -143 minecraft:red_terracotta
fill 329 83 -176 329 96 -143 minecraft:red_terracotta
fill 391 83 -176 391 96 -143 minecraft:red_terracotta
fill 329 83 -176 329 96 -176 minecraft:white_concrete
fill 391 83 -176 391 96 -176 minecraft:white_concrete
fill 329 83 -143 329 96 -143 minecraft:white_concrete
fill 391 83 -143 391 96 -143 minecraft:white_concrete
fill 357 83 -143 363 91 -143 minecraft:dark_oak_planks
fill 358 84 -143 362 91 -143 minecraft:air
fill 340 87 -143 347 92 -143 minecraft:glass_pane
fill 373 87 -143 380 92 -143 minecraft:glass_pane
fill 340 87 -176 347 92 -176 minecraft:glass_pane
fill 373 87 -176 380 92 -176 minecraft:glass_pane
fill 329 87 -166 329 92 -154 minecraft:glass_pane
fill 391 87 -166 391 92 -154 minecraft:glass_pane
fill 326 97 -180 394 97 -139 minecraft:deepslate_tiles
fill 326 98 -178 394 98 -141 minecraft:deepslate_tiles
fill 326 99 -176 394 99 -143 minecraft:deepslate_tiles
fill 326 100 -174 394 100 -145 minecraft:deepslate_tiles
fill 326 101 -172 394 101 -147 minecraft:deepslate_tiles
fill 326 102 -170 394 102 -149 minecraft:deepslate_tiles
fill 326 103 -168 394 103 -151 minecraft:deepslate_tiles
fill 326 104 -166 394 104 -153 minecraft:deepslate_tiles
fill 326 105 -164 394 105 -155 minecraft:deepslate_tiles
fill 326 106 -162 394 106 -157 minecraft:deepslate_tiles
fill 326 107 -160 394 107 -159 minecraft:deepslate_tiles
setblock 380 108 -162 minecraft:brick_wall
setblock 380 109 -162 minecraft:brick_wall
setblock 380 110 -162 minecraft:campfire[lit=false]

# Long barn/outbuilding: approx 32.2 x 10.6 m -> 130 x 43 blocks.
fill 330 81 -226 459 81 -184 minecraft:stone_bricks
fill 331 82 -225 458 82 -185 minecraft:spruce_planks
fill 330 83 -226 459 100 -226 minecraft:red_terracotta
fill 330 83 -184 459 100 -184 minecraft:red_terracotta
fill 330 83 -226 330 100 -184 minecraft:red_terracotta
fill 459 83 -226 459 100 -184 minecraft:red_terracotta
fill 386 83 -184 402 96 -184 minecraft:dark_oak_planks
fill 387 84 -184 401 96 -184 minecraft:air
fill 338 88 -184 350 94 -184 minecraft:glass_pane
fill 432 88 -184 444 94 -184 minecraft:glass_pane
fill 338 88 -226 350 94 -226 minecraft:glass_pane
fill 432 88 -226 444 94 -226 minecraft:glass_pane
fill 326 101 -230 463 101 -180 minecraft:dark_oak_planks
fill 326 102 -228 463 102 -182 minecraft:dark_oak_planks
fill 326 103 -226 463 103 -184 minecraft:dark_oak_planks
fill 326 104 -224 463 104 -186 minecraft:dark_oak_planks
fill 326 105 -222 463 105 -188 minecraft:dark_oak_planks
fill 326 106 -220 463 106 -190 minecraft:dark_oak_planks
fill 326 107 -218 463 107 -192 minecraft:dark_oak_planks
fill 326 108 -216 463 108 -194 minecraft:dark_oak_planks
fill 326 109 -214 463 109 -196 minecraft:dark_oak_planks
fill 326 110 -212 463 110 -198 minecraft:dark_oak_planks
fill 326 111 -210 463 111 -200 minecraft:dark_oak_planks
fill 326 112 -208 463 112 -202 minecraft:dark_oak_planks
fill 326 113 -206 463 113 -204 minecraft:dark_oak_planks

# Small shed: approx 8.2 x 6.8 m -> 34 x 28 blocks.
fill 304 81 -125 337 81 -98 minecraft:stone_bricks
fill 305 82 -124 336 82 -99 minecraft:spruce_planks
fill 304 83 -125 337 92 -125 minecraft:red_terracotta
fill 304 83 -98 337 92 -98 minecraft:red_terracotta
fill 304 83 -125 304 92 -98 minecraft:red_terracotta
fill 337 83 -125 337 92 -98 minecraft:red_terracotta
fill 316 83 -98 326 90 -98 minecraft:dark_oak_planks
fill 317 84 -98 325 90 -98 minecraft:air
fill 307 87 -125 314 91 -125 minecraft:glass_pane
fill 327 87 -125 334 91 -125 minecraft:glass_pane
fill 302 93 -129 339 93 -94 minecraft:deepslate_tiles
fill 302 94 -127 339 94 -96 minecraft:deepslate_tiles
fill 302 95 -125 339 95 -98 minecraft:deepslate_tiles
fill 302 96 -123 339 96 -100 minecraft:deepslate_tiles
fill 302 97 -121 339 97 -102 minecraft:deepslate_tiles
fill 302 98 -119 339 98 -104 minecraft:deepslate_tiles
fill 302 99 -117 339 99 -106 minecraft:deepslate_tiles
fill 302 100 -115 339 100 -108 minecraft:deepslate_tiles
fill 302 101 -113 339 101 -110 minecraft:deepslate_tiles
fill 302 102 -112 339 102 -111 minecraft:deepslate_tiles

# Yard details and visible scale references.
fill 329 82 -139 391 82 -139 minecraft:yellow_concrete
fill 397 82 -184 397 82 -143 minecraft:yellow_concrete
fill 330 82 -230 459 82 -230 minecraft:yellow_concrete
fill 304 82 -94 337 82 -94 minecraft:yellow_concrete
fill 352 82 -166 368 82 -154 minecraft:dirt_path
fill 352 82 -236 368 82 -184 minecraft:dirt_path
fill 352 82 -143 368 82 -90 minecraft:dirt_path
setblock 355 83 -204 minecraft:lantern[hanging=false]
setblock 365 83 -204 minecraft:lantern[hanging=false]
setblock 346 82 -186 minecraft:barrel
setblock 348 82 -186 minecraft:barrel
setblock 350 82 -186 minecraft:composter
setblock 408 82 -176 minecraft:hay_block
setblock 410 82 -176 minecraft:hay_block
setblock 408 83 -176 minecraft:hay_block
setblock 410 83 -176 minecraft:hay_block
setblock 412 82 -176 minecraft:crafting_table
setblock 414 82 -176 minecraft:chest[facing=south]

# Stone piles and slope/forest cues from photos.
fill 306 82 -222 326 82 -199 minecraft:cobblestone
fill 307 83 -221 323 83 -202 minecraft:mossy_cobblestone
fill 309 84 -219 320 84 -205 minecraft:stone
fill 314 85 -214 318 85 -209 minecraft:andesite
fill 334 82 -219 350 82 -202 minecraft:cobblestone
fill 336 83 -217 348 83 -205 minecraft:mossy_cobblestone
setblock 311 82 -154 minecraft:andesite
setblock 312 82 -154 minecraft:andesite
setblock 311 83 -154 minecraft:andesite
setblock 312 82 -153 minecraft:stone
setblock 312 83 -153 minecraft:mossy_cobblestone
setblock 313 82 -154 minecraft:cobblestone
setblock 318 82 -210 minecraft:spruce_log
setblock 318 83 -210 minecraft:spruce_log
setblock 318 84 -210 minecraft:spruce_log
setblock 318 85 -210 minecraft:spruce_log
fill 316 86 -212 320 88 -208 minecraft:spruce_leaves
setblock 310 82 -88 minecraft:birch_log
setblock 310 83 -88 minecraft:birch_log
setblock 310 84 -88 minecraft:birch_log
setblock 310 85 -88 minecraft:birch_log
fill 308 86 -90 312 89 -86 minecraft:birch_leaves
setblock 460 82 -92 minecraft:spruce_log
setblock 460 83 -92 minecraft:spruce_log
setblock 460 84 -92 minecraft:spruce_log
setblock 460 85 -92 minecraft:spruce_log
fill 457 86 -95 463 90 -89 minecraft:spruce_leaves

# Labels without transformation NBT to avoid display-entity errors.
summon text_display 360 112 -160 {Tags:["millbygard_farm4_building"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"Millbygard 4:1 - gard klar","color":"gold","bold":true}'}
summon text_display 360 109 -139 {Tags:["millbygard_farm4_building"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"Huvudhus ca 15.6 x 8.3 m","color":"white"}'}
summon text_display 394 116 -180 {Tags:["millbygard_farm4_building"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"Lada/uthus ca 32.2 x 10.6 m","color":"white"}'}
summon text_display 321 105 -94 {Tags:["millbygard_farm4_building"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"Skjul ca 8.2 x 6.8 m","color":"white"}'}
summon text_display 431 85 -148 {Tags:["millbygard_farm4_building"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"Infart/vag - torr mark","color":"gray"}'}
summon text_display 318 88 -210 {Tags:["millbygard_farm4_building"],billboard:"center",brightness:{sky:15,block:15},see_through:1b,shadow:1b,background:1073741824,text:'{"text":"Sten/slant/skogskant","color":"gray"}'}

tellraw @a [{"text":"4:1-gardsmodell klar: huvudhus, lada/uthus, skjul, infart, stenpartier och skogskanter. Inget vatten.","color":"gold"}]
