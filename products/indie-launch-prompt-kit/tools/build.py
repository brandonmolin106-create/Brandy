#!/usr/bin/env python3
"""Build prompts.json from the module files, verify counts, and zip the deliverable."""
import json, os, re, sys, zipfile
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdir=os.path.join(root,'product','prompts'); out=[]
for fn in sorted(os.listdir(pdir)):
    if not fn.endswith('.md'): continue
    text=open(os.path.join(pdir,fn),encoding='utf-8').read()
    module=re.match(r'# (\d+) · (.+?) \((\d+) prompts\)',text)
    assert module, fn
    declared=int(module.group(3))
    items=re.findall(r'### (\d+\.\d+) (.+?)\n(?:\*\*Use when:\*\* .+?\n)?```\n(.*?)\n```',text,re.S)
    assert len(items)==declared, f"{fn}: declared {declared}, found {len(items)}"
    for num,title,body in items:
        assert '{{' in body or 'Act as' in body, f"{fn} {num} malformed"
        out.append({"id":num,"module":module.group(2),"title":title.strip(),"prompt":body.strip(),"variables":sorted(set(re.findall(r'\{\{([A-Z_]+)\}\}',body)))})
json.dump(out,open(os.path.join(root,'product','prompts.json'),'w',encoding='utf-8'),indent=1,ensure_ascii=False)
print("prompts:",len(out),"modules:",len({o['module'] for o in out}))
# zip
dist=os.path.join(root,'dist'); os.makedirs(dist,exist_ok=True)
zp=os.path.join(dist,'indie-launch-prompt-kit-v1.0.0.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for dp,_,fs in os.walk(os.path.join(root,'product')):
        for f in fs:
            full=os.path.join(dp,f); z.write(full,os.path.join('Indie-Launch-Prompt-Kit',os.path.relpath(full,os.path.join(root,'product'))))
print("zip:",os.path.getsize(zp),"bytes")
