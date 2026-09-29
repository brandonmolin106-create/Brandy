# Echoes in the Dark — Logo Formation Trailer (6:00, 4K UHD)

A six-minute cinematic trailer where the Echoes in the Dark emblem forms from a single
spark, grows vein by vein across a giant close-up, and slams into its full,
realistically detailed form. It then resolves into the logo lockup, flips to the
official light version, and collapses back into the dark.

Everything is procedural. The emblem is traced from `assets/logo-source.jpg` into
distance fields, so it stays razor sharp in 3840×2160, even with the camera 5× inside it.

## Story beats

| Time | Beat |
|------|------|
| 0:00 | The void: dust, fog, a drone. *"Before the light… there was only the dark."* |
| 0:20 | The gold star ignites. Heartbeat echo rings reveal a ghost of the giant emblem (sonar). |
| 1:00 | Dust is pulled into the star, the ticking clock builds. *"They said nothing could grow here… They were wrong."* |
| 1:35 | **BOOM.** The camera rushes in to the top of the emblem. |
| 1:36–4:35 | **The giant formation.** Molten-gold growth fronts crawl along every stroke (thin filament, then full width), throwing sparks, while the camera chases the front across the emblem and slowly pulls back. |
| 4:35 | Held breath: total silence. |
| 4:36 | **The full formation hits.** Shockwave, flash, shake. The glowing lines solidify into engraved platinum with gold inlay. Light sweeps, perspective orbit. *"This is where legends are born."* |
| 4:58 | Logo lockup. The letterbox opens and letters echo in one by one. *"Echoes… in the Dark."* |
| 5:30 | Light floods out of the star: the official black-on-paper logo. *"Our story begins now."* |
| 5:46 | Collapse back into the star. *"Listen closely. The dark is calling."* Last echo, star out. |

## Build

```bash
pip install numpy scipy opencv-python-headless numexpr pillow scikit-image soundfile imageio-ffmpeg fonttools brotli
python3 build_assets.py            # trace the logo -> assets/cache/*.npy
python3 audio.py                   # score + narration mix -> out/soundtrack_raw.wav
./make_video.sh                    # 4K frames in parallel segments -> out/video_4k_silent.mp4
./finalize.sh                      # loudness-normalise + mux -> out/Echoes_in_the_Dark_Trailer_4K.mp4
```

Preview stills: `python3 render.py --scale 0.25 --stills 30,150,276.3,310,335`

## Files

- `timeline.py`: every beat (picture and sound read the same timings)
- `build_assets.py`: emblem → signed distance field, growth distance, stroke-core field, micro-detail texture
- `render.py`: frame renderer (growth shader, engraved-metal shader, star, rings, dust/bokeh, bloom, god rays, grain)
- `audio.py`: synthesised thriller score (drones, heartbeat, ticking ostinato, taiko, braams, choir, risers) plus narration EQ/echo/adaptive ducking
- `assets/voice/`: narration lines (deep male preset voice, generated with Higgsfield Seed Audio)
- `assets/Jost-*.ttf`: wordmark font (SIL OFL, see `assets/LICENSE-Jost.txt`)

## v2: worlds, shock and brutal thriller score (6:00)

`render2.py` + `timeline2.py` + `scenery.py` + `audio2.py`, a faster and harsher cut:

- **79 shots, always centred on the logo:** push-ins straight down its axis, never off to the side.
- **Photographic worlds** (`build_plates.py`): NASA/ESA Webb "Cosmic Cliffs" deep space, a dusk ocean,
  mountains under the Milky Way (also the storm), and a night forest. They are graded to night and the logo is
  composited *into* them: real peaks and tree trunks pass in front of it (hand-traced ridge, snapped to the
  photo), its light spills onto snow and bark, and its reflection ripples across the real water.
- **Effects:** lightning (branching bolts that strike the logo), electric arcs, rain, storm clouds, fireflies,
  embers, metal shards, lens-flare ghosts, light leaks, god rays, shockwave distortion with prismatic fringe,
  impact frames (white-hot flash, negative frame), zoom-blur punches, radial light-streak bursts,
  RGB glitch-slicing on stutter cuts, chromatic aberration, camera shake, and film halation with an ACES grade.
- **Kinetic title cards** in chrome-gold: EVERY SOUND / HAS AN ECHO / THEY WERE WRONG / FASTER / LOUDER / STRONGER,
  with the last three slammed on the narrator's words.
- **24 narration lines**, plus a synthesised thriller score: layered impact stacks (crack, metal clang, 808 boom,
  sub drop, taiko, gated snare, crash), opening-filter braams, Shepard-tone risers, tremolo and screeching strings,
  a 120 bpm pulse, thunder, weather beds per world, and true dead air before every mega-hit.

```bash
./fetch_plates.sh && python3 build_plates.py   # photographic plates -> assets/cache/plates
python3 audio2.py                              # score + narration -> out2/soundtrack_raw.wav
./make_video2.sh                               # 4K picture -> out2/video_4k_silent.mp4
./finalize2.sh                                 # 4K master, 1080p copy, <30 MB HEVC share copy
```

### Credits
- "Cosmic Cliffs" in the Carina Nebula: NASA, ESA, CSA, STScI (ESA/Webb, CC BY 4.0)
- Ocean at dusk: Anthony Cantin on Unsplash
- Mountains under the Milky Way: Gantavya Bhatt on Unsplash
- Night forest: Wolfgang Hasselmann on Unsplash
- Wordmark and title font: Jost (SIL Open Font License)
- Narration voice: Higgsfield Seed Audio preset voice
