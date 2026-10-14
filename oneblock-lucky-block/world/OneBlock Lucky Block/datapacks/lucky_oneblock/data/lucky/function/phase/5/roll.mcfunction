execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..11 run function lucky:block/place_lucky
execute if score #r ob.rng matches 12..21 run function lucky:phase/5/chest
execute if score #r ob.rng matches 22..35 run function lucky:phase/5/mob
execute if score #r ob.rng matches 36..100 run function lucky:phase/5/blocks
