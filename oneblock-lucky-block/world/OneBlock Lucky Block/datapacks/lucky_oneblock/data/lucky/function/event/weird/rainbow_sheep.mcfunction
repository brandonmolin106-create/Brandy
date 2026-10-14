playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1
summon minecraft:sheep 0.5 64 0.5 {Color:14b}
summon minecraft:sheep 0.5 65 0.5 {Color:1b}
summon minecraft:sheep 0.5 66 0.5 {Color:4b}
summon minecraft:sheep 0.5 67 0.5 {Color:5b}
summon minecraft:sheep 0.5 68 0.5 {Color:11b}
summon minecraft:sheep 0.5 69 0.5 {Color:10b}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Rainbow sheep tower. Shear them!", "color": "light_purple"}]
