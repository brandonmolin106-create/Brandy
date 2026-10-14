playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

execute if score #phase ob.phase matches ..2 run function lucky:event/bad/horde_early
execute if score #phase ob.phase matches 3..4 run function lucky:event/bad/horde_mid
execute if score #phase ob.phase matches 5.. run function lucky:event/bad/horde_late
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A HORDE! Fight or get yeeted off the block.", "color": "red"}]
