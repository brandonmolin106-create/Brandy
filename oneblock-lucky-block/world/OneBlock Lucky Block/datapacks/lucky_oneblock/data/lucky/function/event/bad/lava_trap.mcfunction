playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

setblock 0 64 0 minecraft:lava
schedule function lucky:event/bad/lava_clear 100t
title @a title {"text":"LAVA!","color":"red","bold":true}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "LAVA on top of the block! It clears in 5 seconds. Jump!", "color": "red"}]
