playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run give @p minecraft:jukebox 1
execute store result score #r2 ob.rng run random value 1..3
execute if score #r2 ob.rng matches 1 run execute positioned 0.5 64 0.5 run give @p minecraft:music_disc_pigstep 1
execute if score #r2 ob.rng matches 2 run execute positioned 0.5 64 0.5 run give @p minecraft:music_disc_otherside 1
execute if score #r2 ob.rng matches 3 run execute positioned 0.5 64 0.5 run give @p minecraft:music_disc_cat 1
playsound minecraft:music_disc.pigstep record @a 0 64 0 1 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "DJ TIME. Jukebox + a music disc. Drop the beat.", "color": "light_purple"}]
