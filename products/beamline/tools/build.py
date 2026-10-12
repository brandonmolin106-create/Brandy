#!/usr/bin/env python3
"""Build Beamline: build/free/index.html (public, levels 1-20) and product/index.html (full, 40 levels + Zen)."""
import os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=open(os.path.join(root,'src','index.html'),encoding='utf-8').read()
assert '__FULL__' in src
os.makedirs(os.path.join(root,'build','free'),exist_ok=True); os.makedirs(os.path.join(root,'product'),exist_ok=True)
open(os.path.join(root,'build','free','index.html'),'w',encoding='utf-8').write(src.replace('__FULL__','false'))
open(os.path.join(root,'product','index.html'),'w',encoding='utf-8').write(src.replace('__FULL__','true'))
for p in ('build/free/index.html','product/index.html'): print(p, os.path.getsize(os.path.join(root,p)),'bytes')
