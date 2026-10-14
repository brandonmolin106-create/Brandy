setblock 0 63 0 minecraft:sponge
scoreboard players set #lucky ob.flag 1
particle minecraft:happy_villager 0.5 64.3 0.5 0.5 0.3 0.5 0.1 40 force
playsound minecraft:block.note_block.chime master @a 0 64 0 1 1.6
playsound minecraft:block.amethyst_block.chime master @a 0 64 0 1 0.8
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A LUCKY BLOCK appeared! Break it if you dare...", "color": "yellow", "bold": true}]
