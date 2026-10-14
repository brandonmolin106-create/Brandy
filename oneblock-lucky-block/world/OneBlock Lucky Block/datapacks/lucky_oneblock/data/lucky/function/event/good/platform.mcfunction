playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

fill -1 62 -1 1 62 1 minecraft:cobblestone keep
particle minecraft:cloud 0.5 63 0.5 1.5 0.3 1.5 0.02 80 force
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "LAND! A 3x3 cobblestone platform grew under your block.", "color": "green"}]
