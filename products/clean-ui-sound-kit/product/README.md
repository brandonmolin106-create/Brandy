# Clean UI Sound Kit — Vol. 1

113 modern interface sounds, made by Jacksons world. Royalty-free for any app, website, game, video or stream you make, including ones you sell.

## What's in the box

```
Clean-UI-Sound-Kit/
  wav/            113 x 44.1 kHz 16-bit mono WAV   (apps, games, editors)
  ogg/            the same 113 as OGG Vorbis        (web, Android, Godot)
  mp3/            the same 113 as MP3               (browsers, video timelines, no-nonsense)
  index.csv       every file with category, description and length in seconds
  preview.mp3     one-minute montage, two sounds from every category
  bonus/
    generate_ui_sfx.py   the synth engine that made the kit. Roll your own variations.
  LICENSE.txt
  README.md
```

## Categories (variations in brackets)

click (8) · tap (6) · hover (4) · toggle_on (4) · toggle_off (4) · switch (4) · success (6) · error (6) · warning (4) · notification (8) · message_sent (4) · message_received (4) · pop (6) · swipe (4) · whoosh (4) · lock (3) · unlock (3) · typing_tick (4) · scroll_tick (4) · delete (4) · undo (3) · achievement (4) · level_complete (3) · countdown_tick (3) · loading_loop (3) · ambient_pad_loop (3)

Files are named `category_01.wav`, `category_02.wav`, … so you can pick a random variation in one line.

## Using it

**Web (JS)** — `new Audio('mp3/click_01.mp3').play()`. Preload the ones you use. For variation: `const c = clicks[Math.floor(Math.random()*clicks.length)]`.

**Flutter** — add `mp3/` to assets, play with `audioplayers` or `just_audio`.

**React Native / Expo** — `expo-av`: `const { sound } = await Audio.Sound.createAsync(require('./mp3/tap_01.mp3')); await sound.playAsync();`

**iOS / Android native** — WAV or MP3 both import directly. Keep UI sounds under 50 ms for taps and clicks (they are).

**Unity / Godot / GameMaker** — drop `wav/` (Unity, GameMaker) or `ogg/` (Godot) into your audio folder. Random pick per category.

**Video editors** — drag `mp3/` or `wav/` onto the timeline. `whoosh`, `swipe`, `pop` and `notification` are the editor favourites.

**Loops** — `loading_loop_*` (1 s) and `ambient_pad_loop_*` (2 s) are cut to exact lengths so they loop seamlessly.

## Roll your own (bonus)

```
pip install numpy
python bonus/generate_ui_sfx.py --out my_sounds --seed 5
```

Change the seed for new noise textures, or edit a recipe (frequency, glide, envelope) to match your brand. Everything you generate is covered by the same licence.

## Licence

Royalty-free, commercial use allowed, unlimited projects, no credit required. You can't resell or redistribute the sounds themselves as a pack. Full text in `LICENSE.txt`.

## Support

Something wrong or want a category added? Message @jacksonf5l on X: https://x.com/jacksonf5l
