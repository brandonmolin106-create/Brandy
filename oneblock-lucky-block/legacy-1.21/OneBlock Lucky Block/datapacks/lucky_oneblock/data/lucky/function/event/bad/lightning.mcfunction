playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

summon minecraft:lightning_bolt 0.5 64 0.5
summon minecraft:lightning_bolt 1.5 64 0.5
summon minecraft:lightning_bolt -0.5 64 1.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "ZAP. Thor says hi.", "color": "red"}]
