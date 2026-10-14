execute if score #phase ob.phase matches 1 if score #count ob.count matches 60.. run function lucky:phase/2/enter
execute if score #phase ob.phase matches 2 if score #count ob.count matches 150.. run function lucky:phase/3/enter
execute if score #phase ob.phase matches 3 if score #count ob.count matches 260.. run function lucky:phase/4/enter
execute if score #phase ob.phase matches 4 if score #count ob.count matches 400.. run function lucky:phase/5/enter
execute if score #phase ob.phase matches 5 if score #count ob.count matches 560.. run function lucky:phase/6/enter
execute if score #phase ob.phase matches 6 if score #boss ob.flag matches 0 if score #count ob.count matches 800.. run function lucky:boss/start
