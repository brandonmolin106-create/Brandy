execute if block 0 63 0 minecraft:diamond_ore run setblock 0 63 0 minecraft:slime_block
summon minecraft:slime 0.5 64 0.5 {Size:1}
summon minecraft:slime 0.5 65 0.5 {Size:1}
summon minecraft:slime 0.5 66 0.5 {Size:1}
playsound minecraft:entity.slime.squish master @a 0 64 0 1 0.7
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Psych! It was slime the whole time.", "color": "red"}]
