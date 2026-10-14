playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

summon minecraft:giant 0.5 64 2.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A GIANT ZOMBIE appeared. It just... stands there. Menacingly.", "color": "light_purple"}]
