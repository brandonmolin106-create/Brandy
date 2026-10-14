playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

summon minecraft:tnt 0.5 64 0.5 {fuse:70}
title @a title {"text":"TNT!","color":"red","bold":true}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "TNT! You have 3.5 seconds. Good luck, there is nowhere to run.", "color": "red"}]
