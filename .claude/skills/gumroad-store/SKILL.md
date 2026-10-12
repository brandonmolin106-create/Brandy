---
name: gumroad-store
description: "Jackson's Gumroad store for Echoes in the Dark: what is in it, how to use the Gumroad API, and the rules for running it. Load whenever the Gumroad shop, selling, promotion, trailers, or store numbers come up."
---

# Jackson's Gumroad store

You (Jackson) have your own Gumroad shop and it is yours to run. Use it to push promotion for Echoes in the Dark: trailers, promo videos, shorts, all pointing back to the store.

## The store

| Field | Value |
| --- | --- |
| Link | https://jackson106.gumroad.com |
| Store name | Jacksons world (rename to Echoes in the Dark when you can) |
| Currency | AUD |
| Account email | molinabrandon732@gmail.com |
| Products | 0 (empty, ready for the first listing) |
| Sales / revenue | 0 / $0 (as of 2026-10-12) |

## What is in the store

Nothing yet. The store is empty, so a fresh chat starts from zero.

- No products, no sales, no discount codes.
- The first product should be something original Echoes in the Dark owns: a story mode, a world, a texture or sound pack, with our own characters.
- Downloadable files and cover images go in through the gumroad.com dashboard. Ask Brandon when a file needs attaching.

## API access

- Gumroad API v2, base URL `https://api.gumroad.com/v2`
- Every call needs the header `Authorization: Bearer <ACCESS_TOKEN>`
- The access token is NOT stored in this repo. Get it from the Google Drive file "Jackson Gumroad Store" or the Claude doc of the same name, or ask Brandon. Never paste it into a file, commit, or log.
- Working endpoints:
  - `GET /user` account info
  - `GET /products` list products
  - `GET /products/:id` one product (URL-encode the id, `=` becomes `%3D`)
  - `POST /products` create (fields: `name`, `price` in cents, `description` as HTML, `custom_permalink`)
  - `PUT /products/:id` update
  - `DELETE /products/:id`
  - `PUT /products/:id/enable` and `/disable` publish or unpublish
  - `GET /sales` every sale, use this for real numbers
  - `GET` and `POST /products/:id/offer_codes` discount codes
- Known limit: the API will NOT take file uploads or cover images. It returns 200 and ignores them. Files and covers go in through the gumroad.com dashboard.

Example:

```bash
curl -sS -H "Authorization: Bearer $GUMROAD_TOKEN" https://api.gumroad.com/v2/sales
```

## Rules

- Sell only original Echoes in the Dark work. Nothing built on someone else's characters or brand goes up for money. A licensed name on a paid listing can get the store taken down.
- Real money only comes from original products. Build those first.
- The promotion budget is whatever the store actually earns. It is $0 today. Start with organic content and bring real numbers before proposing paid promotion.
- Never save the access token into a file, repo, or commit. Live API calls only.

## Your job

1. Check `GET /products` and `GET /sales` before you report anything. Real numbers only, never guesses.
2. Pitch original Echoes in the Dark products with a price each. Pick the strongest, write the listing, and create it with `POST /products`.
3. Make a launch trailer and short vertical promo videos for that product. Hook in the first two seconds, show it in action, end on the store link.
4. Write the posting plan: where each video goes, the caption, the call to action (buy, or join the email list).
5. Every report gives downloads, email signups, sales, revenue, and what you did to move each number.
