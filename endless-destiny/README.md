# Endless Destiny

A game by **Echoes in the Dark**, based on the song *Endless Destiny*, written and sung by Sonny Molina.

You play the Torchbearer, a hooded figure who walks the song's journey in one loop:
**sit → listen → dark → bridge → the other side → light → step → road → river**, and back where you began.

| Moment | What happens |
| --- | --- |
| The River | You sit beside a vast dark river under one golden star. |
| The Flame | You kneel and dip the torch into the star's reflection, and the gold climbs the torch. |
| The Dark | A gorge of scanned rock and dead trees. Leaf braziers catch your flame and stay lit behind you. |
| The Bridge | You step off the cliff into nothing, and each step forms a golden oak plank under your foot. |
| The Other Side | Thick fog, where it is still unknown. |
| The Light | You walk up seven worn steps to a 4-metre bronze cauldron shaped like the studio's leaf. The fire climbs its veins and a 20-metre column of flame turns the world from blue to gold. |
| The Road | A road of light runs down to the water. |
| The River | You sit beside something that doesn't stop. The leaf draws itself and the journey begins again. |

Along the way there are **9 echoes**: small leaves of light, one for each word in the song's chain. They are faint until you **listen**. Each echo asks one of the questions from the Endless Destiny announcement, and lights another vein of the leaf in the corner of the screen.

## Play it

The game runs in a web browser. No install is needed.

- **Online:** open the published link. This is the easiest way.
- **On your own computer:** the files have to come from a local web server, because browsers block games from loading their files straight off the disk. From this folder, run:
  ```
  cd endless-destiny/web
  python -m http.server 8000
  ```
  Then open http://localhost:8000 in Chrome, Edge, Safari or Firefox. Python comes with most Macs and Linux computers. On Windows, install it from python.org or the Microsoft Store.
- **itch.io:** zip the contents of `endless-destiny/web/` (with `index.html` at the top of the zip). Upload it as an HTML game and set the viewport to 1280 × 720 with fullscreen allowed.

## Controls

| | Keyboard and mouse | Touch | Gamepad |
| --- | --- | --- | --- |
| Walk | W A S D / arrows | Left thumb | Left stick |
| Look | Mouse (click to capture) | Right thumb | Right stick |
| Act (rise, gather the flame, lower the flame, sit) | E / Space / Enter | ACT | A |
| Listen | Hold Q or the right mouse button | Hold LISTEN | Triggers or X |
| Hurry | Shift | | Left stick press |
| Pause and settings | Esc / P | PAUSE | Start |

## The narrator

Every line is read out loud by the browser's built-in text-to-speech, using a deep English voice when one is available. The narrator can be switched off in Settings.

To use real recordings (for example your own cloned voice), see [`web/assets/voice/README.md`](web/assets/voice/README.md). A recording replaces the synthetic voice for that line, and any line without a recording keeps the text-to-speech.

## The leaf logo

The emblem in the game is a vector redraw of the Echoes in the Dark leaf. It draws itself on the title screen, fills with gold as you gather echoes, forms the channels of the bronze cauldron, is carved into the standing stones, and gathers from golden sparks at the end.

To show the exact official artwork as well, export the logo as a PNG with a transparent background and light lines, then save it as `web/assets/brand/logo.png` and set `"logo": "logo.png"` in `web/assets/brand/brand.json`. The title and ending screens fade it in once the leaf has finished drawing itself.

## What's inside

```
endless-destiny/
  web/                  the playable game (HTML + JavaScript + three.js)
    index.html
    src/                game code, one file per system
    assets/models/      photoscanned rocks, cliffs and dead trees (Poly Haven, CC0)
    assets/textures/    scanned ground, rock, stone and plank materials (Poly Haven, CC0)
    assets/voice/       optional narrator recordings
    assets/brand/       optional official logo
  docs/
    GAME_DESIGN.md      the design, beat by beat
    UNREAL_ENGINE_GUIDE.md   how to rebuild this in Unreal Engine 5 on your own PC
  CREDITS.md
```

## Honest limits

- This is a browser game, not Unreal Engine. It uses real photoscanned assets, physically based lighting, height fog, bloom and film grain, but it can't match Unreal Engine 5's Lumen and Nanite. [docs/UNREAL_ENGINE_GUIDE.md](docs/UNREAL_ENGINE_GUIDE.md) covers that step.
- The Torchbearer is built and animated in code rather than motion-captured. Because it is only ever seen from behind in silhouette, as the films ask, it holds up at a distance. It won't hold up in close-ups.
- The song itself isn't in the game yet. When it's released, it can play over the ending.
