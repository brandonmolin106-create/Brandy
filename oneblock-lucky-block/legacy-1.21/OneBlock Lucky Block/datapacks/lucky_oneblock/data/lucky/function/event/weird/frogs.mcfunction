playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

summon minecraft:frog 0.5 64 0.5 {variant:"minecraft:temperate"}
summon minecraft:frog 0.5 65 0.5 {variant:"minecraft:warm"}
summon minecraft:frog 0.5 66 0.5 {variant:"minecraft:cold"}
summon minecraft:frog 0.5 67 0.5 {variant:"minecraft:warm"}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Frogs! All three kinds. Ribbit.", "color": "light_purple"}]
