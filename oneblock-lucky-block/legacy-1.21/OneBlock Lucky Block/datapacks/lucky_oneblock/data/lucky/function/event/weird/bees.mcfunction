playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

summon minecraft:bee 0.5 65 0.5
summon minecraft:bee 0.5 66 0.5
summon minecraft:bee 0.5 66 0.5
summon minecraft:bee 0.5 67 0.5
execute positioned 0.5 64 0.5 run give @p minecraft:honey_bottle 2
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Bees! Don't hit them. Seriously, don't.", "color": "light_purple"}]
