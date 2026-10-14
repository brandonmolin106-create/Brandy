scoreboard players add #count ob.count 1
scoreboard players set #stuck ob.flag 0
execute as @e[type=item,x=0,y=62.5,z=0,dx=0,dy=1,dz=0] run function lucky:block/save_drop
execute as @e[type=experience_orb,x=0,y=62.5,z=0,dx=0,dy=1,dz=0] run tp @s 0.5 64.3 0.5
execute if score #lucky ob.flag matches 1 run function lucky:lucky/trigger
execute if score #lucky ob.flag matches 0 run function lucky:block/roll
function lucky:phase/check
