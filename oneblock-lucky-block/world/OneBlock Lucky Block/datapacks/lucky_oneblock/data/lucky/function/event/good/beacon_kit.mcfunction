playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:beacon 1
execute positioned 0.5 64 0.5 run give @p minecraft:iron_block 9
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A BEACON and 9 iron blocks. Build the pyramid when you have the room.", "color": "aqua"}]
