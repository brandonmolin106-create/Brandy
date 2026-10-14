playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run loot give @p loot lucky:lucky/starter
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Starter pack: saplings, seeds, bone meal, food, a water bucket. Build a farm!", "color": "yellow"}]
