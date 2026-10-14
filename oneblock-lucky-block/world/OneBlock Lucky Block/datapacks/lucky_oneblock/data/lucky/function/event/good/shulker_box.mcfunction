playsound minecraft:entity.player.levelup master @a 0 64 0 1 1

setblock 0 63 0 minecraft:yellow_shulker_box{Items:[{Slot:0b,id:"minecraft:diamond",count:6},{Slot:1b,id:"minecraft:golden_apple",count:4},{Slot:2b,id:"minecraft:iron_ingot",count:16},{Slot:3b,id:"minecraft:oak_sapling",count:4},{Slot:4b,id:"minecraft:ender_pearl",count:4},{Slot:5b,id:"minecraft:experience_bottle",count:16},{Slot:6b,id:"minecraft:cooked_beef",count:12},{Slot:7b,id:"minecraft:emerald",count:8},{Slot:8b,id:"minecraft:torch",count:32}]}
tellraw @a ["", {"text": "[Lucky] ", "color": "gold", "bold": true}, {"text": "A LUCKY BOX (shulker box) full of goodies. Break it and it's yours, contents and all.", "color": "green"}]
