playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

setblock 0 63 0 minecraft:diamond_ore
schedule function lucky:event/bad/fake_diamond_pop 40t
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Ooh, diamond ore! ...wait.", "color": "aqua"}]
