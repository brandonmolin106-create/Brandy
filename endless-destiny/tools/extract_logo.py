from PIL import Image, ImageFilter
import numpy as np, json, base64, io, collections
src='assets/logo-source.jpg'
im=Image.open(src).convert('RGB'); a=np.array(im).astype(float)
# symbol crop, square around center of symbol bbox (237..531, 162..501)
cx=(237+531)/2; cy=(162+501)/2; half=180
x0,y0=int(cx-half),int(cy-half); S=2*half
crop=a[y0:y0+S,x0:x0+S]
g=crop.mean(2)
r,gg,b=crop[...,0],crop[...,1],crop[...,2]
goldm=np.clip(((r-b)-25)/40,0,1)*np.clip((r-120)/60,0,1)
dark=np.clip((200-g)/150,0,1)*(1-goldm)
UP=4
def up(m):
    I=Image.fromarray((m*255).astype(np.uint8)).resize((S*UP,S*UP),Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    v=np.array(I)/255.0
    return np.clip((v-0.35)/0.3,0,1)  # sharpen edges
D=up(dark); G=up(goldm)
def png(alpha,col):
    h,w=alpha.shape; out=np.zeros((h,w,4),np.uint8); out[...,:3]=col; out[...,3]=(alpha*255).astype(np.uint8)
    bio=io.BytesIO(); Image.fromarray(out).save(bio,'PNG',optimize=True); return base64.b64encode(bio.getvalue()).decode()
lines_b64=png(D,(255,255,255)); star_b64=png(G,(232,196,120))
# sample points at original res with geodesic distance from the top tip
m=dark>0.5
ys,xs=np.where(m)
# top-most stroke pixel(s) near center = start of wave (the star sits between the tips)
starpos=np.argwhere(goldm>0.5).mean(0)
dist=np.full(m.shape,-1); q=collections.deque()
# seeds: stroke pixels nearest the star
d2=(ys-starpos[0])**2+(xs-starpos[1])**2
for i in np.argsort(d2)[:6]:
    dist[ys[i],xs[i]]=0; q.append((ys[i],xs[i]))
while q:
    y,x=q.popleft()
    for dy in(-1,0,1):
        for dx in(-1,0,1):
            ny,nx=y+dy,x+dx
            if 0<=ny<S and 0<=nx<S and m[ny,nx] and dist[ny,nx]<0:
                dist[ny,nx]=dist[y,x]+1; q.append((ny,nx))
def bfs():
    while q:
        y,x=q.popleft()
        for dy in(-1,0,1):
            for dx in(-1,0,1):
                ny,nx=y+dy,x+dx
                if 0<=ny<S and 0<=nx<S and m[ny,nx] and dist[ny,nx]<0:
                    dist[ny,nx]=dist[y,x]+1; q.append((ny,nx))
while True:
    un=m&(dist<0)
    if un.sum()==0: break
    uy,ux=np.where(un); dd=np.hypot(uy-starpos[0],ux-starpos[1]); k=dd.argmin()
    dist[uy[k],ux[k]]=int(dd[k]*1.15); q.append((uy[k],ux[k])); bfs()
print('all reached')
maxd=dist.max()
rng=np.random.default_rng(7)
idx=rng.choice(len(xs),size=min(4200,len(xs)),replace=False)
pts=[]
for i in idx:
    y,x=ys[i],xs[i]; dd=dist[y,x]
    if dd<0: dd=maxd
    pts.append([round(float(x+rng.random()-.5)/S*2-1,4),round(float(y+rng.random()-.5)/S*2-1,4),round(float(dd)/maxd,3)])
pts.sort(key=lambda p:p[2])
star=[round(float(starpos[1])/S*2-1,4),round(float(starpos[0])/S*2-1,4)]
# wordmark crop
wm=a[540:620,40:728]; wg=wm.mean(2); wd=np.clip((200-wg)/150,0,1)
ys2,xs2=np.where(wd>0.3); print('wm bbox',xs2.min(),xs2.max(),ys2.min(),ys2.max())
wd=wd[ys2.min()-4:ys2.max()+5, xs2.min()-4:xs2.max()+5]
W=Image.fromarray((wd*255).astype(np.uint8)); W=W.resize((W.width*3,W.height*3),Image.BICUBIC).filter(ImageFilter.GaussianBlur(.8))
wv=np.clip((np.array(W)/255-.3)/.35,0,1)
word_b64=png(wv,(255,255,255))
json.dump({'lines':lines_b64,'star':star_b64,'word':word_b64,'wordAspect':W.width/W.height,'pts':pts,'starPos':star},open('assets/logo.json','w'),separators=(',',':'))
print(len(pts),'pts star',star, 'sizes', len(lines_b64),len(star_b64),len(word_b64))
