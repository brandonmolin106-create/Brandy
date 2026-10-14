execute unless score #init ob.flag matches 1 if loaded 0 63 0 run function lucky:init
execute if score #init ob.flag matches 1 if block 0 63 0 #minecraft:air run function lucky:block/broken
execute if score #init ob.flag matches 1 run function lucky:block/stuck_timer
execute as @a[tag=!ob.joined] run function lucky:player/welcome
execute if score #rescue ob.flag matches 1 as @a[gamemode=!spectator,gamemode=!creative] at @s if dimension minecraft:overworld if entity @s[y=-300,dy=330] run function lucky:player/rescue
execute as @a[scores={ob.help=1..}] run function lucky:player/help
execute as @a[scores={ob.rescue=1..}] run function lucky:player/toggle_rescue
execute as @a[scores={ob.reroll=1..}] run function lucky:player/reroll
scoreboard players enable @a ob.help
scoreboard players enable @a ob.rescue
scoreboard players enable @a ob.reroll
execute as @e[type=item,distance=..64] if items entity @s contents minecraft:sponge run kill @s
scoreboard players add #tick ob.flag 1
execute if score #tick ob.flag matches 20.. run function lucky:hud/show
execute if score #boss ob.flag matches 1 run function lucky:boss/tick
