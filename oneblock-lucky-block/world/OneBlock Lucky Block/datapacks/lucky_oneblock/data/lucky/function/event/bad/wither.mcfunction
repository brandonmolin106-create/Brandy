playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

execute if score #phase ob.phase matches 6 run summon minecraft:wither 0.5 72 0.5
execute if score #phase ob.phase matches 6 run title @a title {"text":"THE WITHER","color":"dark_gray","bold":true}
execute if score #phase ob.phase matches 6 run tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "THE WITHER?! Ultra rare, ultra deadly. Kill it for a Nether Star!", "color": "dark_gray"}]
execute if score #phase ob.phase matches ..5 run function lucky:event/bad/creepers
