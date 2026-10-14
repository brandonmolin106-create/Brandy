scoreboard objectives add ob.count dummy
scoreboard objectives add ob.phase dummy
scoreboard objectives add ob.rng dummy
scoreboard objectives add ob.flag dummy
scoreboard objectives add ob.stats dummy
scoreboard objectives add ob.help trigger
scoreboard objectives add ob.rescue trigger
scoreboard objectives add ob.reroll trigger
scoreboard objectives add ob.dragonkill minecraft.killed:minecraft.ender_dragon
execute unless score #count ob.count = #count ob.count run scoreboard players set #count ob.count 0
execute unless score #phase ob.phase = #phase ob.phase run scoreboard players set #phase ob.phase 1
execute unless score #thresh ob.count = #thresh ob.count run scoreboard players set #thresh ob.count 60
execute unless score #init ob.flag = #init ob.flag run scoreboard players set #init ob.flag 0
execute unless score #lucky ob.flag = #lucky ob.flag run scoreboard players set #lucky ob.flag 0
execute unless score #boss ob.flag = #boss ob.flag run scoreboard players set #boss ob.flag 0
execute unless score #rescue ob.flag = #rescue ob.flag run scoreboard players set #rescue ob.flag 1
execute unless score #luckycount ob.stats = #luckycount ob.stats run scoreboard players set #luckycount ob.stats 0
execute unless score #chests ob.stats = #chests ob.stats run scoreboard players set #chests ob.stats 0
execute unless score #mobs ob.stats = #mobs ob.stats run scoreboard players set #mobs ob.stats 0
scoreboard players set #tick ob.flag 0
scoreboard players set #stuck ob.flag 0
scoreboard players set #dragon_gone ob.flag 0
scoreboard players set #dragon_dying ob.flag 0
execute in minecraft:overworld run forceload add -16 -16 15 15
execute in minecraft:overworld run setworldspawn 0 64 0
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "One Block: Lucky Block Edition loaded. Type ", "color": "gray"}, {"text": "/trigger ob.help", "color": "yellow"}, {"text": " for the rules.", "color": "gray"}]
