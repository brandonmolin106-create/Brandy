playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

summon minecraft:iron_golem 0.5 64 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "An Iron Golem bodyguard. It falls off a lot, but it tries.", "color": "yellow"}]
