# Endless Destiny: game design

**Studio:** Echoes in the Dark
**Source:** the song *Endless Destiny*, written and sung by Sonny Molina
**Genre:** a short third-person journey (10 to 15 minutes), built around a single idea
**Rule taken from the announcement:** every question stays unanswered, and no lyric is ever quoted.

## The idea in one line

The song says destiny has no finish line, so the game doesn't have one either. It ends where it began, at the river, and the first line changes from *"Somebody sat down…"* to *"You sat down…"*.

## Structure: ring composition

The journey walks the chain from the announcement and then comes back to the start:

```
A  THE RIVER    sit     you sit beside something that doesn't stop
B  THE FLAME    listen  the star's reflection becomes a flame
C  THE DARK     dark    a gorge; the torch is the only warm light
X  THE BRIDGE   bridge  the turn: step into nothing and the plank appears
C' THE OTHER SIDE side  fog; it's still unknown
B' THE LIGHT    light   the leaf cauldron is lit and the world turns from blue to gold
   THE ROAD     step, road  a road of light runs down to the water
A' THE RIVER    river   same river; it never stopped, and it never needed to
```

## Art direction (from the Seedance film scripts)

- Night only: true black, deep indigo, midnight blue and soft violet.
- **Molten gold is the only warm colour.** It comes from one golden four-pointed star, the torch flame, and whatever that flame lights. After the cauldron is lit, gold rolls out across the world.
- Thick haze makes every light glow, and the post-processing adds anamorphic streaks, film grain and a vignette.
- The Torchbearer is always seen from behind or in silhouette: a hooded, floor-length charcoal wool robe with gold thread at the hem and cuffs, dark leather gloves, and a 70 cm aged bronze torch with a leaf-shaped head.
- The world is empty of people.

## The leaf (studio emblem) in the game

The emblem is part of the story, not a logo stamped on top of it:

| Where | What it means |
| --- | --- |
| **The cauldron** | A 4-metre bronze leaf with raised veins. Fire climbs the veins "like golden water flowing uphill", then a 20 m column erupts from the tip. |
| **The star in the leaf's open point** | Lights when the cauldron is lit. It is the song's golden star, held in the studio's leaf. |
| **Echoes** | Nine small leaves of light, one for each chain word. |
| **HUD leaf** | Each echo gathered fills more of the leaf with gold. Lighting the cauldron ignites its star. |
| **Standing stones** | Carved with the leaf. The carvings glow when you listen. |
| **Ending** | Golden sparks drift in from every edge and gather into the leaf from the base upward, then the star ignites with one clean four-point flare (Shot 5 of THE FLAME). |
| **Microphone stands** | One waits at the far end of the bridge (THE FALL). Another stands alone at the river's edge at the end (THE IDENT), where you sit down beside it. |

## Mechanics

| Verb | Input | What it does |
| --- | --- | --- |
| Walk | move | A solemn pace. Hold hurry to go faster. On the bridge the pace is always steady. |
| Look | mouse / right thumb / right stick | Over-the-shoulder camera that eases back behind you while you walk. |
| Listen | hold | Sends a pulse of pale light across the ground. Echoes within range brighten and answer with a tone from where they are (3D sound), the hood turns toward the nearest one, and the leaf carvings glow. Walking while listening is slower. |
| Act | press | Rise · gather the flame (at the water) · lower the flame (at the cauldron) · sit beside the river. |

**Gating is soft.** Before the flame, the dark is "too dark to walk on". Before the cauldron is lit, "the light pulls you to the leaf". The bridge only appears when you walk off the cliff edge.

**Leaf braziers** along the gorge and the road catch your flame as you pass and keep burning behind you, so the trail of light you leave is the "echo in the dark".

## Echoes: the nine questions

Each echo asks the nested questions from Brandon's announcement (Version E, "The Loop"). It never answers them.

| # | Word | Where |
| --- | --- | --- |
| 1 | Sit | beside the starting stone |
| 2 | Listen | on the shore |
| 3 | Dark | in the gorge |
| 4 | Bridge | at the cliff edge |
| 5 | Side | out in the fog on the far side (you need to listen to find it) |
| 6 | Light | on the platform steps |
| 7 | Step | at the top of the road |
| 8 | Road | where the road bends |
| 9 | River | on the final shore (off the path) |

## Sound

Everything is synthesised live, following the film scripts:

- The river, night air, and a low drone on A and E.
- Wind rising from the canyon.
- A glassy shimmer as the flame is gathered.
- A deep wooden knock and a soft bell for every plank, climbing a pentatonic scale as you cross.
- **One full second of total silence**, then a chest-shaking impact and the roar of the fire.
- A single low tone for the emblem.

The narrator reads every line aloud with text-to-speech. Real recordings can replace any line (see `web/assets/voice/README.md`).

## Where the money is (studio plan)

1. **Release the game with the song.** On release day, the game is the song's interactive trailer. Put it on itch.io as free or pay-what-you-want, link it from the YouTube video, TikTok and Discord, and give Discord first access, just as the song goes to Discord first.
2. **Voice it.** Replace the text-to-speech with the real narrator voice: record it, or clone it with the voice tools. That costs nothing extra and is the biggest quality jump available.
3. **Score it.** When the song is out, it plays over the ending and loops on the title screen. Every playthrough is a listen.
4. **Film it.** Gameplay captures of the bridge forming and the world turning gold make vertical clips for TikTok and Reels, and can feed the Seedance and Higgsfield pipeline as reference shots.
5. **Then Unreal.** The vertical slice in [UNREAL_ENGINE_GUIDE.md](UNREAL_ENGINE_GUIDE.md) produces the trailer that earns a Steam page. Get the wishlists before building more game.
