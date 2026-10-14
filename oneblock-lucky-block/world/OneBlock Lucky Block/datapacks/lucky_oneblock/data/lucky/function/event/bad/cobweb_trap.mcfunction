playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

fill 0 64 0 0 65 0 minecraft:cobweb
summon minecraft:cave_spider 0.5 64 0.5
summon minecraft:cave_spider 0.5 66 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Stuck in cobwebs with cave spiders. Yikes.", "color": "red"}]
