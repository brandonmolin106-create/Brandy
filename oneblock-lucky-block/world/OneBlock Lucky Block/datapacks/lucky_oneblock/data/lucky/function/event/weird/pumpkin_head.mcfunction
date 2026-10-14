playsound minecraft:entity.villager.celebrate master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run item replace entity @p armor.head with minecraft:carved_pumpkin
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "You are now a pumpkin. Enjoy the view.", "color": "light_purple"}]
