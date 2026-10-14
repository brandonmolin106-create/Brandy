scoreboard players add #mobs ob.stats 1
setblock 0 63 0 minecraft:gold_block
execute store result score #r2 ob.rng run random value 1..106
execute if score #r2 ob.rng matches 1..6 run summon minecraft:zombie 0.5 64 0.5
execute if score #r2 ob.rng matches 7..12 run summon minecraft:skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 13..17 run summon minecraft:creeper 0.5 64 0.5
execute if score #r2 ob.rng matches 18..22 run summon minecraft:enderman 0.5 64 0.5
execute if score #r2 ob.rng matches 23..26 run summon minecraft:blaze 0.5 64 0.5
execute if score #r2 ob.rng matches 27..30 run summon minecraft:wither_skeleton 0.5 64 0.5
execute if score #r2 ob.rng matches 31..33 run summon minecraft:witch 0.5 64 0.5
execute if score #r2 ob.rng matches 34..35 run summon minecraft:ravager 0.5 64 0.5
execute if score #r2 ob.rng matches 36..37 run summon minecraft:evoker 0.5 64 0.5
execute if score #r2 ob.rng matches 38..40 run summon minecraft:vindicator 0.5 64 0.5
execute if score #r2 ob.rng matches 41..43 run summon minecraft:breeze 0.5 64 0.5
execute if score #r2 ob.rng matches 44..46 run summon minecraft:bogged 0.5 64 0.5
execute if score #r2 ob.rng matches 47..49 run summon minecraft:iron_golem 0.5 64 0.5
execute if score #r2 ob.rng matches 50..51 run summon minecraft:snow_golem 0.5 64 0.5
execute if score #r2 ob.rng matches 52..54 run summon minecraft:wandering_trader 0.5 64 0.5
execute if score #r2 ob.rng matches 55..58 run summon minecraft:villager 0.5 64 0.5
execute if score #r2 ob.rng matches 59..60 run summon minecraft:zombie_villager 0.5 64 0.5
execute if score #r2 ob.rng matches 61..63 run summon minecraft:horse 0.5 64 0.5
execute if score #r2 ob.rng matches 64..65 run summon minecraft:camel 0.5 64 0.5
execute if score #r2 ob.rng matches 66..67 run summon minecraft:sniffer 0.5 64 0.5
execute if score #r2 ob.rng matches 68..69 run summon minecraft:armadillo 0.5 64 0.5
execute if score #r2 ob.rng matches 70..71 run summon minecraft:panda 0.5 64 0.5
execute if score #r2 ob.rng matches 72..73 run summon minecraft:polar_bear 0.5 64 0.5
execute if score #r2 ob.rng matches 74..76 run summon minecraft:allay 0.5 64 0.5
execute if score #r2 ob.rng matches 77..78 run summon minecraft:shulker 0.5 64 0.5
execute if score #r2 ob.rng matches 79..81 run summon minecraft:phantom 0.5 64 0.5
execute if score #r2 ob.rng matches 82..83 run summon minecraft:hoglin 0.5 64 0.5
execute if score #r2 ob.rng matches 84..85 run summon minecraft:piglin_brute 0.5 64 0.5
execute if score #r2 ob.rng matches 86 run summon minecraft:warden 0.5 64 0.5
execute if score #r2 ob.rng matches 87..90 run summon minecraft:cow 0.5 64 0.5
execute if score #r2 ob.rng matches 91..94 run summon minecraft:pig 0.5 64 0.5
execute if score #r2 ob.rng matches 95..98 run summon minecraft:sheep 0.5 64 0.5
execute if score #r2 ob.rng matches 99..102 run summon minecraft:chicken 0.5 64 0.5
execute if score #r2 ob.rng matches 103..105 run summon minecraft:bee 0.5 64 0.5
execute if score #r2 ob.rng matches 106 run summon minecraft:axolotl 0.5 64 0.5
