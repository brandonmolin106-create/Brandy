playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:levitation 6 1
execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:slow_falling 25 0
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Up, up and away! (Slow falling kicks in, you'll float back down... hopefully onto the block.)", "color": "red"}]
