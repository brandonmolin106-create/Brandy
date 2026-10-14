playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:golden_apple 3
execute positioned 0.5 64 0.5 run give @p minecraft:enchanted_golden_apple 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Golden apples, plus one NOTCH apple. Save it for the dragon.", "color": "yellow"}]
