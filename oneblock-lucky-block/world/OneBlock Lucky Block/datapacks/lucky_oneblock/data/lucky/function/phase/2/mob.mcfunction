scoreboard players add #mobs ob.stats 1
setblock 0 63 0 minecraft:stone
execute store result score #r2 ob.rng run random value 1..72
execute if score #r2 ob.rng matches 1..14 run summon minecraft:zombie 0.5 64 0.5
execute if score #r2 ob.rng matches 15..26 run summon minecraft:skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 27..34 run summon minecraft:spider 0.5 64 0.5
execute if score #r2 ob.rng matches 35..39 run summon minecraft:cave_spider 0.5 64 0.5
execute if score #r2 ob.rng matches 40..44 run summon minecraft:creeper 0.5 64 0.5
execute if score #r2 ob.rng matches 45..50 run summon minecraft:bat 0.5 64 0.5
execute if score #r2 ob.rng matches 51..54 run summon minecraft:silverfish 0.5 64 0.5
execute if score #r2 ob.rng matches 55..56 run summon minecraft:villager 0.5 64 0.5
execute if score #r2 ob.rng matches 57..60 run summon minecraft:sheep 0.5 64 0.5
execute if score #r2 ob.rng matches 61..64 run summon minecraft:cow 0.5 64 0.5
execute if score #r2 ob.rng matches 65..67 run summon minecraft:slime 0.5 64 0.5
execute if score #r2 ob.rng matches 68..69 run summon minecraft:glow_squid 0.5 64 0.5
execute if score #r2 ob.rng matches 70 run summon minecraft:iron_golem 0.5 64 0.5
execute if score #r2 ob.rng matches 71..72 run summon minecraft:witch 0.5 64 0.5
