execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..6 run function lucky:block/place_lucky
execute if score #r ob.rng matches 7..16 run function lucky:phase/1/chest
execute if score #r ob.rng matches 17..26 run function lucky:phase/1/mob
execute if score #r ob.rng matches 27..100 run function lucky:phase/1/blocks
