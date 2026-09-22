"""Re-create data/chunks.json and data/words_med.json from the narration.

Only needed if the narration WAVs change. Splits each part on silence
(-48 dB for 0.4 s+), keeps a little padding round every phrase, and labels
each phrase with the words faster-whisper (medium.en) heard in it. The line
grouping in edl.py refers to the chunk ids this produces, so re-check
edl.LINES / edl.DROP after re-running it.
"""
import json
import re
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel

import edl

ROOT = Path(__file__).resolve().parent
PRE, POST = 0.18, 0.35


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout)


def silences(path):
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(path), "-af", "silencedetect=noise=-48dB:d=0.4",
                        "-f", "null", "-"], capture_output=True, text=True)
    t = [float(x) for x in re.findall(r"silence_(?:start|end): ([0-9.]+)", r.stderr)]
    return list(zip(t[0::2], t[1::2]))


def main():
    model = WhisperModel("medium.en", device="cpu", compute_type="int8")
    words, chunks = {}, []
    for p in edl.NARRATION_PARTS:
        wav = ROOT / "work/narr" / f"part{p}.wav"
        segs, _ = model.transcribe(str(wav), word_timestamps=True, beam_size=5, condition_on_previous_text=False)
        words[p] = [[round(w.start, 3), round(w.end, 3), w.word.strip()] for s in segs for w in s.words]
        dur = duration(wav)
        regions, t = [], 0.0
        for a, b in silences(wav):
            if a - t > 0.05:
                regions.append([t, a])
            t = b
        if dur - t > 0.05:
            regions.append([t, dur])
        for k, (vs, ve) in enumerate(regions):
            lo = regions[k - 1][1] if k else 0.0
            hi = regions[k + 1][0] if k + 1 < len(regions) else dur
            ws = [w for w in words[p] if vs - 0.3 <= (w[0] + w[1]) / 2 <= ve + 0.3]
            chunks.append(dict(part=p, s=round(max(vs - PRE, (lo + vs) / 2, 0), 3),
                               e=round(min(ve + POST, (ve + hi) / 2, dur), 3), vs=round(vs, 3), ve=round(ve, 3),
                               text=" ".join(w[2] for w in ws)))
    for i, c in enumerate(chunks):
        c["id"] = i
    json.dump(chunks, open(ROOT / "data/chunks.json", "w"), indent=1)
    json.dump(words, open(ROOT / "data/words_med.json", "w"))
    print(len(chunks), "chunks")


if __name__ == "__main__":
    main()
