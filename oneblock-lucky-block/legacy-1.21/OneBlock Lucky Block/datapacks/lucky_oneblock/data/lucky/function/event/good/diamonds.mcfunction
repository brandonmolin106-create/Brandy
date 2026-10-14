playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:diamond 5
particle minecraft:end_rod 0.5 65 0.5 0.4 0.6 0.4 0.05 60 force
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "DIAMONDS! 5 of them. Just like that.", "color": "yellow"}]
