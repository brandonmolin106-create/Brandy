playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

execute if score #phase ob.phase matches 5.. run summon minecraft:evoker 0.5 64 0.5
execute if score #phase ob.phase matches 5.. run summon minecraft:vex 0.5 66 0.5
execute if score #phase ob.phase matches 5.. run summon minecraft:vex 0.5 66 0.5
execute if score #phase ob.phase matches ..4 run summon minecraft:pillager 0.5 64 0.5
execute if score #phase ob.phase matches ..4 run summon minecraft:pillager 0.5 65 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Illagers! They hate you specifically.", "color": "red"}]
