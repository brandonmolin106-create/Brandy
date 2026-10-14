scoreboard players set #boss ob.flag 2
scoreboard players reset @a ob.dragonkill
title @a times 10 120 30
title @a title {"text":"DRAGON SLAIN!","color":"gold","bold":true}
title @a subtitle {"text":"You beat One Block: Lucky Block Edition!","color":"yellow"}
playsound minecraft:ui.toast.challenge_complete master @a 0 64 0 1 1
playsound minecraft:entity.ender_dragon.death master @a 0 64 0 1 1
summon minecraft:firework_rocket 0.5 66 0.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "large_ball", "colors": [I;16766720, 16777215], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket 4.5 66 4.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "star", "colors": [I;11141290, 16766720], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket -3.5 66 4.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "burst", "colors": [I;43775, 16777215], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket 4.5 66 -3.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "large_ball", "colors": [I;16711680, 65280], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
summon minecraft:firework_rocket -3.5 66 -3.5 {LifeTime:25,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{"explosions": [{"shape": "star", "colors": [I;16711935, 16766720], "has_trail": true, "has_twinkle": true}], "flight_duration": 1}}}}
execute positioned 0.5 64 0.5 run give @a[distance=..64] minecraft:dragon_egg 1
execute positioned 0.5 64 0.5 run give @a[distance=..64] minecraft:dragon_head 1
execute positioned 0.5 64 0.5 run give @a[distance=..64] minecraft:elytra 1
execute positioned 0.5 64 0.5 run give @a[distance=..64] minecraft:firework_rocket 64
execute positioned 0.5 64 0.5 run xp add @a[distance=..64] 5000 points
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "YOU WIN! ", "color": "gold", "bold": true}, {"text": "Dragon egg, dragon head, elytra and 64 rockets for everyone. The block keeps going forever in Lucky Chaos, so keep building your sky island.", "color": "white"}]
