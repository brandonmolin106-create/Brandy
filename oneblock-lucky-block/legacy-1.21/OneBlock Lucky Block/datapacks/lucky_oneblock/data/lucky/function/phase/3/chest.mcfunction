scoreboard players add #chests ob.stats 1
execute store result score #r2 ob.rng run random value 1..10
execute if score #r2 ob.rng matches 1..8 run setblock 0 63 0 minecraft:chest{LootTable:"lucky:chest/phase_3"}
execute if score #r2 ob.rng matches 9..10 run setblock 0 63 0 minecraft:barrel{LootTable:"lucky:chest/phase_3"}
playsound minecraft:block.chest.open master @a 0 64 0 0.6 1.2
