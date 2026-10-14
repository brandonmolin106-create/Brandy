playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

summon minecraft:wolf 0.5 64 0.5
summon minecraft:cat 0.5 64 0.5
summon minecraft:parrot 0.5 65 0.5
execute positioned 0.5 64 0.5 run give @p minecraft:bone 4
execute positioned 0.5 64 0.5 run give @p minecraft:cod 4
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Pet party! A wolf, a cat and a parrot. Bones and fish included.", "color": "yellow"}]
