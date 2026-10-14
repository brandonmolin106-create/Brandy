playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

setblock 0 63 0 minecraft:chest{LootTable:"lucky:lucky/treasure"}
playsound minecraft:block.chest.open master @a 0 64 0 1 1
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "TREASURE CHEST! The block itself is the chest. Open it.", "color": "green"}]
