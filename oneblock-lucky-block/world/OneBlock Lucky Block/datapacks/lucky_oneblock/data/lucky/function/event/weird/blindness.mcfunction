playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:blindness 6 0
execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:darkness 6 0
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Lights out! Don't move...", "color": "light_purple"}]
