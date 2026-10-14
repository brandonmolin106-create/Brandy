playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

summon minecraft:wandering_trader 0.5 64 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A Wandering Trader dropped by. Got emeralds?", "color": "yellow"}]
