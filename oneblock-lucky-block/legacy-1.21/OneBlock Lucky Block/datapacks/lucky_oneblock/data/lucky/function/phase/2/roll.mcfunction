execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..8 run function lucky:block/place_lucky
execute if score #r ob.rng matches 9..18 run function lucky:phase/2/chest
execute if score #r ob.rng matches 19..30 run function lucky:phase/2/mob
execute if score #r ob.rng matches 31..100 run function lucky:phase/2/blocks
