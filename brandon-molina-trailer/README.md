# Brandon Molina — "A place to pause" trailer

`trailer.mp4`: a 68-second vertical (1080×1920, 30 fps) cinematic thriller-style trailer for
[@brandonmolina651](https://www.tiktok.com/@brandonmolina651).

- **Visuals:** nine motivational-speech TikToks from @brandonmolina651, used as picture only.
  All original audio (speech, background sound, music) is discarded.
- **Narration:** newly generated calm male voice (Microsoft Edge neural TTS, "Andrew", slowed),
  with convolution reverb that opens up on "You can just be here", "Just take this moment",
  "Breathe" and "Stay". Each line is held at least 11 dB above the music by adaptive ducking.
- **Score:** synthesised in Python: heartbeat pulse, low strings in D minor, rises and impacts
  on the big cuts, bells and a high violin line as the light breaks through, then a hard cut to
  near-silence for the final look into camera and a soft D-major chord under the title.

## Structure

| Time | Beat | Source video | Line |
|---|---|---|---|
| 0–5s | Darkness, pulse, "2:47 AM · can't sleep", a glimpse of Brandon | — | — |
| 5.0 | 01/09 | 7690214681029512454 | If tonight feels heavier than you can explain… |
| 10.2 | 02/09 | 7666367364165864722 | if you're surrounded by people… but still feel alone… |
| 15.2 | 03/09 | 7677257839844347143 | you don't have to find the perfect words. |
| 18.8 | 04/09 | 7651262992369077522 | You can just be here. |
| 23.4 | Night sky through a rain-lit window, rise | — | — |
| 25.8 | 05/09 (impact) | 7673609701367778578 | Watch when you need something that helps you keep going. |
| 30.0 | 06/09, stars across the frame | 7654673503492394247 | Listen while you look at the sky. |
| 33.2 | 07/09, rain on glass | 7678001520788426002 | Put one of my videos on while you're trying to fall asleep. |
| 37.6 | 08/09 | 7685934513406364936 | You don't have to answer. |
| 40.4 | 09/09 (impact, light breaks) | 7659767007692295432 | You don't have to pretend you're happy. |
| 44.6 | Montage of all nine | all | Just take this moment. |
| 48.6 | Music cuts. Direct look into camera | 7654673503492394247 | Breathe. … Stay. |
| 56.0 | **BRANDON MOLINA** / *A place to pause. A voice to come back to.* | | |
| 61.0 | Night sky, **@brandonmolina651** | | |

## Rebuilding

`build/` holds the scripts. Source clips aren't committed. Download them with
`yt-dlp --impersonate chrome` into `build/src/`, generate narration into `build/vo/`
(see `build/timeline.py` for the lines), then run `analyze.py`, `select.py`, `audio.py` and
`video.py`. You also need `ffmpeg`, `opencv-python-headless<5`, `numpy`, `scipy` and `pillow`,
plus the Inter, JetBrains Mono and Cormorant Garamond fonts in `build/fonts/x/`.
