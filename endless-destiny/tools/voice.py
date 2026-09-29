"""Render the narration with an offline neural voice (Kokoro) and lay it out on the timeline.

Needs: pip install kokoro-onnx soundfile imageio-ffmpeg
       kokoro-v1.0.onnx + voices-v1.0.bin (github.com/thewh1teagle/kokoro-onnx releases) in $KOKORO_DIR
Writes narration/clips/NN.mp3 and narration/timing.json
"""
import json, os, pathlib, subprocess, tempfile
import numpy as np, soundfile as sf, imageio_ffmpeg
from kokoro_onnx import Kokoro

root = pathlib.Path(__file__).resolve().parent.parent
kdir = pathlib.Path(os.environ.get('KOKORO_DIR', '.'))
k = Kokoro(str(kdir / 'kokoro-v1.0.onnx'), str(kdir / 'voices-v1.0.bin'))
# narrator: natural phrasing of am_michael + the chest depth of am_onyx
VOICE = .55 * k.get_voice_style('am_michael') + .45 * k.get_voice_style('am_onyx')
FF = imageio_ffmpeg.get_ffmpeg_exe()
CHAIN = ('asetrate=24000*0.94,aresample=24000,atempo=1.0638,highpass=f=55,'
         'bass=g=4:f=110,equalizer=f=3200:t=q:w=1:g=2,'
         'acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-16:TP=-1.5:LRA=7')

script = json.loads((root / 'narration/script.json').read_text())
out = root / 'narration/clips'; out.mkdir(parents=True, exist_ok=True)
timing, n, problems = [], 0, []
for sec in script['sections']:
    t = sec['at']
    for line in sec['lines']:
        text, gap = line[0], line[1]
        opt = line[2] if len(line) > 2 else {}
        if 'at' in opt:
            if opt['at'] < t - .05: problems.append(f'{sec["name"]}: "{text}" wants {opt["at"]} but previous line runs to {t:.1f}')
            t = max(t, opt['at'])
        samples, sr = k.create(text, voice=VOICE, speed=.82, lang='en-us')
        # trim model padding
        idx = np.where(np.abs(samples) > .01)[0]
        samples = samples[max(0, idx[0] - 800): idx[-1] + 2400]
        with tempfile.NamedTemporaryFile(suffix='.wav') as w:
            sf.write(w.name, samples, sr)
            mp3 = out / f'{n:02d}.mp3'
            subprocess.run([FF, '-y', '-loglevel', 'error', '-i', w.name, '-af', CHAIN, '-ac', '1', '-ar', '24000', '-b:a', '64k', str(mp3)], check=True)
        dur = len(samples) / sr
        timing.append({'t': round(t, 2), 'd': round(dur, 2), 's': text.replace('...', '…'), 'f': mp3.name, 'soft': bool(opt.get('soft'))})
        t += dur + gap; n += 1
    if t - (timing[-1]['d'] and 0) > sec['end'] + .01:
        problems.append(f'{sec["name"]}: runs to {t:.1f}, past its end {sec["end"]}')
(root / 'narration/timing.json').write_text(json.dumps(timing, indent=1))
print(n, 'lines,', round(sum(x['d'] for x in timing)), 's of voice')
print('\n'.join(problems) or 'timing OK')
