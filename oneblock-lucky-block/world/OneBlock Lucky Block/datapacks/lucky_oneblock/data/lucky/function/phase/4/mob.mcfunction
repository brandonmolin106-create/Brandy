scoreboard players add #mobs ob.stats 1
setblock 0 63 0 minecraft:netherrack
execute store result score #r2 ob.rng run random value 1..92
execute if score #r2 ob.rng matches 1..20 run summon minecraft:zombified_piglin 0.5 64 0.5
execute if score #r2 ob.rng matches 21..32 run summon minecraft:piglin 0.5 64 0.5
execute if score #r2 ob.rng matches 33..38 run summon minecraft:hoglin 0.5 64 0.5
execute if score #r2 ob.rng matches 39..48 run summon minecraft:magma_cube 0.5 64 0.5
execute if score #r2 ob.rng matches 49..56 run summon minecraft:blaze 0.5 64 0.5
execute if score #r2 ob.rng matches 57..64 run summon minecraft:wither_skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 65..70 run summon minecraft:strider 0.5 64 0.5
execute if score #r2 ob.rng matches 71..73 run summon minecraft:ghast 0.5 64 0.5
execute if score #r2 ob.rng matches 74..79 run summon minecraft:skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 80..81 run summon minecraft:piglin_brute 0.5 64 0.5
execute if score #r2 ob.rng matches 82..86 run summon minecraft:zombie 0.5 64 0.5
execute if score #r2 ob.rng matches 87..89 run summon minecraft:creeper 0.5 64 0.5
execute if score #r2 ob.rng matches 90..92 run summon minecraft:chicken 0.5 64 0.5
