scoreboard players set #phase ob.phase 2
scoreboard players set #thresh ob.count 150
title @a title {"text": "PHASE 2", "color": "gray", "bold": true}
title @a subtitle {"text": "THE CAVES", "color": "white"}
playsound minecraft:ui.toast.challenge_complete master @a 0 64 0 1 1
summon minecraft:firework_rocket 0.5 66 0.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "large_ball", "colors": [I;16766720, 16777215], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket 2.5 66 -1.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "star", "colors": [I;11141290, 16766720], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket -1.5 66 2.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "burst", "colors": [I;43775, 16777215], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
setblock 0 63 0 minecraft:chest{LootTable:"lucky:chest/kit_2"}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "Phase 2: THE CAVES! ", "color": "gray", "bold": true}, {"text": "A kit chest spawned on the block. New blocks, new mobs, more lucky blocks.", "color": "white"}]
