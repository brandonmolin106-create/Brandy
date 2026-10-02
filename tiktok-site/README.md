# Brandon Molina — TikTok site

Every video from [@brandonmolina651](https://www.tiktok.com/@brandonmolina651) on one animated page,
sorted into categories, each with its own name, playing straight from the site with **no TikTok watermark**.

No build step, no framework. Open `index.html` and it works. Push it to GitHub Pages and it's live.

## What's in here

| Path | What it is |
|---|---|
| `index.html` | the page |
| `styles.css` | the look and every animation |
| `app.js` | renders the site from `videos.js`, the custom player, particles, cursor, previews |
| `videos.js` | **all the data**: profile, categories and one line per video |
| `videos/<id>.mp4` | the video files, original uploads re-encoded to 480p, no watermark |
| `covers/<id>.jpg` | the cover image for every video |
| `assets/profile.jpg` | profile picture |

## Categories

| id | name | what goes in it |
|---|---|---|
| `motivation` | 💪 Real Talk | pep talks to camera |
| `quotes` | ✍️ Words to Live By | videos with a line on screen |
| `reflect` | 🌙 Late Night Thoughts | slower talks over sad piano / slowed tracks |
| `faith` | ✝️ Faith & Worship | prayer, scripture, worship music |
| `fun` | 😂 Fun & Skits | filters, faces, bits |
| `songs` | 🎶 Songs & Vibes | lip syncs and song moments |
| `outside` | 🌿 Out & About | walks, backyard, bush, family |
| `community` | 💬 Replies & Duets | replies, duets, tag-a-mate posts |
| `holiday` | 🎄 Christmas & Events | Santa hat season, live streams |

Titles come from the on-screen text or caption where there is one, otherwise a generated name
like "Pep Talk #12 · Boundless Worship". Change any title or category by editing its line in `videos.js`.

## Adding a new TikTok

1. Download the video without watermark (for example `yt-dlp -f "b[format_id!=download]" <link>`).
2. Re-encode it small: `ffmpeg -i in.mp4 -vf scale=-2:854 -crf 32 -preset veryfast -c:a aac -b:a 48k -ac 1 videos/<id>.mp4`
3. Save its cover as `covers/<id>.jpg` (360 px wide is plenty).
4. Add one line to the `videos` list in `videos.js` with the id, title, category, date, seconds, views, likes and music.

## Features

- Intro splash, aurora background, particle field with shooting stars, custom cursor with trail
- Profile hero: spinning gradient ring, three orbiting satellites, floating emoji chips, 3D tilt, typewriter tagline, count-up stats, confetti on follow
- Scrolling category ticker, category cards with animated borders and mini cover stacks
- "Most watched" highlight row
- Sticky search / filter chips / sort bar, show-more pagination per category
- 9:16 cards: cover, duration, views, hover **video preview**, 3D tilt, staggered reveal
- Custom player: progress bar, buffer bar, mute, fullscreen, prev / next, auto-play next, keyboard (space, arrows, m, esc), share link (`#v=<id>` opens a video directly)
- Fully responsive, reduced-motion friendly

## Put it online (free)

GitHub repo **Settings ➜ Pages ➜ Deploy from branch ➜ pick the branch and `/tiktok-site`**.
