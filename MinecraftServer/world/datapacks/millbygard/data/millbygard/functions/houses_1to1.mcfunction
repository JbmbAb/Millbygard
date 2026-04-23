# Millbygard visible 1:1 house markers on top of the ortofoto surface.
# Built from the same approximate placements as the 4:1 draft, scaled back to 1 block = 1 m.
kill @e[type=text_display,tag=millbygard_houses_1to1]

# Clear only air above the 1:1 surface; keep ortofoto and property lines below.
fill -14 66 -128 34 84 -88 minecraft:air

# Main house, approx x -3..13, z -111..-103.
fill -3 65 -111 13 65 -103 minecraft:stone_bricks
fill -3 66 -111 13 70 -111 minecraft:red_terracotta
fill -3 66 -103 13 70 -103 minecraft:red_terracotta
fill -3 66 -111 -3 70 -103 minecraft:red_terracotta
fill 13 66 -111 13 70 -103 minecraft:red_terracotta
fill -2 71 -112 12 71 -102 minecraft:dark_oak_planks
fill -1 72 -111 11 72 -103 minecraft:dark_oak_planks
fill 0 73 -110 10 73 -104 minecraft:dark_oak_planks
fill 1 74 -109 9 74 -105 minecraft:dark_oak_planks
fill 2 75 -108 8 75 -106 minecraft:dark_oak_planks
fill 4 66 -103 7 69 -103 minecraft:dark_oak_planks
fill -1 68 -103 1 69 -103 minecraft:glass_pane
fill 10 68 -103 12 69 -103 minecraft:glass_pane
fill -3 68 -109 -3 69 -106 minecraft:glass_pane
fill 13 68 -109 13 69 -106 minecraft:glass_pane

# Long outbuilding/barn, approx x -3..30, z -124..-114.
fill -3 65 -124 30 65 -114 minecraft:stone_bricks
fill -3 66 -124 30 70 -124 minecraft:red_terracotta
fill -3 66 -114 30 70 -114 minecraft:red_terracotta
fill -3 66 -124 -3 70 -114 minecraft:red_terracotta
fill 30 66 -124 30 70 -114 minecraft:red_terracotta
fill -4 71 -125 31 71 -113 minecraft:dark_oak_planks
fill -3 72 -124 30 72 -114 minecraft:dark_oak_planks
fill -2 73 -123 29 73 -115 minecraft:dark_oak_planks
fill -1 74 -122 28 74 -116 minecraft:dark_oak_planks
fill 0 75 -121 27 75 -117 minecraft:dark_oak_planks
fill 1 76 -120 26 76 -118 minecraft:dark_oak_planks
fill 9 66 -114 17 69 -114 minecraft:dark_oak_planks
fill 10 67 -114 16 69 -114 minecraft:air
fill 2 68 -124 5 69 -124 minecraft:glass_pane
fill 22 68 -124 25 69 -124 minecraft:glass_pane

# Small shed, approx x -9..-1, z -99..-92.
fill -9 65 -99 -1 65 -92 minecraft:stone_bricks
fill -9 66 -99 -1 69 -99 minecraft:red_terracotta
fill -9 66 -92 -1 69 -92 minecraft:red_terracotta
fill -9 66 -99 -9 69 -92 minecraft:red_terracotta
fill -1 66 -99 -1 69 -92 minecraft:red_terracotta
fill -10 70 -100 0 70 -91 minecraft:deepslate_tiles
fill -9 71 -99 -1 71 -92 minecraft:deepslate_tiles
fill -8 72 -98 -2 72 -93 minecraft:deepslate_tiles
fill -7 73 -97 -3 73 -94 minecraft:deepslate_tiles
fill -6 74 -96 -4 74 -95 minecraft:deepslate_tiles
fill -6 66 -92 -4 68 -92 minecraft:dark_oak_planks

# High visibility references on the ground, no water.
fill -3 66 -101 13 66 -101 minecraft:yellow_concrete
fill -3 66 -126 30 66 -126 minecraft:yellow_concrete
fill -11 66 -99 -11 66 -92 minecraft:yellow_concrete
setblock 5 76 -107 minecraft:glowstone
setblock 14 72 -107 minecraft:torch
setblock 31 72 -119 minecraft:torch
setblock -10 70 -95 minecraft:torch

tellraw @a [{"text":"Synliga 1:1-hus byggda vid gardens lage: huvudhus, lada/uthus och skjul. Inget vatten lagt till.","color":"gold"}]
