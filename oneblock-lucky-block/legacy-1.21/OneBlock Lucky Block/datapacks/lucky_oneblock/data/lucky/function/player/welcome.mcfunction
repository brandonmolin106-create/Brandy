tag @s add ob.joined
title @s times 10 70 20
title @s title {"text":"ONE BLOCK","color":"gold","bold":true}
title @s subtitle {"text":"LUCKY BLOCK EDITION","color":"yellow"}
playsound minecraft:entity.player.levelup master @s ~ ~ ~ 1 0.8
tellraw @s ""
tellraw @s ["",{"text":"=== ONE BLOCK: LUCKY BLOCK EDITION ===","color":"gold","bold":true}]
tellraw @s ["",{"text":"You have ONE block. Break it. It comes back as something new.","color":"white"}]
tellraw @s ["",{"text":"Yellow ","color":"white"},{"text":"LUCKY BLOCKS","color":"yellow","bold":true},{"text":" can be amazing... or a disaster. Break them anyway.","color":"white"}]
tellraw @s ["",{"text":"6 phases, a kit chest every phase, and at 800 blocks: ","color":"white"},{"text":"THE DRAGON.","color":"dark_purple","bold":true}]
tellraw @s ["",{"text":"Fall in the void? You get rescued (toggle with ","color":"gray"},{"text":"/trigger ob.rescue","color":"yellow"},{"text":"). Rules: ","color":"gray"},{"text":"/trigger ob.help","color":"yellow"}]
tellraw @s ""
