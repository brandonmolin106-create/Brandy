scoreboard players set @s ob.reroll 0
scoreboard players set #lucky ob.flag 0
scoreboard players set #stuck ob.flag 0
execute unless block 0 63 0 #minecraft:air run setblock 0 63 0 minecraft:dirt
tellraw @s ["",{"text":"[Lucky] ","color":"gold","bold":true},{"text":"Block replaced with dirt. No lucky stuff for that one, nice try.","color":"gray"}]
