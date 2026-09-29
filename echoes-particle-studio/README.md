# Echoes in the Dark: Particle Studio

A CPU pipeline that turns a talking-head speech video into a fully rendered 3D particle film:
the speaker becomes a particle avatar driven by their real facial performance, the story is
told through procedural 3D particle scenery, and the audio gets a full cinematic treatment.
Everything except the speaker's voice is generated here, so the output carries no licensed
music or stock footage.

First production: **"The Fish in the Cup"**, from @brandonmolina651's 6-minute TikTok speech.

## Pipeline

| Step | Script | What it does |
| --- | --- | --- |
| 1 | `yt-dlp` + `demucs` | Download the source, split voice from the background track (`htdemucs_ft`) |
| 2 | `transcribe.py` | Word-timed transcript (faster-whisper large-v3), then proofread by hand |
| 3 | `capture.py` | MediaPipe face landmarks + blendshapes + head pose for every frame |
| 4 | `build_bust.py` | 3D particle bust from one clean frame (landmarks + segmentation + Depth Anything V2) |
| 5 | `avatar.py` | Retargets the real performance onto the bust (face-mesh warp, head pose, mouth cavity, hair, aura) |
| 6 | `elements.py`, `elements2.py` | Procedural particle world: stars, nebulae, galaxies, fish, glass cup, ocean, people, sun, tree, planet, text |
| 7 | `timeline.py` | The edit: every shot, camera move and effect keyed to word timestamps |
| 8 | `render_core.py`, `director.py`, `render.py` | Numba splat renderer (blur-pyramid DOF, bloom, god rays, ACES, grade, grain) + subtitles |
| 9 | `soundtrack.py` (`sfx.py`, `audio_post.py`) | Vocal chain, emotion-automated reverb/echo, synthesized score + SFX, ducking, -14 LUFS master |
| 10 | `run_render.sh` | Parallel chunked render (no captions baked in) |
| 11 | `overlay.py`, `assemble.sh` | Hand-written captions aligned word-for-word to the transcript, brand mark, final encodes |

## Running it

```bash
WORK=/path/to/workdir            # holds the source video, stems, capture data
python capture.py source.mp4 $WORK/perf_capture.npz
python build_bust.py likeness.mp4 FRAME $WORK/bust.npz --density 1.0 --size 0.5
python transcribe.py vocals16k.wav $WORK/transcript.json   # then write the proofread words.json
# write productions/<name>/captions.txt: one caption per line, *keyword* in gold
python render.py $WORK preview 1.0,10.0,42.0 sheet.jpg     # look-dev contact sheet
./run_render.sh $WORK                                       # full render (chunks)
python soundtrack.py $WORK $WORK/audio/mix.wav
./assemble.sh $WORK out/
```

Needs: ffmpeg, Python 3.11 with numpy, numba, opencv, scipy, pedalboard, pyloudnorm, mediapipe,
torch/transformers (Depth Anything V2), faster-whisper, demucs. Runs on CPU only: about 0.4 s per 1080x1920 frame on 4 cores.
