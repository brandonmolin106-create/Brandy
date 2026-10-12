#!/usr/bin/env python3
"""Build LoopDay from src/app.html.

  product/LoopDay.html        Pro edition, standalone (doctype + head), the paid download
  examples/LoopDay-free.html  Free edition, standalone, for local preview
  build/artifact-free.html    Free edition in artifact format (no doctype), for the public page
"""
import os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(root, 'src', 'app.html'), encoding='utf-8').read()

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="LoopDay: habits with streaks and routines with timers. Runs in your browser, data stays on your device.">
<meta name="theme-color" content="#2457e6">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%232457e6'/%3E%3Ccircle cx='16' cy='16' r='6' fill='white'/%3E%3C/svg%3E">
<style>[hidden]{display:none!important} img{max-width:100%}</style>
"""
TAIL = "\n</body>\n</html>\n"

def edition(pro: bool) -> str:
    out = src.replace('__PRO__', 'true' if pro else 'false')
    assert '__PRO__' not in out
    return out

def standalone(body: str) -> str:
    # title + fonts + style go in <head>; the rest in <body>
    m = re.search(r'^(.*?</style>)(.*)$', body, re.S)
    head_part, rest = m.group(1), m.group(2)
    return HEAD + head_part + "\n</head>\n<body>" + rest + TAIL

os.makedirs(os.path.join(root, 'product'), exist_ok=True)
os.makedirs(os.path.join(root, 'examples'), exist_ok=True)
os.makedirs(os.path.join(root, 'build'), exist_ok=True)
open(os.path.join(root, 'product', 'LoopDay.html'), 'w', encoding='utf-8').write(standalone(edition(True)))
open(os.path.join(root, 'examples', 'LoopDay-free.html'), 'w', encoding='utf-8').write(standalone(edition(False)))
open(os.path.join(root, 'build', 'artifact-free.html'), 'w', encoding='utf-8').write(edition(False))
for p in ('product/LoopDay.html', 'examples/LoopDay-free.html', 'build/artifact-free.html'):
    print(p, os.path.getsize(os.path.join(root, p)), 'bytes')
