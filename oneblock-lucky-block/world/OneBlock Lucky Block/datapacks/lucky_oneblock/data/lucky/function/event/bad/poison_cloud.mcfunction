playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

summon minecraft:area_effect_cloud 0.5 64 0.5 {Radius:3.0f,Duration:160,potion_contents:{potion:"minecraft:poison"}}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Poison cloud! Hold your breath.", "color": "red"}]
