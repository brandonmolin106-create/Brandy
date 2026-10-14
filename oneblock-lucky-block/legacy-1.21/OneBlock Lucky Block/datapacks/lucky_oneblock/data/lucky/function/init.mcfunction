setblock 0 63 0 minecraft:grass_block
scoreboard players set #init ob.flag 1
scoreboard players set #stuck ob.flag 0
kill @e[type=item,distance=..8]
