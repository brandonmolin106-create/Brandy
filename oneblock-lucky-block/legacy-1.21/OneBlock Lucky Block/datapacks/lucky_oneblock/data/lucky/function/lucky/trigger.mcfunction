scoreboard players set #lucky ob.flag 0
scoreboard players add #luckycount ob.stats 1
function lucky:block/plain
particle minecraft:totem_of_undying 0.5 64.5 0.5 0.6 0.6 0.6 0.25 80 force
playsound minecraft:entity.firework_rocket.twinkle master @a 0 64 0 1 1
execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..50 run function lucky:lucky/good
execute if score #r ob.rng matches 51..80 run function lucky:lucky/bad
execute if score #r ob.rng matches 81..100 run function lucky:lucky/weird
