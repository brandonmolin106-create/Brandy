scoreboard players add #mobs ob.stats 1
setblock 0 63 0 minecraft:end_stone
execute store result score #r2 ob.rng run random value 1..81
execute if score #r2 ob.rng matches 1..20 run summon minecraft:enderman 0.5 64 0.5
execute if score #r2 ob.rng matches 21..28 run summon minecraft:endermite 0.5 64 0.5
execute if score #r2 ob.rng matches 29..32 run summon minecraft:shulker 0.5 64 0.5
execute if score #r2 ob.rng matches 33..38 run summon minecraft:phantom 0.5 64 0.5
execute if score #r2 ob.rng matches 39..43 run summon minecraft:zombie 0.5 64 0.5
execute if score #r2 ob.rng matches 44..48 run summon minecraft:skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 49..52 run summon minecraft:creeper 0.5 64 0.5
execute if score #r2 ob.rng matches 53..56 run summon minecraft:spider 0.5 64 0.5
execute if score #r2 ob.rng matches 57..59 run summon minecraft:witch 0.5 64 0.5
execute if score #r2 ob.rng matches 60 run summon minecraft:warden 0.5 64 0.5
execute if score #r2 ob.rng matches 61..63 run summon minecraft:allay 0.5 64 0.5
execute if score #r2 ob.rng matches 64..65 run summon minecraft:ravager 0.5 64 0.5
execute if score #r2 ob.rng matches 66..69 run summon minecraft:pillager 0.5 64 0.5
execute if score #r2 ob.rng matches 70..72 run summon minecraft:vindicator 0.5 64 0.5
execute if score #r2 ob.rng matches 73 run summon minecraft:evoker 0.5 64 0.5
execute if score #r2 ob.rng matches 74..76 run summon minecraft:breeze 0.5 64 0.5
execute if score #r2 ob.rng matches 77..79 run summon minecraft:bogged 0.5 64 0.5
execute if score #r2 ob.rng matches 80..81 run summon minecraft:villager 0.5 64 0.5
