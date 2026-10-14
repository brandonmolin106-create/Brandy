playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

setblock 0 74 0 minecraft:anvil
setblock 0 80 0 minecraft:anvil
setblock 0 86 0 minecraft:anvil
setblock 1 78 0 minecraft:chipped_anvil
setblock 0 82 1 minecraft:damaged_anvil
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "ANVILS FROM THE SKY! Move! (Hey, free anvil though.)", "color": "red"}]
