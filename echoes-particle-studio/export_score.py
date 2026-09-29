"""Export the synthesized score on its own (no voice, no ducking) as a releasable track."""
import sys

import numpy as np
import soundfile as sf

from audio_post import master
from soundtrack import N, score
from sfx import SR

out = sys.argv[1]
mus = score(None)[:N]
fo = int(SR * 4.0)
mus[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
y, lufs = master(mus, target_lufs=-16.0, ceiling_db=-1.0)
sf.write(out, y, SR, subtype='PCM_24')
print(f'score: {out} {lufs:.2f} LUFS', flush=True)
