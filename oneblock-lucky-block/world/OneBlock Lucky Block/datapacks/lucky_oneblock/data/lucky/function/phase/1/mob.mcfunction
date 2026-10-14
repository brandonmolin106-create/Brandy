scoreboard players add #mobs ob.stats 1
setblock 0 63 0 minecraft:grass_block
execute store result score #r2 ob.rng run random value 1..64
execute if score #r2 ob.rng matches 1..10 run summon minecraft:chicken 0.5 64 0.5
execute if score #r2 ob.rng matches 11..20 run summon minecraft:cow 0.5 64 0.5
execute if score #r2 ob.rng matches 21..30 run summon minecraft:pig 0.5 64 0.5
execute if score #r2 ob.rng matches 31..40 run summon minecraft:sheep 0.5 64 0.5
execute if score #r2 ob.rng matches 41..46 run summon minecraft:rabbit 0.5 64 0.5
execute if score #r2 ob.rng matches 47..49 run summon minecraft:villager 0.5 64 0.5
execute if score #r2 ob.rng matches 50..51 run summon minecraft:wolf 0.5 64 0.5
execute if score #r2 ob.rng matches 52..53 run summon minecraft:cat 0.5 64 0.5
execute if score #r2 ob.rng matches 54..57 run summon minecraft:zombie 0.5 64 0.5
execute if score #r2 ob.rng matches 58..59 run summon minecraft:spider 0.5 64 0.5
execute if score #r2 ob.rng matches 60..62 run summon minecraft:bee 0.5 64 0.5
execute if score #r2 ob.rng matches 63..64 run summon minecraft:horse 0.5 64 0.5
