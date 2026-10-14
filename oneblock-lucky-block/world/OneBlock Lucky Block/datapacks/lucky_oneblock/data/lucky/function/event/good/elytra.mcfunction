playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:elytra 1
execute positioned 0.5 64 0.5 run give @p minecraft:firework_rocket 32
title @a title {"text":"ELYTRA!","color":"aqua","bold":true}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "ELYTRA + 32 rockets?! Ultra rare. Don't fly into the void, you hear me?", "color": "aqua"}]
