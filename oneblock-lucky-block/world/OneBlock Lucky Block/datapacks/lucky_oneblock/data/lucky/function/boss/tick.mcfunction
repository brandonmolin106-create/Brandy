execute if entity @a[scores={ob.dragonkill=1..}] run function lucky:boss/win
execute if score #boss ob.flag matches 1 if entity @e[type=minecraft:ender_dragon] run scoreboard players set #dragon_gone ob.flag 0
execute if score #boss ob.flag matches 1 store result score #ddt ob.flag run data get entity @e[type=minecraft:ender_dragon,limit=1] DragonDeathTime
execute if score #boss ob.flag matches 1 if score #ddt ob.flag matches 1.. run scoreboard players set #dragon_dying ob.flag 1
execute if score #boss ob.flag matches 1 unless entity @e[type=minecraft:ender_dragon] run scoreboard players add #dragon_gone ob.flag 1
execute if score #boss ob.flag matches 1 if score #dragon_dying ob.flag matches 1 if score #dragon_gone ob.flag matches 40.. run function lucky:boss/win
