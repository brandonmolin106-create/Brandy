playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:water_bucket 1
execute positioned 0.5 64 0.5 run give @p minecraft:lava_bucket 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Water bucket + lava bucket = infinite cobblestone. You know what to do.", "color": "yellow"}]
