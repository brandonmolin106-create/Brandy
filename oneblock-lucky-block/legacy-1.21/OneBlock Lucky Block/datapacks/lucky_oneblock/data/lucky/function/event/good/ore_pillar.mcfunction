playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

setblock 0 64 3 minecraft:iron_ore
setblock 0 65 3 minecraft:gold_ore
setblock 0 66 3 minecraft:lapis_ore
setblock 0 67 3 minecraft:redstone_ore
setblock 0 68 3 minecraft:diamond_ore
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "An ore pillar appeared 3 blocks away. Bridge to it carefully!", "color": "aqua"}]
