import cv2, numpy as np, glob, os, json, sys
S=os.path.dirname(os.path.abspath(__file__))
casc=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
ids=['7651262992369077522','7654673503492394247','7659767007692295432','7666367364165864722','7673609701367778578','7677257839844347143','7678001520788426002','7685934513406364936','7690214681029512454']
out={}
for vid in ids:
    cap=cv2.VideoCapture(f'{S}/src/{vid}.mp4'); fps=cap.get(5); n=int(cap.get(7)); W=cap.get(3); H=cap.get(4)
    rows=[]; prev=None; t=0.0
    while t< n/fps-1:
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,f=cap.read()
        if not ok: break
        g=cv2.cvtColor(cv2.resize(f,(270,480)),cv2.COLOR_BGR2GRAY)
        eq=cv2.equalizeHist(g)
        fs=casc.detectMultiScale(eq,1.15,5,minSize=(50,50))
        face=max(fs,key=lambda r:r[2]*r[3]).tolist() if len(fs) else None
        mot=float(np.mean(np.abs(g.astype(int)-prev))) if prev is not None else 0
        rows.append([round(t,1),round(float(g.mean()),1),round(mot,2),face]); prev=g.astype(int); t+=0.5
    out[vid]={'dur':n/fps,'W':W,'H':H,'rows':rows}
    fr=[r for r in rows if r[3]]
    print(vid, round(n/fps,1), 'faces', len(fr),'/',len(rows), 'bright', round(np.mean([r[1] for r in rows]),1))
json.dump(out,open(f'{S}/analysis.json','w'))
