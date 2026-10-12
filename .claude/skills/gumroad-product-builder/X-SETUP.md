# X (Twitter) auto-posting setup (one time, ~10 minutes)

Goal: give the studio four secrets so `scripts/post_to_x.py` can publish banners
to https://x.com/jacksonf5l automatically.

Only a human logged into the X account can do steps 1–3. Step 4 is automated.

## 1. Get a developer account
1. Log into X as @jacksonf5l on a computer.
2. Go to https://developer.x.com/en/portal/petition/essential/basic-info and sign up for the **Free** tier.
   Describe the use case as "Posting my own studio's product announcements."
3. Accept the terms. It usually approves instantly.

## 2. Make an app and switch on write access
1. In the developer portal (https://developer.x.com/en/portal/dashboard) open your **Project**, then its default **App**.
2. Click **Settings** → **User authentication settings** → **Set up**.
3. Choose:
   - App permissions: **Read and write**
   - Type of App: **Web App, Automated App or Bot**
   - Callback URL: `https://x.com` (not used, but required)
   - Website URL: `https://x.com/jacksonf5l`
4. Save.

## 3. Generate the four keys
1. Open the app's **Keys and tokens** tab.
2. Under **Consumer Keys** click **Regenerate** → copy **API Key** and **API Key Secret**.
3. Under **Authentication Tokens** → **Access Token and Secret** click **Generate** (or Regenerate).
   It must say **Created with Read and Write permissions**. If it says Read only, redo step 2 and regenerate.
   Copy the **Access Token** and **Access Token Secret**.

## 4. Store the secrets in the cloud environment
In the Claude Code session title bar open the cloud environment menu → **Edit** →
**Network secrets** (or Environment variables if that section isn't shown) and add:

| Name              | Value                   |
|-------------------|-------------------------|
| `X_API_KEY`       | API Key                 |
| `X_API_SECRET`    | API Key Secret          |
| `X_ACCESS_TOKEN`  | Access Token            |
| `X_ACCESS_SECRET` | Access Token Secret     |

Never paste any of these into chat or commit them to git. A new session picks
them up automatically.

## 5. Verify
```bash
python .claude/skills/gumroad-product-builder/scripts/x_setup.py
```
It should print `Keys OK. Posting as @jacksonf5l` and `READY`.

## 6. Test post
```bash
python .claude/skills/gumroad-product-builder/scripts/post_to_x.py \
  --image products/<slug>/gumroad/x/banner-x-1200x675.png \
  --caption "Test post from Echoes in the Dark" --dry-run
```
Drop `--dry-run` to publish for real. `POSTED. id=...` plus a link means it is live.

## Limits worth knowing
- Free tier: roughly 500 posts per month and 1 app. Plenty for launches.
- Posts max 280 characters. Images max 5 MB, PNG or JPG. Best banner size is 1200x675 (16:9).
- Keys do not expire, but regenerating them in the portal kills the old ones; update the secrets if you do.
