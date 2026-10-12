#!/usr/bin/env python3
"""Publish a product ad/banner to Instagram via the Instagram Graph API.

Target account: https://www.instagram.com/jacksonsworld16/

Requirements (one-time setup, done by a human):
  1. Switch @jacksonsworld16 to a Business or Creator account and link it to a Facebook Page.
  2. Create a Meta app (developers.facebook.com), add "Instagram Graph API", and generate a
     long-lived user access token with permissions:
       instagram_basic, instagram_content_publish, pages_read_engagement, pages_show_list
  3. Find the Instagram Business account id (IG_USER_ID) via:
       GET https://graph.facebook.com/v21.0/me/accounts?access_token=...   -> page id
       GET https://graph.facebook.com/v21.0/<page-id>?fields=instagram_business_account&access_token=...
  4. Export:
       export IG_USER_ID=1784...
       export IG_ACCESS_TOKEN=EAAB...

The image must be reachable by a public HTTPS URL (Instagram fetches it). Upload the banner to
your GitHub repo (raw URL), Gumroad, Imgur, S3, etc. and pass that URL.

Usage:
    python post_to_instagram.py --image-url https://example.com/banner.png --caption-file captions.md
    python post_to_instagram.py --image-url https://example.com/banner.png --caption "text..."
    python post_to_instagram.py ... --dry-run     # validate inputs, do not publish

Exit code 0 and a printed media id means the post is LIVE. Anything else means it did not post.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


def api(method: str, path: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        url = f"{url}?{data.decode()}"
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"Instagram API error {e.code}: {body}")


def first_caption(path: str) -> str:
    """Take the first caption block from captions.md (blocks separated by a '---' line)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = [b.strip() for b in text.split("\n---\n") if b.strip()]
    if not blocks:
        raise SystemExit(f"No caption found in {path}")
    # Drop a leading markdown heading if present
    lines = blocks[0].splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-url", required=True, help="Public HTTPS URL of the banner PNG/JPG")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--caption")
    g.add_argument("--caption-file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    caption = args.caption if args.caption else first_caption(args.caption_file)
    if len(caption) > 2200:
        raise SystemExit(f"Caption is {len(caption)} chars; Instagram max is 2200.")
    if not args.image_url.startswith("https://"):
        raise SystemExit("--image-url must be a public https:// URL")

    user_id = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not user_id or not token:
        print("NOT POSTED: set IG_USER_ID and IG_ACCESS_TOKEN (see header of this script).", file=sys.stderr)
        print("Caption ready to paste manually:\n")
        print(caption)
        return 2

    if args.dry_run:
        print("DRY RUN ok. Would publish:")
        print(f"  image:   {args.image_url}")
        print(f"  caption: {caption[:120]}{'...' if len(caption) > 120 else ''}")
        return 0

    # 1) create media container
    container = api("POST", f"{user_id}/media", {
        "image_url": args.image_url,
        "caption": caption,
        "access_token": token,
    })
    creation_id = container.get("id")
    if not creation_id:
        raise SystemExit(f"No container id returned: {container}")

    # 2) wait until container is FINISHED
    for _ in range(30):
        status = api("GET", creation_id, {"fields": "status_code", "access_token": token})
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise SystemExit(f"Container failed: {status}")
        time.sleep(2)
    else:
        raise SystemExit("Timed out waiting for Instagram to process the image.")

    # 3) publish
    published = api("POST", f"{user_id}/media_publish", {
        "creation_id": creation_id,
        "access_token": token,
    })
    media_id = published.get("id")
    if not media_id:
        raise SystemExit(f"Publish returned no media id: {published}")

    print(f"POSTED. media_id={media_id}")
    print(f"https://www.instagram.com/jacksonsworld16/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
