"""Word-level transcription with faster-whisper.

usage: python transcribe.py VOCALS.wav OUT.json [--model large-v3]
"""
import argparse
import json

from faster_whisper import WhisperModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('audio')
    ap.add_argument('out')
    ap.add_argument('--model', default='large-v3')
    a = ap.parse_args()
    model = WhisperModel(a.model, device='cpu', compute_type='int8', cpu_threads=4)
    segs, info = model.transcribe(a.audio, language='en', beam_size=5, word_timestamps=True,
                                  vad_filter=True, vad_parameters={'min_silence_duration_ms': 300},
                                  condition_on_previous_text=True, temperature=0.0)
    out = []
    for s in segs:
        out.append({'start': s.start, 'end': s.end, 'text': s.text.strip(),
                    'words': [{'w': w.word, 's': w.start, 'e': w.end, 'p': w.probability} for w in s.words]})
        print(f'[{s.start:7.2f} -> {s.end:7.2f}] {s.text.strip()}', flush=True)
    json.dump({'language': info.language, 'segments': out}, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
