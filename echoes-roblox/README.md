# Echoes in the Dark — Roblox experience

A calm, cosmic Roblox game built around Brandon's speeches:

1. **Loading screen**: Brandon's picture, *ECHOES IN THE DARK*, and a glowing progress bar.
2. **The cinema**: you spawn in a starry plaza facing a giant screen playing **Video 1**
   (Brandon's calming "before you sleep" breathing talk). There are seats, and a glowing
   console that restarts the video.
3. **The Climb**: a 15-stage obstacle course that gets harder as you go (jumps, red kill
   lines, a jump pad, a truss climb, moving platforms, spinning bars, fading platforms,
   a tightrope). Your checkpoint is saved at every stage. A **giant billboard playing
   Video 2** ("you were made to move") stands at the end of the course, so you can see
   it the whole way up. Brandon's voice gets louder as you get closer.
4. **Finish**: "You made it. Keep going — Echoes in the Dark", confetti, sparkles, and a
   pad that takes you back to the cinema.
5. **Music**: a calm ambient pad plays in the background, with a **MUSIC: ON/OFF** button
   in the bottom-left corner. It gets quieter near a playing video so Brandon is easy to hear.

## What's in this folder

| File | What it is |
|---|---|
| `EchoesInTheDark.rbxlx` | The Roblox place. Open it in Roblox Studio. |
| `src/` | Every script as a readable `.lua` file, in the same folders as in Studio. The place already has these scripts inside; the copies are here so they're easy to read on GitHub. |
| `upload/loading_screen.png` | Loading screen image (1920×1080, with Brandon's profile photo). |
| `upload/loading_screen_no_photo.png` | Same design with a glowing "B" emblem instead of the photo (safer; see the risks section). |
| `upload/video1.mp4` | Cinema video: 1:34, 576×1024 (vertical), H.264 + AAC, 9.9 MB. |
| `upload/video2.mp4` | Billboard video: 1:00, 576×1024 (vertical), H.264 + AAC, 11 MB. |
| `upload/music_calm_pad.ogg` | Background music: 5:20, 48 kHz stereo OGG, 2.4 MB. |

Everything works before you upload anything. The screens say "Brandon's video is coming
soon", the loading screen shows a plain version, and there's no music until you add the IDs.

---

## Step by step

### 1. Open the place
1. Open **Roblox Studio**, click **File → Open from File…** and choose `EchoesInTheDark.rbxlx`.
2. Click **File → Publish to Roblox As…** and make a **new experience**. It stays
   **private** (only you can play it) until you decide to make it public.

### 2. Upload the files
Upload in Studio with the **Asset Manager** (**Window** menu or **Home** tab → Asset
Manager → **Import**), or on the web in the
[Creator Dashboard](https://create.roblox.com/dashboard/creations). When an upload is done,
right-click it in the Asset Manager → **Copy Asset ID**. Each file is checked by Roblox
moderation first, which usually takes a few hours.

| File | Asset type | Cost | Roblox's rules | This file |
|---|---|---|---|---|
| `loading_screen.png` (or `_no_photo`) | Image | Free | .png/.jpg/.gif/.tga/.bmp. Big images may be shrunk (fine, the text is large). | 1920×1080 PNG |
| `music_calm_pad.ogg` | Audio | Free (ID-verified: 2,000 per 30 days; not verified: 100 per 30 days) | .mp3/.ogg/.wav/.flac, under 20 MB, under 7 minutes, up to 48 kHz | 5:20, 2.4 MB, 48 kHz |
| `video1.mp4`, `video2.mp4` | Video | **2,000 Robux each** (4,000 for both) | You must be **13+ and ID verified**. .mp4/.mov, 5 minutes or less, up to 4096×2160, under 3.75 GB, at most 20 uploads a day | 1:34 and 1:00, 576×1024 |

**Uploading videos in Studio:** first turn on **File → Beta Features → Video Uploads**, then
use the Asset Manager. You can also upload videos on the web:
[Creator Dashboard → Creations → Video](https://create.roblox.com/dashboard/creations?activeTab=Video).
If Roblox rejects a video, **you don't get the Robux back**. Read the risks section before
you pay.

Tip: use the **Asset Manager** for the image. Its ID works directly. A "Decal" uploaded on
the website has a different ID that won't work in the script.

### 3. Paste the IDs into Config (the only place you edit)
In Studio's Explorer, open **ReplicatedStorage → Config** and replace the zeros:

```lua
LoadingImageId = 0, -- Image : upload/loading_screen.png
Video1Id = 0,       -- Video : upload/video1.mp4  (cinema)
Video2Id = 0,       -- Video : upload/video2.mp4  (billboard)
MusicId = 0,        -- Audio : upload/music_calm_pad.ogg
```

All the text in the game (titles, finish message, tagline) is in the same file.

### 4. Test
Click **Play** (Home tab) and check:
- The loading screen shows your image, then fades out after about 4 seconds.
- The cinema screen plays Video 1. Walk to the glowing console in front of it and press
  **E** (or tap on phones) to restart it.
- Go right through the arch into **The Climb**. The stage counter at the top goes up as
  you touch each checkpoint. Fall off and you come back at your last checkpoint.
- The billboard at the end plays Video 2, and the finish shows the celebration.
- The **MUSIC** button turns music off and on.

A brand-new upload can take a while to work. Until then the screen keeps saying "coming soon".

### 5. Publish
Click **File → Publish to Roblox**. To let other people play, open the game in the
Creator Dashboard, finish the **Maturity & Compliance questionnaire**, and set the audience.
Current rules:
- For a **16+** audience: an account at least 2 days old, an age check (face scan or ID), and the questionnaire.
- For **all ages**: also 2-step verification, and either 2 months of Roblox Premium/Plus or a
  refundable 1,000 Robux publishing fee. The game must also pass Roblox's review for young players.

---

## ⚠️ Things that could get the game (or your account) moderated

1. **No TikTok handle, link or logo inside the game.** Roblox's Community Standards only
   allow links through the *Social Links* feature on the game page. Social links need a
   16+ age check, only 16+ age-checked players can see them, and **TikTok isn't one of the
   allowed link types** (Facebook, Twitter/X, YouTube, Twitch, Discord, Guilded, Roblox
   community). "Any other efforts to direct users off of Roblox" aren't allowed. So the
   game is built to follow the rules by default:
   - The loading image has **no** handle, no TikTok logo and no "TikTok" text.
   - Your handle only exists as a hidden label that appears **only if** Roblox's
     `PolicyService` lists "TikTok" for that player. Roblox now documents that list
     (`AllowedExternalLinkReferences`) as a *legacy field that always returns an empty
     array*, so **the handle never shows**. Everyone sees "Brandon · Echoes in the Dark".
   - Please don't type your @ on signs, in chat messages, or in the game description.
2. **Your face and voice.** Roblox lists "visual and audio media of themselves" and "full
   legal names" among the personal information users *may be prohibited from sharing,
   depending on their age*. The original video-upload rules also said videos "cannot
   contain any personally identifiable information". The videos and the photo on the
   loading screen show you, so moderation **could** reject them, and a rejected video
   still costs 2,000 Robux. What was done to lower the risk:
   - Both videos were **trimmed to cut "Hey guys, Brandon Molina here"** (your full name).
   - There's a **no-photo loading screen** (`loading_screen_no_photo.png`) you can use instead.
   - Video 2 was filmed outdoors on a street. Nothing like a house number shows, but it's worth knowing.
   If you're under 18, talk to a parent or guardian before paying for video uploads.
3. **Autoplay rule.** Roblox's `PolicyService` has `IsEndlessContentAutoplayAllowed` for
   video or audio that "automatically and endlessly plays". The game checks it for every
   player. Where it isn't allowed (or the check fails), videos wait for the player to
   press **Play** on a console and play once, and music starts **off** until they press
   the MUSIC button. In Studio tests, videos always autoplay (`AlwaysAutoplayInStudio`).
4. **Only upload what you own.** The videos use your own original sound. The music and
   star background were made by computer for this project, so no one else's music is in it.
   The launch rules for video also required English or Spanish audio, and both videos are in English.

---

## The two videos (and why)
- **Video 1 (cinema):** your most-viewed original-sound video (about 15,300 views), the
  "before you sleep" breathing technique. It's calm and insightful, which is perfect for a
  cinema. The original is very dark, so it was brightened (noise cleaned up and shadows
  lifted). Used 0:02 to 1:36, from "So I thought it would be a great idea…" to
  "…just drink it up."
- **Video 2 (obstacle course):** your most-viewed motivational speech of 45 s or longer
  after that one (884 views). "You were never made to look at dirt, you were made to move…
  one better thought is one step higher", which is great for a climb. Filmed in daylight,
  so it's easy to see on a far-away billboard. Used 0:03 to 1:03, ending on "I'm strong
  and I can do it."
- Both have gentle fades and even loudness, and they're vertical 9:16. The screens in the
  game are 9:16 too, so nothing is stretched.

## How it works (for changing things)
- **Obstacles work by name.** Copy/paste parts named `KillBrick`, `MovingPlatform`,
  `Spinner`, `FadingPlatform` or `JumpPad` anywhere inside `Workspace.Obby` and they work.
  Settings are the small Value objects inside each part (for example `Speed` on a spinner,
  or `Offset`/`Period` on a moving platform).
- **Checkpoints:** a part named `Checkpoint` with an `IntValue` called `Stage`. The finish
  is stage 16 (`Workspace.Finish.FinishPad`). Progress is saved on the server for the
  whole visit.
- **Scripts:**
  - `ReplicatedFirst.LoadingScreen`: the loading screen.
  - `StarterPlayerScripts.ScreensClient`: the two videos.
  - `StarterPlayerScripts.MusicClient`: music and the button.
  - `StarterPlayerScripts.HUD`: stage counter and celebration.
  - `StarterPlayerScripts.JumpPads`: jump pads.
  - `ServerScriptService.Checkpoints`, `.ObbyMechanics` and `.VideoPrompts`: the server side.
  - `ReplicatedStorage.PlayerPolicy`: the PolicyService checks.
- **Music loop:** the file plays a 64-second fade-in once, then loops a seamless section
  (64 s → 256 s) forever, using `Sound.LoopRegion`. If you use a different song, set
  `MusicLoopStart` and `MusicLoopEnd` to 0 in Config.
- Only two videos can play at the same time on Roblox, and this game uses exactly two.

## Verified facts (checked 28 Sep 2026)
| Fact | Source |
|---|---|
| Video upload: 13+ ID verified; .mp4/.mov; ≤ 5 min; ≤ 4096×2160; < 3.75 GB; 2,000 Robux per upload; max 20/day; the "Video Uploads" beta must be on to upload in Studio; max 2 videos playing at once; VideoFrame goes in a ScreenGui/SurfaceGui/BillboardGui | [Creator Docs: Video frames](https://create.roblox.com/docs/ui/video-frames) |
| VideoFrame in a SurfaceGui on a part plays 3D sound from the part; `Looped`, `Playing`, `Volume` (0–100), `RollOffMode/Min/MaxDistance` | [VideoFrame reference](https://create.roblox.com/docs/reference/engine/classes/VideoFrame) |
| Limits grew from 30 s to 60 s (Mar 2025), then to 5 min (Jul 2025) | [DevForum: Longer video uploads](https://devforum.roblox.com/t/longer-video-uploads-more-video-uploads/3532432) |
| Launch rules: no personally identifiable information, English/Spanish audio, fee not refunded if rejected for copyright | [DevForum: Video uploads beta](https://devforum.roblox.com/t/video-uploads-beta-add-short-form-video-to-your-experience/2630621) |
| Audio: .mp3/.ogg/.wav/.flac, < 20 MB, < 7 min, ≤ 48 kHz; free; 2,000 per 30 days (ID verified) / 100 (unverified) | [Creator Docs: Audio assets](https://create.roblox.com/docs/audio/assets) |
| Images: .png/.jpg/.gif/.tga/.bmp | [Creator Docs: Importer](https://create.roblox.com/docs/studio/importer) |
| Off-platform links only through Social Links on game/group/user pages, 16+ age check; other efforts to direct users off Roblox prohibited; "handles not linked to Roblox" and "visual and audio media of themselves" are personal info that may be restricted by age | [Roblox Community Standards](https://about.roblox.com/community-standards) |
| Social link types: Facebook, Twitter, YouTube, Twitch, Discord, Guilded, Roblox community (no TikTok); "You cannot share social media links directly within a game" | [Creator Docs: Social media links](https://create.roblox.com/docs/production/promotion/social-media-links) |
| `AllowedExternalLinkReferences` is "a legacy field. It always returns an empty array"; `IsEndlessContentAutoplayAllowed` covers autoplaying, endlessly playing video/audio | [PolicyService reference](https://create.roblox.com/docs/reference/engine/classes/PolicyService) |
| Your own assets always work in your own games | [Creator Docs: Asset privacy](https://create.roblox.com/docs/projects/assets/privacy) |
| Public/all-ages publishing requirements | [Creator Docs: Publish games](https://create.roblox.com/docs/production/publishing/publish-games-and-places) |

## Credits
- Videos: Brandon (his own TikTok speeches with his own original sound).
- Music, star background and all 3D building: made for Echoes in the Dark by computer. They're royalty-free, and you own them.
- Fonts in the loading image: Cinzel Decorative, Archivo Black and Anton (SIL Open Font License).
