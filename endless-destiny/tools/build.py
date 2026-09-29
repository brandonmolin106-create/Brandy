"""Inline the extracted logo data into the film page -> endless-destiny.html"""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / 'src/film.src.html').read_text()
logo = (root / 'assets/logo.json').read_text()
out = src.replace('/*__LOGO__*/null', logo)
assert out != src, 'placeholder not found'
(root / 'endless-destiny.html').write_text(out)
print('built', len(out) // 1024, 'KB')
