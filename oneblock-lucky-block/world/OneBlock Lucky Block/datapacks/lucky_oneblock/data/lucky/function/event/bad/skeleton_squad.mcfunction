playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

summon minecraft:skeleton 0.5 64 0.5
summon minecraft:skeleton 0.5 65 0.5
summon minecraft:skeleton 0.5 66 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Skeleton squad. Arrows incoming.", "color": "red"}]
