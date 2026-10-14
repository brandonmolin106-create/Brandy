scoreboard players set #boss ob.flag 1
scoreboard players set #dragon_gone ob.flag 0
scoreboard players set #dragon_dying ob.flag 0
scoreboard players set #thresh ob.count 99999
fill -6 62 -6 6 62 6 minecraft:obsidian
fill -5 62 -5 5 62 5 minecraft:end_stone
setblock 0 63 0 minecraft:chest{LootTable:"lucky:boss/kit"}
title @a times 10 90 20
title @a title {"text":"THE DRAGON","color":"dark_purple","bold":true}
title @a subtitle {"text":"FINAL BOSS. An arena rose from the void. SLAY IT.","color":"light_purple"}
playsound minecraft:entity.ender_dragon.growl master @a 0 64 0 3 0.7
playsound minecraft:entity.wither.spawn master @a 0 64 0 1 0.5
summon minecraft:ender_dragon 0.5 95 0.5
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "800 BLOCKS. ", "color": "dark_purple", "bold": true}, {"text": "The Ender Dragon is here. A 13x13 end stone arena rose under you and a boss kit chest is on the block. Shoot it when it perches, run when it breathes.", "color": "white"}]
