# Endless Destiny in Unreal Engine 5

The browser version is the playable prototype: the design, the story beats, the timing and the look are all worked out there. This guide covers rebuilding it in Unreal Engine 5 on your own PC for a realistic, Steam-ready version.

## 1. Why this can't be done from the cloud session

Unreal Engine can't be installed in the cloud session that built the browser game:

- **It needs a real graphics card.** The Unreal Editor draws everything live with Lumen and Nanite, and the cloud session has no GPU.
- **It needs your Epic Games account.** Downloading the engine means signing in and accepting Epic's licence, and that has to be you.
- **It's big.** The engine plus a realistic project and its caches runs to tens of gigabytes. Plan for roughly 100 GB free on an SSD.

## 2. Check your PC

These are Epic's recommended specs for [Unreal Engine 5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine):

| | Recommended |
| --- | --- |
| OS | Windows 11 (Windows 10 22H2 minimum) |
| CPU | Quad-core Intel or AMD, 2.5 GHz or faster |
| RAM | **32 GB** |
| Graphics | DirectX 12 card with **8 GB or more** of video memory, latest drivers |
| Disk | Fast SSD, about 100 GB free |

With less than this, the editor still opens, but realistic scenes will crawl. The browser version runs on almost anything.

## 3. Install

1. Download the **Epic Games Launcher** from unrealengine.com and sign in.
2. Open the **Unreal Engine** tab, then **Library**, then the **+** next to *Engine Versions*. Choose **5.8** and install it.
   In *Options*, untick target platforms you don't need, such as Android and iOS, to save space.
3. Launch it, then choose **Games → Third Person → Blueprint**, *Quality: Maximum*, *Starter Content: off*. Name the project `EndlessDestiny`.

Stay in **Blueprint** at first; C++ isn't needed for this game. Blueprint-only projects usually package without Visual Studio. Once you add C++, Epic recommends Visual Studio 2026 for 5.8.

## 4. The night look (matching the films)

Place these in the level. Every item has a direct equivalent in the browser version.

| Unreal actor / setting | Values to start from | Browser equivalent |
| --- | --- | --- |
| Project Settings → Rendering | Dynamic GI **Lumen**, Reflections **Lumen**, Shadows **Virtual Shadow Maps** (UE5 defaults) | `world.js` lights |
| Directional Light "Starlight" | Cool blue (about 9000 K), low intensity, pointing down from high above | `starlight` |
| Directional Light "Star rim" | Warm gold, very low, aimed from the golden star's direction (north-west, 24° up) | `starRim` |
| Sky Light | Real-time capture on | baked sky environment |
| Exponential Height Fog | **Volumetric Fog on**, violet-blue albedo, dense near the ground | `edFog` height fog |
| Local Fog Volumes | Fill the canyon so it looks like cloud far below | `mist.js` canyon layers |
| Post Process Volume (Infinite Extent) | Manual exposure, bloom, film grain, vignette, slight chromatic aberration, anamorphic flare | `post.js` |

- **The torch:** a Point Light on the right-hand socket. Use a warm temperature (about 2700 K), a small source radius, and set *Volumetric Scattering Intensity* to around 4 so the haze glows around it. Add a Niagara system for the narrow flame and the slow embers.
- **The star:** a small, very bright emissive quad placed far away to the north-west, with a four-point lens flare. Its reflection on the river then comes free from Lumen.
- **The river:** a large plane with a near-black, very smooth material, or the Water plugin's Water Body. A little ripple normal makes the star's reflection tremble.

## 5. Realistic assets

- **[Poly Haven](https://polyhaven.com)** is free and CC0, so you can use anything commercially. The browser version already uses its rocks, cliffs, dead trees and ground textures (see `CREDITS.md`). Download the same assets as glTF or FBX at 2K–4K so both versions match. In Unreal, turn **Nanite on** for every rock.
- **[Fab](https://fab.com)** has Megascans. The free-claim period ended with 2024, so they're bought per asset now. Fab also has free content, and Quixel's Megaplants are free to use in Unreal.
- **The Torchbearer:** model the robe in Blender, where a hooded robe is a beginner-level project, and use **Chaos Cloth** so it swings for real. The figure is always faceless inside the hood, so no MetaHuman face is needed.
- **Animation:** Epic's free **Game Animation Sample** (UE 5.4 and later) includes hundreds of motion-captured moves and motion matching, so the walk looks real. Add custom poses for kneeling at the water, raising the torch and sitting.
- **The leaf cauldron:** build it in Blender from the logo. Trace the SVG from `web/src/emblem.js`, extrude it, and model the veins as raised channels. Bake a vein mask texture for the fire material.

## 6. Rebuilding the mechanics in Blueprint

| Mechanic | Unreal version |
| --- | --- |
| **Listen pulse** | On *Listen* held, a Timeline drives `PulseCenter` and `PulseRadius` in a **Material Parameter Collection**. The landscape and rock materials add a thin pale ring where `distance(WorldPosition, PulseCenter) ≈ PulseRadius`. Echo actors brighten when the ring passes and play a spatialised MetaSound. |
| **Echoes** | A Blueprint actor holding a glowing leaf sprite or mesh. On overlap it flies into the torch, plays the question lines with subtitles, and adds one to the HUD leaf. |
| **Bridge** | A Blueprint with an **Instanced Static Mesh** of an oak plank. While the player is in the bridge corridor over the canyon, add instances just ahead of their feet, play a gold-dust Niagara burst and a knock-and-bell MetaSound, and fade each plank's emissive from gold to warm timber. |
| **Cauldron** | A material scalar `Fill` (0 to 1), animated by a Timeline, lights the vein mask from the base upward. At 1, spawn the 20 m flame column (Niagara) and a big warm light. |
| **Gold wave** | A Material Parameter Collection `GoldRadius` read by every world material. Surfaces inside the radius warm up, and a bright band travels outward. Blend the fog and lights from blue to gold at the same time. |
| **Narration** | Sound waves with subtitle data. Keep the same line ids as `web/assets/voice/manifest.json` so one set of recordings serves both versions. |
| **Story beats** | A simple Level Blueprint or GameMode state machine with the same beats as `web/src/story.js`: opening → sitting → shore → flame → journey → crane → lighting → endSit → ended. |

## 7. Money and licensing

- **Unreal Engine:** free until a game earns **US$1 million** gross over its lifetime. After that the royalty is **5%**. Revenue through the Epic Games Store is exempt, and launching on Epic's store at the same time lowers the rate to 3.5% ([Epic licensing](https://www.unrealengine.com/license)).
- **Steam:** US$100 per game, which Valve pays back once the game earns US$1,000.
- **This order makes sense:** ship the browser version with the song, cut a trailer from the Unreal vertical slice, open the Steam page, and collect wishlists before building a bigger game.

## 8. What to expect

A realistic Unreal version of this one level is a **vertical slice**, not a full game. For one person learning Unreal, expect weeks to a few months.

Keep the scope exactly as it is: one river, one gorge, one bridge, one leaf, one road. Small teams that win with realistic UE5 games start with one thing done extremely well. *Bodycam* began as two young brothers testing Unreal Engine 5's lighting.
