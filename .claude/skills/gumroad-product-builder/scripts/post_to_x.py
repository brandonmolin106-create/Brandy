#!/usr/bin/env python3
"""Post a product ad/banner to X (Twitter) as @jacksonf5l — https://x.com/jacksonf5l

Needs four env vars from the X developer portal (one-time setup, see X-SETUP.md):
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET

The image is uploaded straight from disk; no public URL needed.

Usage:
    python post_to_x.py --image banner-x-1200x675.png --caption-file captions.md
    python post_to_x.py --image banner.png --caption "text..."
    python post_to_x.py --caption "text only post"
    python post_to_x.py ... --dry-run        # validate everything, do not post

Exit 0 and a printed post URL means it is LIVE. Anything else means it did not post.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xapi  # noqa: E402

MAX_CHARS = 280


def first_caption(path: str) -> str:
    """Take the first caption block from captions.md (blocks separated by a '---' line)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = [b.strip() for b in text.split("\n---\n") if b.strip()]
    if not blocks:
        raise SystemExit(f"No caption found in {path}")
    lines = blocks[0].splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="Local PNG/JPG to attach (max 5 MB)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--caption")
    g.add_argument("--caption-file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    caption = args.caption if args.caption else first_caption(args.caption_file)
    if len(caption) > MAX_CHARS:
        raise SystemExit(f"Caption is {len(caption)} chars; X max is {MAX_CHARS}. Trim it.")
    if args.image and not os.path.isfile(args.image):
        raise SystemExit(f"Image not found: {args.image}")

    c = xapi.creds()
    if not c:
        print("NOT POSTED: set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET (see X-SETUP.md).",
              file=sys.stderr)
        print("Caption ready to paste manually at https://x.com/compose/post :\n")
        print(caption)
        if args.image:
            print(f"\nAttach: {os.path.abspath(args.image)}")
        return 2

    if args.dry_run:
        print("DRY RUN ok. Would post:")
        print(f"  image:   {args.image or '(none)'}")
        print(f"  caption: {caption[:120]}{'...' if len(caption) > 120 else ''}")
        return 0

    payload = {"text": caption}
    if args.image:
        media_id = xapi.upload_image(args.image, c)
        payload["media"] = {"media_ids": [media_id]}

    resp = xapi.post_json("/2/tweets", c, payload)
    post_id = (resp.get("data") or {}).get("id")
    if not post_id:
        raise SystemExit(f"Post returned no id: {resp}")

    print(f"POSTED. id={post_id}")
    print(f"https://x.com/jacksonf5l/status/{post_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
