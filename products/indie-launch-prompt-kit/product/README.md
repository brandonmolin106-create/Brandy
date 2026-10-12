# Indie Launch Prompt Kit

106 prompts and 5 templates for launching a game, app, tool, asset pack or any digital product. Written for Claude and ChatGPT; they work in any capable model.

## How to use it (2 minutes)

1. Open `templates/00-product-brief.md`, fill in the eight fields once. That brief is the only thing you paste before any prompt.
2. Open the module you need in `prompts/`. Each prompt is a complete instruction with a role, inputs, constraints and the exact output shape. Paste your brief, then the prompt.
3. Variables look like `{{PRODUCT}}`. Replace them, or just paste the brief above the prompt and say "use the brief."
4. `prompts.json` holds every prompt as data, for Notion imports, Raycast/Alfred snippets or your own tooling.

## Modules

| # | File | Prompts | What it gets you |
|---|---|---|---|
| 01 | positioning | 12 | one-liner, audience, hook, naming, differentiation |
| 02 | store-page | 12 | Steam / itch / Gumroad / App Store page copy that converts |
| 03 | trailer-screenshots | 10 | 30-second trailer script, shot list, screenshot captions, thumbnail text |
| 04 | devlog-content | 12 | devlog posts, build-in-public updates, newsletter issues |
| 05 | x-twitter | 12 | launch thread, teaser cadence, reply hooks, pinned post |
| 06 | reddit-communities | 10 | subreddit-safe posts, Discord drops, Show HN |
| 07 | press-creators | 10 | press email, creator pitch, press kit page, key distribution |
| 08 | pricing-offers | 8 | price ladder, launch discount, bundle logic, regional pricing |
| 09 | launch-week | 10 | day-by-day plan, launch-day post set, FAQ, support replies |
| 10 | post-launch | 10 | review asks, update notes, sale timing, what-went-wrong retro |

## Templates
- `00-product-brief.md` — the one-page brief every prompt reads from
- `store-page-template.md` — fill-in store page with the proven section order
- `press-email-template.md` — two emails (announce, key offer) with subject lines
- `launch-week-calendar.md` — 7-day calendar with slots for every channel
- `pricing-worksheet.md` — price ladder, discount maths, break-even
- `launch-checklist.md` — 42 checks, in order, from "page live" to "day 7 retro"

## Licence
Use the prompts and their outputs for any number of your own launches, personal or commercial. Don't resell or redistribute the kit itself. Full text in `LICENSE.txt`.

Made by Jacksons world · https://jackson106.gumroad.com · @jacksonf5l on X
