scoreboard players set #phase ob.phase 3
scoreboard players set #thresh ob.count 260
title @a title {"text": "PHASE 3", "color": "dark_green", "bold": true}
title @a subtitle {"text": "THE WILD", "color": "white"}
playsound minecraft:ui.toast.challenge_complete master @a 0 64 0 1 1
summon minecraft:firework_rocket 0.5 66 0.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "large_ball", "colors": [I;16766720, 16777215], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket 2.5 66 -1.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "star", "colors": [I;11141290, 16766720], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket -1.5 66 2.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "burst", "colors": [I;43775, 16777215], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
setblock 0 63 0 minecraft:chest{LootTable:"lucky:chest/kit_3"}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Phase 3: THE WILD! ", "color": "dark_green", "bold": true}, {"text": "A kit chest spawned on the block. New blocks, new mobs, more lucky blocks.", "color": "white"}]
