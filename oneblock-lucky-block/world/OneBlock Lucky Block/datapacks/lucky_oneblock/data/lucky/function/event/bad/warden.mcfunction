playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

execute if score #phase ob.phase matches 5.. run summon minecraft:warden 0.5 64 0.5
execute if score #phase ob.phase matches 5.. run title @a title {"text":"WARDEN","color":"dark_aqua","bold":true}
execute if score #phase ob.phase matches 5.. run tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "THE WARDEN. Do NOT fight it. Run. Build. Pray.", "color": "dark_aqua"}]
execute if score #phase ob.phase matches ..4 run function lucky:event/bad/horde
