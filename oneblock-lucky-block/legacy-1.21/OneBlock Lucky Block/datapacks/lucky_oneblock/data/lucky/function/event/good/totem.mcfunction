playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:totem_of_undying 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A Totem of Undying. That's a free life, bro.", "color": "green"}]
