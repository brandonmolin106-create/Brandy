"""Inline the logo data and narration clips into the film page -> endless-destiny.html"""
import base64, json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / 'src/film.src.html').read_text()
logo = (root / 'assets/logo.json').read_text()
voice = json.loads((root / 'narration/timing.json').read_text())
for v in voice:
    v['a'] = base64.b64encode((root / 'narration/clips' / v.pop('f')).read_bytes()).decode()
out = src.replace('/*__LOGO__*/null', logo).replace('/*__VOICE__*/null', json.dumps(voice, separators=(',', ':')))
assert '/*__' not in out, 'placeholder not replaced'
(root / 'endless-destiny.html').write_text(out)
print('built', len(out) // 1024, 'KB')
