# Echoes in the Dark — TikTok site

A one-page, fully animated website that shows every TikTok video sorted into categories,
each with its own name, plus the profile picture, studio logo, follower stats and a built-in
player (videos play in a popup without leaving the site).

No build step. No framework. Open `index.html` and it works.

## Set it up in 3 steps

1. **Profile picture** — save your TikTok profile picture as `assets/profile.jpg`.
2. **Logo** — save the Echoes in the Dark logo as `assets/logo.png` (an animated built-in mark is used until then).
3. **Videos** — open `videos.js` and:
   - put your TikTok username in `profile.handle` (without the @),
   - update `followers` / `likes`,
   - paste every video link (TikTok ➜ Share ➜ Copy link) into the `videos` list with a `title` and a `category`,
   - delete the entries marked `demo: true`.

The site fetches each video's real cover image from TikTok automatically and plays it in a popup when clicked.

## Categories

Edit the `categories` list in `videos.js`. Each one has an `id`, `name`, `emoji`, `color` and `blurb`.
Videos point at a category by its `id`. A video with an unknown id lands in an "Other" section so nothing goes missing.

## Features

- Intro splash with the studio logo
- Animated starfield with shooting stars, drifting nebulas and a cursor glow
- Profile hero with spinning gradient ring, orbiting satellite, 3D tilt and animated follower counters
- Category cards, sticky category nav, filter chips, live search and sorting (newest / oldest / A-Z)
- 9:16 video cards with cover images, hover play button, pinned badge, staggered reveal on scroll
- Popup player with prev / next and keyboard arrows, Escape to close
- Fully responsive (phone, tablet, desktop), reduced-motion friendly

## Put it online (free)

Push this folder to GitHub, open the repo **Settings ➜ Pages**, pick the branch and the `/tiktok-site` folder.
You get a public link in about a minute. Or drag the folder onto https://app.netlify.com/drop.
