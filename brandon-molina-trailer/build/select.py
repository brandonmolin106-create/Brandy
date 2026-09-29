import json, numpy as np, os, subprocess
S=os.path.dirname(os.path.abspath(__file__)); A=json.load(open(f'{S}/analysis.json'))
# (video, window seconds, motion pref: +1 speaking/energetic, -1 still/pause)
plan=[('7690214681029512454',5.0,-1),('7666367364165864722',5.5,0),('7677257839844347143',4.0,-1),
('7651262992369077522',4.5,-1),('7673609701367778578',4.5,1),('7654673503492394247',3.5,-1),
('7678001520788426002',4.5,0),('7685934513406364936',3.0,1),('7659767007692295432',4.5,1),
('7654673503492394247',7.0,-1)]
used={'7651262992369077522':[29.0]}; res=[]
for k,(v,L,mp) in enumerate(plan):
    R=A[v]['rows']; n=int(L/0.5)+1; best=None
    for i in range(3,len(R)-n):
        w=R[i:i+n]
        miss=sum(1 for r in w if not r[3])
        if miss>n//4: continue
        w=[r for r in w if r[3]]
        if any(abs(w[0][0]-u)<15 for u in used.get(v,[])): continue
        area=np.mean([r[3][2]*r[3][3] for r in w])/(270*480)
        cx=np.std([r[3][0]+r[3][2]/2 for r in w])/270
        br=np.mean([r[1] for r in w]); mot=np.mean([r[2] for r in w[1:]])
        sc=-miss*0.3+area*4 - cx*8 + min(br,110)/200 + mp*min(mot,8)/12
        if best is None or sc>best[0]: best=(sc,w[0][0],w)
    sc,t0,w=best[0],best[1],best[2]; used.setdefault(v,[]).append(t0)
    f=np.array([r[3] for r in w]).mean(0)*(A[v]['W']/270)
    res.append(dict(v=v,t0=t0,L=L,face=[round(x) for x in f],W=A[v]['W'],H=A[v]['H']))
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t0+L/2),'-i',f'{S}/src/{v}.mp4','-frames:v','1','-vf','scale=240:-1',f'{S}/sheets/pick{k}.jpg'])
    print(k,v,t0,L,res[-1]['face'],round(sc,2))
json.dump(res,open(f'{S}/picks.json','w'))
