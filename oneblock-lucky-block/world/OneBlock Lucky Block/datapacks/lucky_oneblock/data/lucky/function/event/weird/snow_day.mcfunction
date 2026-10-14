playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

weather clear
summon minecraft:snow_golem 0.5 64 0.5
summon minecraft:snow_golem 0.5 66 0.5
execute positioned 0.5 64 0.5 run give @p minecraft:snowball 32
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Snow day! Two snow golems and 32 snowballs. Snowball fight.", "color": "light_purple"}]
