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
