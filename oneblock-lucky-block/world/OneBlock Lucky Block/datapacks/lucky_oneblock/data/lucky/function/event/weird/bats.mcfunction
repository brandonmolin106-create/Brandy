playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1
summon minecraft:bat 0.5 65 0.5
summon minecraft:bat 0.5 66 0.5
summon minecraft:bat 0.5 67 0.5
summon minecraft:bat 0.5 65 0.5
summon minecraft:bat 0.5 66 0.5
summon minecraft:bat 0.5 67 0.5
summon minecraft:bat 0.5 65 0.5
summon minecraft:bat 0.5 66 0.5
summon minecraft:bat 0.5 67 0.5
summon minecraft:bat 0.5 65 0.5
execute positioned 0.5 64 0.5 run effect give @a[distance=..6] minecraft:darkness 4 0
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "BATS! So many bats.", "color": "light_purple"}]
