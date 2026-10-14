scoreboard players set #stuck ob.flag 0
scoreboard players set #lucky ob.flag 0
setblock 0 63 0 minecraft:dirt
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "That block sat there for 2 minutes, so it turned into dirt. Keep going!", "color": "gray"}]
