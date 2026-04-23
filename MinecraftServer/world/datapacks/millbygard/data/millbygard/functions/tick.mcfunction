scoreboard players add @a millbygard_cd 0
scoreboard players add @a millbygard_latch 0
scoreboard players remove @a[scores={millbygard_cd=1..}] millbygard_cd 1
tag @a remove millbygard_onpad
tag @a[x=16,y=121,z=-179,dx=0,dy=2,dz=0] add millbygard_onpad
tag @a[x=20,y=121,z=-179,dx=0,dy=2,dz=0] add millbygard_onpad
tag @a[x=24,y=121,z=-179,dx=0,dy=2,dz=0] add millbygard_onpad
tag @a[x=16,y=121,z=-173,dx=0,dy=2,dz=0] add millbygard_onpad
tag @a[x=24,y=121,z=-173,dx=0,dy=2,dz=0] add millbygard_onpad
scoreboard players set @a[tag=!millbygard_onpad] millbygard_latch 0
execute as @a[x=16,y=121,z=-179,dx=0,dy=2,dz=0,scores={millbygard_cd=0,millbygard_latch=0}] at @s run function millbygard:button_ortofoto
execute as @a[x=20,y=121,z=-179,dx=0,dy=2,dz=0,scores={millbygard_cd=0,millbygard_latch=0}] at @s run function millbygard:button_500m
execute as @a[x=24,y=121,z=-179,dx=0,dy=2,dz=0,scores={millbygard_cd=0,millbygard_latch=0}] at @s run function millbygard:button_signs
execute as @a[x=16,y=121,z=-173,dx=0,dy=2,dz=0,scores={millbygard_cd=0,millbygard_latch=0}] at @s run function millbygard:button_start
execute as @a[x=24,y=121,z=-173,dx=0,dy=2,dz=0,scores={millbygard_cd=0,millbygard_latch=0}] at @s run function millbygard:button_topo
