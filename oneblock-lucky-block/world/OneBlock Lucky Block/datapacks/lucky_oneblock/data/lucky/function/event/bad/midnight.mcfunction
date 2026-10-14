playsound minecraft:entity.wither.spawn master @a 0 64 0 0.6 1.4

time set midnight
weather thunder 600
summon minecraft:phantom 0.5 72 0.5
summon minecraft:phantom 0.5 74 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Midnight. Thunder. Phantoms. Sleep tight.", "color": "red"}]
