execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..13 run function lucky:block/place_lucky
execute if score #r ob.rng matches 14..23 run function lucky:phase/6/chest
execute if score #r ob.rng matches 24..37 run function lucky:phase/6/mob
execute if score #r ob.rng matches 38..100 run function lucky:phase/6/blocks
