playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

summon minecraft:witch 0.5 64 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A witch! Watch out for the potions.", "color": "red"}]
