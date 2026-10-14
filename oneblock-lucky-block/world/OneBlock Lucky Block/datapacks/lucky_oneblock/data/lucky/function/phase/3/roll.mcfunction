execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..9 run function lucky:block/place_lucky
execute if score #r ob.rng matches 10..19 run function lucky:phase/3/chest
execute if score #r ob.rng matches 20..31 run function lucky:phase/3/mob
execute if score #r ob.rng matches 32..100 run function lucky:phase/3/blocks
