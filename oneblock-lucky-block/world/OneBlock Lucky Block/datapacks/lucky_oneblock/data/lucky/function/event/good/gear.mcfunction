playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run loot give @p loot lucky:lucky/gear
particle minecraft:enchant 0.5 65 0.5 0.6 0.6 0.6 1 80 force
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Enchanted gear! Check your inventory.", "color": "yellow"}]
