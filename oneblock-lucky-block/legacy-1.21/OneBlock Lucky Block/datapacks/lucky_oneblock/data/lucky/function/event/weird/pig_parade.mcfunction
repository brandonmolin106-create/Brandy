playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1
summon minecraft:pig 0.5 64 0.5
summon minecraft:pig 0.5 65 0.5
summon minecraft:pig 0.5 66 0.5
summon minecraft:pig 0.5 67 0.5
summon minecraft:pig 0.5 68 0.5
summon minecraft:pig 0.5 69 0.5
execute positioned 0.5 64 0.5 run give @p minecraft:saddle 1
execute positioned 0.5 64 0.5 run give @p minecraft:carrot_on_a_stick 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Pig parade + a saddle + carrot on a stick. Ride a pig off the edge, I dare you.", "color": "light_purple"}]
