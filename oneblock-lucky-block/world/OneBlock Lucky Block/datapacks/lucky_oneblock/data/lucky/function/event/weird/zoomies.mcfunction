playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:speed 60 3
execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:jump_boost 60 2
execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:haste 60 2
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "ZOOMIES! Speed, jump boost and haste for a minute. On a one-block. Careful.", "color": "light_purple"}]
