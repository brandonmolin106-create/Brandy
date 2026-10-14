scoreboard players set #count ob.count 0
scoreboard players set #phase ob.phase 1
scoreboard players set #thresh ob.count 60
scoreboard players set #lucky ob.flag 0
scoreboard players set #boss ob.flag 0
scoreboard players set #luckycount ob.stats 0
scoreboard players set #chests ob.stats 0
scoreboard players set #mobs ob.stats 0
setblock 0 63 0 minecraft:grass_block
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Progress reset to block 0, Phase 1.", "color": "red"}]
