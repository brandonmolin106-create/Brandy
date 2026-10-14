playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

summon minecraft:villager 0.5 64 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A villager! Keep it safe and it'll trade with you.", "color": "yellow"}]
