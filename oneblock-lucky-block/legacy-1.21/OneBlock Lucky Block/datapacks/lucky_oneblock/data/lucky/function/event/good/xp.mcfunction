playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

execute positioned 0.5 64 0.5 run xp add @p 10 levels
particle minecraft:totem_of_undying 0.5 65 0.5 0.5 0.5 0.5 0.2 60 force
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "+10 XP levels! Go enchant something.", "color": "yellow"}]
