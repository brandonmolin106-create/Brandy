playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

execute if score #phase ob.phase matches 4.. run summon minecraft:blaze 0.5 64 0.5
execute if score #phase ob.phase matches 4.. run summon minecraft:blaze 0.5 66 0.5
execute if score #phase ob.phase matches 4.. run summon minecraft:blaze 0.5 68 0.5
execute if score #phase ob.phase matches ..3 run summon minecraft:spider 0.5 64 0.5
execute if score #phase ob.phase matches ..3 run summon minecraft:spider 0.5 65 0.5
execute if score #phase ob.phase matches ..3 run summon minecraft:spider 0.5 66 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Fire and fangs! Hot stuff.", "color": "red"}]
