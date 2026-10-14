execute store result score #r ob.rng run random value 1..100
execute if score #r ob.rng matches 1..10 run function lucky:block/place_lucky
execute if score #r ob.rng matches 11..20 run function lucky:phase/4/chest
execute if score #r ob.rng matches 21..33 run function lucky:phase/4/mob
execute if score #r ob.rng matches 34..100 run function lucky:phase/4/blocks
