scoreboard players add #mobs ob.stats 1
setblock 0 63 0 minecraft:moss_block
execute store result score #r2 ob.rng run random value 1..93
execute if score #r2 ob.rng matches 1..5 run summon minecraft:panda 0.5 64 0.5
execute if score #r2 ob.rng matches 6..10 run summon minecraft:parrot 0.5 64 0.5
execute if score #r2 ob.rng matches 11..14 run summon minecraft:ocelot 0.5 64 0.5
execute if score #r2 ob.rng matches 15..18 run summon minecraft:polar_bear 0.5 64 0.5
execute if score #r2 ob.rng matches 19..23 run summon minecraft:fox 0.5 64 0.5
execute if score #r2 ob.rng matches 24..28 run summon minecraft:wolf 0.5 64 0.5
execute if score #r2 ob.rng matches 29..32 run summon minecraft:goat 0.5 64 0.5
execute if score #r2 ob.rng matches 33..35 run summon minecraft:llama 0.5 64 0.5
execute if score #r2 ob.rng matches 36..38 run summon minecraft:mooshroom 0.5 64 0.5
execute if score #r2 ob.rng matches 39..41 run summon minecraft:turtle 0.5 64 0.5
execute if score #r2 ob.rng matches 42..45 run summon minecraft:frog 0.5 64 0.5
execute if score #r2 ob.rng matches 46 run summon minecraft:sniffer 0.5 64 0.5
execute if score #r2 ob.rng matches 47..48 run summon minecraft:camel 0.5 64 0.5
execute if score #r2 ob.rng matches 49..54 run summon minecraft:drowned 0.5 64 0.5
execute if score #r2 ob.rng matches 55..58 run summon minecraft:witch 0.5 64 0.5
execute if score #r2 ob.rng matches 59..63 run summon minecraft:husk 0.5 64 0.5
execute if score #r2 ob.rng matches 64..68 run summon minecraft:stray 0.5 64 0.5
execute if score #r2 ob.rng matches 69..73 run summon minecraft:zombie 0.5 64 0.5
execute if score #r2 ob.rng matches 74..78 run summon minecraft:skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 79..82 run summon minecraft:creeper 0.5 64 0.5
execute if score #r2 ob.rng matches 83..86 run summon minecraft:spider 0.5 64 0.5
execute if score #r2 ob.rng matches 87..89 run summon minecraft:pillager 0.5 64 0.5
execute if score #r2 ob.rng matches 90..91 run summon minecraft:armadillo 0.5 64 0.5
execute if score #r2 ob.rng matches 92..93 run summon minecraft:villager 0.5 64 0.5
