# Nothing Becomes Everything
*a game by Brandon*

A story-driven Roblox game built from Brandon's speeches. Each metaphor becomes a place you
play through: you climb a clock tower while time eats the seconds, climb out of a hole on
better thoughts, let go of heavy words in a glass box, walk a road toward a wall that turns
out to be a pebble, break your chains with three "I CAN" bells, and watch the sunrise from
the summit where *nothing becomes everything*. Brandon's own voice narrates it all, with
captions.

Everything works before you upload anything. Captions still show, the screens say
"Brandon's video goes here", and the shop items stay hidden until you add their IDs.

---

## What's in this folder

| Path | What it is |
|---|---|
| `NothingBecomesEverything.rbxlx` | **The Roblox place.** Open it in Roblox Studio. |
| `src/` | Every script as a `.lua` file, in the same folders as in Studio's Explorer. The place already contains them; these copies are for reading and for rebuilding. |
| `upload/` | The files you upload to Roblox: three audio packs, two loading screens, the audio manifest, and `videos/` (the optional zone videos, sent to you separately because they're big). |
| `tools/build_place.py` | Rebuilds the place from `src/`, `tools/story.json` and `upload/audio_manifest.json`. |
| `tools/validate_place.py` | Checks the place (details at the end). |
| `tools/placegen/` | The code that builds each zone. |
| `tools/story.json` | Zone names, themes, Insights and phrases (see "Changing text"). |
| `tools/make_media.py` | Built the audio packs, videos and loading screens (not needed to play). |

**Size:** 2,019 parts in total (under the 4,000 budget), 36 scripts, all strict-typed Luau.

---

## The journey, zone by zone

Players start in the Clearing. Each zone ends when you collect its **Insight** (the key
line). Collecting an Insight saves it in your Journal and opens the next portal. You can
go back to any zone you've unlocked.

**0. The Clearing (hub).** A calm night meadow with a crackling campfire, log benches,
fireflies, glowing flowers and eight tall glowing stones. A big 9:16 cinema screen stands at
the north end. The first time you arrive, Brandon says *"Just a friendly reminder that you
are amazing."* A **Journal** book on a pedestal lets you reread your Insights. A stone
tablet maps the journey (open, locked or done). Six **portals** stand in a ring, each with
the zone's name on the arch. Locked portals look grey and say LOCKED; finished ones say
COMPLETE.

**1. The Clock Tower (time).** A desert of falling sand around a brass clock tower. You
climb a square spiral of brass gears. Some turn under your feet, and giant wall gears and a
swinging pendulum keep the clock ticking. Twice the path becomes a **clock dial**: stand on
the hub, wait for a clock hand to sweep past, and walk out along it. A giant hourglass
pours sand. Speech stones play `time_1` (at the bottom) and `time_2` (halfway up). The
Insight on the roof is *"Even while you are watching this, it is already taking the next
second."*

**2. The Hole (hole).** You start at the bottom of a deep pit. The walls are carved with
"I CAN'T", "I'M NOT GOOD", "WHY TRY" and "I CAN'T DO IT", and a sliver of starry sky shows
far above. A glowing **Better Thought** orb waits ("I CAN", "I'M LEARNING", "ONE STEP",
"I'M STRONG", "KEEP GOING", "LOOK UP", "I'M ENOUGH"). Touch it and a new flight of stone
steps slides out of the wall, one step at a time, up to where the next orb waits. As you
climb, a shaft of light opens from the sky and the carved words below you fade. The lines
play in order: `hole_1` at the bottom, `hole_step` after the first thought, then `hole_2`,
`hole_3`, `hole_4`, and `hole_move` at the rim. The Insight is *"One better thought is one
step higher."*

**3. The Glass Box (glass).** You're inside a glass room on a lakeshore. Heavy word blocks
("WORTHLESS", "WEIRD", "TOO QUIET", "NOT GOOD", "I CAN'T") fall in one at a time, and the
water rises with each one. Under the surface the screen tints blue and the music sounds
muffled. The water is only a picture: nobody can drown, nothing does damage, and you can
always walk. Hold **"Let it go"** on a block to dissolve it and drain the water. The twist:
the door was **unlocked the whole time**, and it starts to glow once the water is low. Walk
out and the box shatters outward. The Insight on the pier is *"Not everything that tries
reaching for you needs to stay in you."*

**4. The Road (road).** A long road at dusk, with street lamps and telephone poles, heading
toward a **colossal wall** that blocks the horizon. It barely changes for most of the walk.
Then, about 260 studs out, it starts shrinking smoothly as you get closer, until it's a
small rock you step over. That's the moment Brandon says *"The truth is, you didn't hit a
wall. You just met something small and gave it a big name,"* which is also the Insight at
the lookout beyond.

**5. Chains (chains).** A stormy valley. Walk through the gate and glowing chains lock onto
your legs, dragging a heavy weight, and you slow right down. Ring the three **I CAN** bells.
Each one cracks the chains a little and lets you move a bit faster. The third bell breaks
them: a burst of light, the storm clears, and you get a speed boost for a sprint-and-jump run
up the mountain path. The Insight at the top is *"Never let your mind lock you in a place
your body could have left."*

**6. The Summit (everything).** A peak above the clouds at sunrise, over an endless ocean,
with a marble monument that reads **NOTHING BECOMES EVERYTHING**. The Insight is *"Keep on
going, even when it feels like nothing, because one day that nothing becomes everything."*
Collecting it starts the **finale**: the finale music, confetti, the sun rising higher,
Brandon's last line (`everything_3`), the credits ("a game by Brandon"), and a portal home.

**Everywhere:**
- Every zone has a screen for Brandon's video and speech stones you can **Listen** to again.
  A stone glows while its line plays.
- The zone name and theme appear between cinematic bars when you arrive.
- The lighting, sky and music change for each zone.

---

## Step by step

### 1. Open and publish
1. Open **Roblox Studio** → **File → Open from File…** → choose `NothingBecomesEverything.rbxlx`.
2. **File → Publish to Roblox As…** → create a **new experience**. It stays private (only
   you can play) until you choose otherwise.

### 2. Upload the free files
In Studio, open the **Asset Manager** (**Window → Asset Manager**, then **Import**), or use
the [Creator Dashboard](https://create.roblox.com/dashboard/creations). When a file is
ready, right-click it → **Copy Asset ID**. Roblox moderation checks each file first, which
can take a while.

| File (in `upload/`) | Type | Cost | Roblox's limit | This file |
|---|---|---|---|---|
| `voice_pack.ogg` | Audio | Free | .mp3/.ogg/.wav/.flac, < 20 MB, < 7 min, ≤ 48 kHz | 2:39, 2.3 MB, all 24 lines |
| `sfx_pack.ogg` | Audio | Free | same | 0:40, 0.6 MB, all 14 sounds |
| `music_pack.ogg` | Audio | Free | same | 4:52, 3.2 MB, all 8 tracks |
| `loading_screen.png` *or* `loading_screen_no_photo.png` | Image | Free | .png/.jpg/.gif/.tga/.bmp | 1920×1080 |

That's only **3 audio uploads**, because every line, sound and track lives inside one file
per type. The game plays just the right slice (see "How it works").
ID-verified accounts can upload 2,000 audio files per 30 days (unverified: 100).

### 3. Paste the IDs into Config (the one place you edit)
In Studio's Explorer: **ReplicatedStorage → Config**. Replace the zeros with your numbers:

```lua
VoicePackId = 0,    -- upload/voice_pack.ogg
SfxPackId = 0,      -- upload/sfx_pack.ogg
MusicPackId = 0,    -- upload/music_pack.ogg
LoadingImageId = 0, -- upload/loading_screen.png (or the no-photo one)
```

### 4. Optional: the zone videos (these cost Robux, so read this first)
There's one screen per zone, and the videos are in `upload/videos/`:

| File | Screen | Length |
|---|---|---|
| video_hub.mp4 | The Clearing | 1:40 |
| video_time.mp4 | The Clock Tower | 2:15 |
| video_hole.mp4 | The Hole | 1:17 |
| video_glass.mp4 | The Glass Box | 1:26 |
| video_road.mp4 | The Road | 1:15 |
| video_chains.mp4 | Chains | 1:32 |
| video_everything.mp4 | The Summit | 1:42 |

All seven are 576×1024 (vertical 9:16, like the screens), H.264 .mp4, and under 5 minutes.

- **Cost: 2,000 Robux per video** (14,000 for all seven). You must be **13+ and ID
  verified**, and you can upload at most 20 a day. In Studio, first turn on **File → Beta
  Features → Video Uploads**, or upload on the web under
  [Creations → Video](https://create.roblox.com/dashboard/creations?activeTab=Video).
- **If Roblox rejects a video, you don't get the Robux back.** Videos showing a real
  person's face may be rejected. **Upload one video first, wait until it's approved, and only
  then buy the others.** If you're unsure, skip the videos. The screens look finished
  without them.
- Paste each ID into `Config.Videos` (for example `hub = 123456789`).

Roblox plays at most 2 videos at once. This game only ever plays the screen in your current
zone and pauses the rest.

### 5. Let Studio save progress (for testing)
Progress is saved with DataStores. Studio can't use them until you allow it:
**Game Settings → Security → Enable Studio Access to API Services**. Roblox recommends doing
this on a **test copy** of the game, because Studio then writes to the same saved data as the
live game. With it off, everything still works, but progress resets when you stop, and a
small message says progress isn't being saved.

### 6. Test (Home → Play)
- **Loading screen:** your image (or the built-in title card), then a fade.
- **The Clearing:** the intro card appears and Brandon's welcome plays with a caption. Try
  **Journal**, **Settings** (volume sliders, captions, reduce motion) and the map tablet.
- **The Clock Tower portal:** climb the gears, ride a clock hand from a dial hub, and collect
  the Insight on the roof. The Insight card shows, the Hole portal opens, and the tracker
  dot fills in.
- **Work through the other zones.** To test fast, you can temporarily paste IDs and play
  each zone in order. Progress saves if API access is on.
- **Phones:** in Studio, use the **Device** emulator (Test tab) to check the buttons and
  captions at phone size.

### 7. Optional extras (hidden while their ID is 0)
- **Badges** (one per zone plus the finale): Creator Dashboard → your game → **Engagement →
  Badges**. The first 5 badges each day are free, and more cost 100 Robux each. Paste the
  IDs into `Config.BadgeIds`.
- **"Echo Aura" game pass** (a soft glowing trail): **Monetization → Passes** → create one
  and set a price → **Copy Asset ID** → `Config.GamePassId`. A small shrine by the fire sells
  it, and owners can switch it off in Settings.
- **"Tip Brandon" developer product:** **Monetization → Developer Products** → create one →
  **Copy Asset ID** → `Config.DevProductIds.TipBrandon`. A lantern by the campfire appears.
  Tipping shows a thank-you and sparkles. Don't promise anything in return for tips.

### 8. Go public
Open the game in the Creator Dashboard, finish the **Maturity & Compliance questionnaire**,
and choose who can play:
- **16+:** your account must be at least 2 days old, you need an age check (face or ID),
  and you must finish the questionnaire.
- **All ages:** everything above, plus 2-step verification, plus either 2 months of Roblox
  Premium/Plus or a refundable 1,000 Robux publishing fee.

### 9. Social links go on the experience page, never in the game
Creator Dashboard → your game → **Engagement → Social Links**. You need a 16+ age check to
add them, and only age-checked 16+ players can see them. **YouTube is allowed. TikTok isn't
one of the link types** (the list is Facebook, Twitter/X, YouTube, Twitch, Discord, Guilded
and a Roblox community). Don't put any handle, link or logo inside the game, on signs, or
in chat. The game has none, and the validator checks that.

---

## Changing text and lines

- **Quick edits in Studio:** open **ReplicatedStorage → Content**. You'll find every caption
  (`Content.Lines`), each zone's name, theme and Insight (`Content.Zones`), the orb phrases,
  the glass words, the monument words and the credits (`Content.Story`). Change the text in
  quotes and publish.
- **Edits that survive a rebuild:** `Content.lua` is generated. Change the text in
  `tools/story.json` (zones, phrases, credits) or `upload/audio_manifest.json` (captions and
  timings), then run `python3 tools/build_place.py`.
- **Swapping in new audio:** rebuild the pack, keep the manifest's `start`/`end` times in
  step with it, upload it, and paste the new ID into Config.
- **Which stone plays which line:** each speech stone has a `LineId` attribute (Properties
  → Attributes). Auto-played story beats are invisible `BeatMarker` parts in
  `ReplicatedStorage.ZoneKits` (also a `LineId`), plus a few calls in
  `StarterPlayerScripts.ClientModules.Zones.*`.
- **Tuning:** `Config` also has the volumes, the chained and sprint speeds, the glass drop
  timing and the DataStore name. Change the DataStore name to reset everyone's progress.

---

## How it works (for tinkering)

- **Server owns the story, clients draw it.** `ServerScriptService.Modules.ZoneService`
  tracks each player's zone, checkpoint and puzzle progress (orbs, blocks, bells) and checks
  every request. For example, the player must be close to the orb, and it must be the next
  one. Clients show only what the server confirms.
- **Per-player zone kits.** Things that differ per player (the Hole's steps and orbs, the
  glass box, blocks and water, the road wall, the clock hands and gears) live in
  `ReplicatedStorage.ZoneKits`. The client clones its zone's kit locally, so two players
  never see each other's puzzle state. Clock hands and gears turn from the server clock, so
  everyone sees the same positions, and a character standing on a hand is carried along.
- **Audio packs.** Each line, effect and track is a slice of its pack:
  `Sound.PlaybackRegionsEnabled = true`, `Sound.PlaybackRegion = NumberRange.new(start, end)`.
  Music loops inside its slice with `Sound.LoopRegion` and crossfades between zones.
  Captions are timed to the slice length, so they work even with no audio uploaded. Volumes
  go through the Music, Voice and SFX SoundGroups.
- **Autoplay policy.** `PolicyService:GetPolicyInfoForPlayerAsync().IsEndlessContentAutoplayAllowed`
  decides whether music and videos may start by themselves. If it's false (or the check
  fails), music waits for a **Play music** button and videos wait for **Play video** and play
  once. Studio tests always autoplay (`Config.AlwaysAutoplayInStudio`).
- **Saving.** `ProgressStore` uses DataStoreService with pcall and retries. Saves use
  `UpdateAsync` with a merge: Insights are joined together (the earliest date wins), so two
  servers, or a save after a failed load, can't erase progress. If DataStores are
  unavailable in Studio, it carries on in memory. It autosaves every 90 seconds and saves
  when you leave and when the server closes.
- **Purchases.** `ProcessReceipt` records each PurchaseId in the player's saved data and
  answers `PurchaseGranted` only after that record is saved (otherwise `NotProcessedYet`, and
  Roblox tries again later). A receipt is never granted twice.
- **Prompts.** Every ProximityPrompt has an `Action` attribute (portal, insight, listen,
  bell, letgo, door, video, journal, tip, aura, return). The server handles the important
  ones, and the client handles the cosmetic ones.
- **Streaming and performance.** `Workspace.StreamingEnabled` is on, and zones are 2,400+
  studs apart, so a phone only loads the zone you're in. Every part is anchored. Decoration
  doesn't collide or cast shadows.
- **Mobile first.** The buttons are 44 px touch targets in the top-right safe area, the
  zone tracker is a compact row of 6 dots, and captions sit low in the centre, between the
  thumbstick and the jump button. **Reduce motion** replaces slides and big movements with fades.

---

## Verified facts (checked 28 Sep 2026)

| Fact | Source |
|---|---|
| Video: 13+ ID verified; .mp4/.mov; ≤ 5 min; ≤ 4096×2160; < 3.75 GB; **2,000 Robux per upload**; max 20 uploads a day; the Video Uploads beta is needed in Studio; **max 2 videos playing at once**; VideoFrame must be in a ScreenGui/SurfaceGui/BillboardGui | [Creator Docs: Video frames](https://create.roblox.com/docs/ui/video-frames) |
| VideoFrame.Volume is 0 to 100; `Looped`, `Playing`, `Loaded`, `Ended` | [VideoFrame reference](https://create.roblox.com/docs/reference/engine/classes/VideoFrame) |
| A rejected video's fee isn't refunded (copyright rejections at launch) | [DevForum: Video uploads beta](https://devforum.roblox.com/t/video-uploads-beta-add-short-form-video-to-your-experience/2630621) |
| Audio: .mp3/.ogg/.wav/.flac, < 20 MB, < 7 min, ≤ 48 kHz; free; 2,000 per 30 days (ID verified), 100 (unverified) | [Creator Docs: Audio assets](https://create.roblox.com/docs/audio/assets) |
| `Sound.PlaybackRegion` and `Sound.LoopRegion` are NumberRanges in seconds, active when `PlaybackRegionsEnabled` is true; `Play()` starts from the last TimePosition set by a script | [Sound reference](https://create.roblox.com/docs/reference/engine/classes/Sound) |
| `IsEndlessContentAutoplayAllowed` covers video/audio that "automatically and endlessly plays"; `AllowedExternalLinkReferences` "is a legacy field. It always returns an empty array" | [PolicyService reference](https://create.roblox.com/docs/reference/engine/classes/PolicyService) |
| Social links: only on the game page, never inside the game; a 16+ age check is needed to add them and to see them; types: Facebook, Twitter, YouTube, Twitch, Discord, Guilded, Roblox community (no TikTok) | [Creator Docs: Social media links](https://create.roblox.com/docs/production/promotion/social-media-links) |
| Other attempts to send players off Roblox aren't allowed; personal information rules (full names, media of yourself) | [Roblox Community Standards](https://about.roblox.com/community-standards) |
| Studio needs "Enable Studio Access to API Services" for DataStores; use a test copy | [Creator Docs: Data stores](https://create.roblox.com/docs/cloud-services/data-stores) |
| Error 403 `StudioAccessToApisNotAllowed` when that setting is off | [Data store error codes and limits](https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits) |
| ProcessReceipt: return PurchaseGranted only after granting; receipts are retried when NotProcessedYet; the same purchase can run on two servers at once | [MarketplaceService.ProcessReceipt](https://create.roblox.com/docs/reference/engine/classes/MarketplaceService#ProcessReceipt) |
| Passes and developer products: Monetization → Passes / Developer Products → Copy Asset ID | [Passes](https://create.roblox.com/docs/production/monetization/passes), [Developer products](https://create.roblox.com/docs/production/monetization/developer-products) |
| Badges: 5 free per game per 24 h, then 100 Robux each; `AwardBadge` is deprecated in favour of `AwardBadgeAsync` | [Badges](https://create.roblox.com/docs/production/publishing/badges), [BadgeService](https://create.roblox.com/docs/reference/engine/classes/BadgeService) |
| SurfaceGui buttons only get input from PlayerGui, so the screens use ProximityPrompts | [In-experience UI containers](https://create.roblox.com/docs/ui/in-experience-containers) |
| `Player:RequestStreamAroundAsync` loads the destination before a teleport when streaming is on | [Player reference](https://create.roblox.com/docs/reference/engine/classes/Player) |
| Public publishing: 16+ needs a 2-day-old account, an age check and the questionnaire; all ages also needs 2FA plus 2 months of Premium/Plus or a refundable 1,000 Robux fee | [Publish games and places](https://create.roblox.com/docs/production/publishing/publish-games-and-places) |

---

## Moderation risks (read before paying for anything)

1. **Your face.** Videos and the photo loading screen show you, and moderation may reject
   videos that show a real person's face. A rejected video still costs 2,000 Robux, so
   upload one and wait. If the photo loading screen is rejected (images are free to retry),
   use `loading_screen_no_photo.png`.
2. **No off-platform references in the game.** There's no TikTok handle, link, logo or
   name anywhere in the place or scripts, and no web links at all. `tools/validate_place.py`
   fails the build if one appears. Social links go only on the experience page (step 9).
3. **Your name.** The game only ever says "Brandon" (for example "a game by Brandon"). Keep
   it that way in descriptions and thumbnails too.
4. **Negative words on purpose.** The Hole's carvings ("I CAN'T", "WHY TRY") and the glass
   blocks ("WORTHLESS", "WEIRD") are self-talk that the player overcomes. Mention it
   honestly in the questionnaire. It's in a positive, uplifting context, with no bullying of
   other players.
5. **Autoplay.** Handled through PolicyService (see "How it works").
6. **Chat.** The game only uses Roblox's default chat.
7. **Ownership.** The voice is yours, and the music and sound effects were made by code for
   this game (`tools/make_media.py`), so there's no one else's copyrighted audio.

---

## Rebuilding and validating (for developers)

```bash
python3 tools/build_place.py      # regenerate Content.lua + the place (+ tools/.cache/sourcemap.json)
python3 tools/validate_place.py   # all checks below; downloads luau-lsp, lune and the API dumps into tools/.cache on first run
```

The validator checks that:
1. the file is well-formed XML (Roblox place format 4);
2. every class, property, XML data type and enum value exists in rbx-dom's reflection
   database **and** in Roblox's current API dump (nothing deprecated), and the attributes
   and tags decode;
3. the compliance scan passes (no links, handles, social names or full name in any string
   or script), and every script in the place matches its file in `src/`;
4. every part is anchored and the part count is under 4,000;
5. **jump gaps are makeable:** every hop between consecutive platforms (the `PathGroup` /
   `PathOrder` attributes) is ≤ 5 studs across and ≤ 2 studs up. The clock-hand rides are
   checked as sweeps. Current worst: Clock Tower 3.0 / 2.0, Hole 0.7 / 2.0, Chains 4.0 / 1.0;
6. `tools/check_place.luau` loads the place in **Lune** (the same Roblox DOM library Rojo
   uses) and checks the structure the scripts need. It covers the zones, arrival pads,
   Insights, portals, the 9:16 screens with placeholders, prompt actions, that every voice
   line and sound effect is used and exists in `Content`, the kits (7×6 steps, 7 orbs, one
   block per word, visual-only water) and the Config defaults;
7. **luau-lsp** type-checks all 36 scripts with Roblox types (all `--!strict`), with both
   the classic and the new Luau type solver.

---

## Credits
- **Words and voice:** Brandon.
- **Music, sound effects and every 3D build:** made for this game in code. They're
  royalty-free, and you own them.
- **Fonts:** Roblox built-ins (Balthazar via `Enum.Font.Fantasy`, BuilderSans, Roman
  Antique). The loading images use Cinzel Decorative and Archivo Black (SIL Open Font
  License).
