# Instagram auto-posting setup (one time, ~20 minutes)

Goal: give the studio two secrets, `IG_USER_ID` and `IG_ACCESS_TOKEN`, so
`scripts/post_to_instagram.py` can publish banners to
https://www.instagram.com/jacksonsworld16/ automatically.

Only a human logged into the accounts can do steps 1–3. Step 4 is automated.

## 1. Make @jacksonsworld16 a Creator (or Business) account and link a Facebook Page
1. Instagram app → profile → menu (≡) → **Settings and privacy** → **Account type and tools** → **Switch to professional account** → pick **Creator**.
2. Still in Settings → **Business tools and controls** → **Connect a Facebook Page**. If you don't have a Page, tap **Create a new Facebook Page** right there (name it "Echoes in the Dark").

## 2. Make a Meta app
1. Go to https://developers.facebook.com/apps → **Create App**.
2. Use case: **Other** → type **Business** → name it "Echoes in the Dark Poster".
3. In the app dashboard click **Add product** → **Instagram** → **Set up** (this is the "Instagram Graph API").
4. App Settings → Basic → leave it in **Development mode**. That is fine: it can post to accounts that are admins/testers of the app, which includes yours.

## 3. Generate a long-lived token
1. Open https://developers.facebook.com/tools/explorer/ and pick your app at the top right.
2. Click **Generate Access Token**. In the permissions box tick:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
3. Log in, approve, make sure the Page from step 1 is selected.
4. Copy the token. It only lasts ~1 hour, so extend it: open https://developers.facebook.com/tools/debug/accesstoken/ , paste it, click **Debug**, then **Extend Access Token**. Copy the **long-lived** one (lasts 60 days; refresh the same way before it expires).

## 4. Let the script find the rest
On any machine with Python 3:

```bash
export IG_ACCESS_TOKEN=<paste long-lived token>
python .claude/skills/gumroad-product-builder/scripts/ig_setup.py
```

It verifies the token, checks the permissions, finds the Page, finds the linked
Instagram account, and prints the `IG_USER_ID`. If something is missing it says
exactly which step above to redo.

## 5. Store the secrets in the cloud environment
In the Claude Code session title bar open the cloud environment menu → **Edit** →
**Network secrets** (or Environment variables if that section isn't shown) and add:

- `IG_USER_ID` = the id printed by the script
- `IG_ACCESS_TOKEN` = the long-lived token

Never paste the token into chat or commit it to git. A new session picks the
secrets up automatically and the product-builder skill will post on every launch.

## 6. Test
```bash
python .claude/skills/gumroad-product-builder/scripts/post_to_instagram.py \
  --image-url https://raw.githubusercontent.com/brandonmolin106-create/Brandy/<branch>/products/<slug>/gumroad/instagram/banner-feed-1080x1080.png \
  --caption "Test post from Echoes in the Dark" --dry-run
```
Drop `--dry-run` to publish for real. "POSTED. media_id=..." means it is live.

## Token expiry
Long-lived tokens die after 60 days. Repeat step 3.4 (Debug → Extend) and update
the secret. The poster script prints a clear Meta error if the token is dead.
