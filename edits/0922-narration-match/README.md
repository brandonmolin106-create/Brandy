# 0922 narration-match: Endless Destiny announcement

A full edit of the *Endless Destiny* announcement: the narrator (the Evie
voice, 7 parts) is re-timed and given emotion-matched effects, and 100 shots
from the 26 Higgsfield trailer clips are cut to her lines with transitions, a
cinematic finish, an original score and sound design.

CapCut has no API, so nobody can edit inside the CapCut app remotely. This
folder builds the finished pieces as files that drop straight into the
CapCut project.

## What you get (in `out/`, not committed)

| File | What it is | Where it goes in CapCut |
|---|---|---|
| `endless_destiny_narration_match.mp4` | The finished edit: picture + mixed audio, 1920x1080, 24 fps, 7:16 | Main video track |
| `narration_fx.wav` / `.m4a` | Narrator only, with all voice effects baked in (`.m4a` = small copy for phones) | Audio track 1 (if you want to rebalance) |
| `score_sfx.wav` / `.m4a` | Music + sound design only | Audio track 2 |
| `full_mix.wav` | Both together, mastered (-14 LUFS, true peak under -1 dB) | Already inside the MP4 |
| `captions.srt` | Captions timed to the new edit | Captions → import local captions (`.srt`) |
| `timeline.json` | Where every line and cue landed | Used by the scripts |

### Putting it into the CapCut project

1. Open **0922 narration-match** in CapCut and set the project to 24 fps.
2. Mute or delete the old narration track, otherwise she'll talk over herself.
3. Import `endless_destiny_narration_match.mp4` and drop it at 00:00 on the main track.
4. To rebalance voice against music: detach/mute the MP4's audio, then put
   `narration_fx.wav` and `score_sfx.wav` on two audio tracks, both at 00:00.
   Played together at 100% they equal the master mix.
5. Captions: import `captions.srt`, or use CapCut's auto-captions (not both).

[`CUESHEET.md`](CUESHEET.md) lists every line with its timecode, voice
effect, shot, transition and sound cue.

## What the edit does

**Voice**
- Pacing: the raw narration was 9:08 and **54% silence** (294 s). Pauses
  inside a line are kept up to 0.8 s and longer ones are squeezed. The pause
  after each line is set by hand: about 0.85 s in the fast montages, 2–3.6 s
  on the big beats. The result is 7:16.
- Every voice line gets the same base polish: 80 Hz high-pass, warmth and
  presence EQ, a mud cut at 380 Hz, 3:1 compression.
- Every line also gets an effect chosen for what it says (`VOICE_FX` in `edl.py`):
  - **Echo:** a ping-pong echo on the last word of "Echoes in the Dark",
    "…feel *endless*?", "But where?", "another… another".
  - **Reverse-reverb swell:** rises into both "Endless Destiny" title lines
    and "travelling beside us the entire time".
  - **Memory voice** (filtered, with chorus): on the imagined quotes "This is
    it…" and "Go this way. Do this…", and on "who we used to be".
  - **Shadow voice** (pitched down, dark cathedral): on "endless can sound
    scary / distance / waiting / questions".
  - **Chorus of voices:** on "we're all doing the same thing. Walking.
    Wondering. Falling. Growing."
  - **Close and dry:** on the direct questions to the listener ("Think about
    yours", "are you actually lost?").
- Reverb comes from shared room, hall, cathedral and space buses, like a
  real mixing desk, so the voice sits in one consistent space.

**Picture**
- 100 shots, each chosen for its line. Some examples:
  - "You cross one bridge… another road" is on the bridge that reveals a second road.
  - "Everything underneath you is changing" is on the gold cracks lighting up under the rocks.
  - "Every smile / tear / fall" gets the star flash, the water drop and the
    falling figure, slowed down to fit.
- The cut is rhythmic, one shot per line, in the "You change / You lose
  things…" and "every success / failure / friendship…" montages.
- Transitions are dissolves, dips to black on section changes, white flashes
  on the impacts, a blur dissolve and a zoom-in.
- Finishing pass:
  - teal-shadow / gold-highlight grade and contrast curve
  - bloom on the gold light, plus an extra gold glow when the mote becomes the logo
  - film grain, vignette, 2.39:1 letterbox
  - camera shake and flash on every impact, RGB-split glitch on "getting
    lost" and "everything underneath you is changing"
- The trailer brief is followed:
  - The music cuts to silence before "Maybe it's been travelling beside us".
  - The gold mote blooms into the logo right after that line.
  - Three chimes land on smile / tear / fall.
  - It hard-cuts to black on her last word.

**Score and sound design** (synthesised, no licensing issues)
- A pad follows a chord plan tied to the script (`MUSIC` in `edl.py`):
  - A minor for the questions
  - a dissonant cluster for "endless can sound scary"
  - A **major** for the reveal and the final title
- Plucked arpeggios drive the "journey" sections. There's a sub-bass and air texture throughout.
- The music ducks under the voice and is EQ-carved around her formants.
- Sound design:
  - risers into the titles and sub impacts on them
  - soft booms and a rumble under "everything underneath you is changing"
  - footsteps on "one step… another… another"
  - a heartbeat under the reveal and chimes on the ending

## Rebuilding

```bash
pip install -r requirements.txt           # plus ffmpeg
python fetch_assets.py                    # needs assets.local.tsv (see the file)
python build_audio.py                     # ~1.5 min
python build_video.py                     # full render; `python build_video.py 20` = 20 s preview
python make_cuesheet.py
```

All creative decisions live in [`edl.py`](edl.py): line grouping, voice
effect per line, pause lengths, music plan, sound cues, and every shot.
Change a number and rebuild. Only changed shots are re-rendered.

`data/chunks.json` is the narration split into phrases (`analyze.py`
re-creates it if the narration audio ever changes).

## Privacy

This repo is public, so the unreleased narration audio, the clips, their
download links and all rendered media stay out of git (see `.gitignore`).
What is committed: the edit code, the phrase timings and the cue sheet. The
script text is in `edl.py`, `CUESHEET.md` and `data/`. Make the repo private
if the script shouldn't be readable before the announcement goes out.
