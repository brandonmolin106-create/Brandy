playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run loot give @p loot lucky:lucky/books
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Enchanted books. Nerd loot, but the good kind.", "color": "yellow"}]
