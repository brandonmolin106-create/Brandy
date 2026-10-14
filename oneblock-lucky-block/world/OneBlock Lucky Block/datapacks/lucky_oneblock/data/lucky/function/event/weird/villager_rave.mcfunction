playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

summon minecraft:villager 0.5 64 0.5
summon minecraft:villager 0.5 65 0.5
summon minecraft:villager 0.5 66 0.5
summon minecraft:villager 0.5 67 0.5
summon minecraft:wandering_trader 0.5 68 0.5
playsound minecraft:music_disc.pigstep record @a 0 64 0 1 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "VILLAGER RAVE! Hmmm. Hmm hmm hmm.", "color": "light_purple"}]
