# Echoes 8-Bit SFX Pack — Vol. 1

136 retro game sound effects, made by Echoes in the Dark. Royalty-free for any game, app, video or stream you make, including ones you sell.

## What's in the box

```
Echoes-8Bit-SFX-Vol1/
  wav/            136 x 44.1 kHz 16-bit mono WAV  (drop-in for Unity, Godot, GameMaker, Unreal)
  ogg/            the same 136 sounds as OGG Vorbis (smaller, web/mobile friendly)
  index.csv       every file with category, description and length in seconds
  preview.mp3     40-second montage, two sounds from every category
  bonus/
    generate_sfx.py   the synth engine that made the pack. Roll your own variations.
  LICENSE.txt
  README.md
```

## Categories (variations in brackets)

jump (8) · land (4) · coin (8) · gem (6) · powerup (6) · hit (8) · hurt (6) · death (4) · explosion (8) · laser (8) · shoot (6) · ui_click (6) · ui_confirm (4) · ui_cancel (4) · ui_error (4) · menu_move (4) · level_up (4) · win (3) · lose (3) · door (4) · teleport (4) · footstep (8) · splash (4) · alarm (3) · heartbeat (2) · engine_loop (3) · drone_loop (4)

Files are named `category_01.wav`, `category_02.wav`, … so you can pick a random variation in code with one line.

## Using it

**Unity** — drag the `wav/` folder into `Assets/Audio/SFX/`. Use `AudioSource.PlayOneShot(clip)`. For variation: keep an `AudioClip[]` per category and play `clips[Random.Range(0, clips.Length)]`.

**Godot 4** — copy `ogg/` into `res://audio/sfx/`. Godot imports OGG automatically. Use an `AudioStreamPlayer` and set `stream` to a random pick from the category.

**GameMaker** — Import the WAVs as sounds. `audio_play_sound(choose(snd_coin_01, snd_coin_02, snd_coin_03), 10, false)`.

**Unreal** — import the WAVs; use a Sound Cue with a Random node over the variations.

**Loops** — `engine_loop_*` and `drone_loop_*` are cut to exact lengths (1 s and 2 s) so they loop seamlessly. `heartbeat_*` loops with its own gap built in.

## Roll your own (bonus)

```
pip install numpy
python bonus/generate_sfx.py --out my_sfx --seed 7
```

Change the seed for different noise textures, or edit the recipes at the top of the file (frequencies, sweeps, envelope times) to tune a sound to your game. Everything you generate is covered by the same license.

## Licence

Royalty-free, commercial use allowed, unlimited projects, no credit required. You can't resell or redistribute the sounds themselves as a sound pack. Full text in `LICENSE.txt`.

## Support

Something wrong or want a category added in Vol. 2? Message us on X: https://x.com/jacksonf5l
