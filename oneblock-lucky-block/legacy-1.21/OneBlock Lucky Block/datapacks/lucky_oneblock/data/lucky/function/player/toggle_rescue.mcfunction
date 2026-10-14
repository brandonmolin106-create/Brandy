scoreboard players set @s ob.rescue 0
execute if score #rescue ob.flag matches 1 run scoreboard players set #rescue ob.flag 2
execute if score #rescue ob.flag matches 0 run scoreboard players set #rescue ob.flag 1
execute if score #rescue ob.flag matches 2 run scoreboard players set #rescue ob.flag 0
execute if score #rescue ob.flag matches 1 run tellraw @s ["",{"text":"[Lucky] ","color":"gold","bold":true},{"text":"Void rescue: ON. Fall in and you get teleported back.","color":"green"}]
execute if score #rescue ob.flag matches 0 run tellraw @s ["",{"text":"[Lucky] ","color":"gold","bold":true},{"text":"Void rescue: OFF. Hardcore mode, huh? Respect.","color":"red"}]
