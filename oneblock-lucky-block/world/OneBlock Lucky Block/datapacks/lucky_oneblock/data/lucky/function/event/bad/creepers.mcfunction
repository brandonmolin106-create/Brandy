playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

summon minecraft:creeper 0.5 64 0.5
summon minecraft:creeper 0.5 65 0.5
execute if score #phase ob.phase matches 4.. run summon minecraft:creeper 0.5 66 0.5 {powered:1b}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Creepers. Aw man.", "color": "red"}]
