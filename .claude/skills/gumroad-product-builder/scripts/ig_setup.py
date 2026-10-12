#!/usr/bin/env python3
"""One-shot Instagram setup checker.

Give it ONLY an access token (via the IG_ACCESS_TOKEN env var). It will:
  1. confirm the token works and list its permissions
  2. find the Facebook Page(s) the token can see
  3. find the Instagram Business/Creator account linked to each Page  -> that is IG_USER_ID
  4. check the publishing permission is present
  5. print the exact two secrets to store in the cloud environment

Usage:
    export IG_ACCESS_TOKEN=EAAB...
    python ig_setup.py

Exit 0 = ready to post. Anything else = the printed message says what is still missing.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
NEEDED = {"instagram_basic", "instagram_content_publish", "pages_show_list", "pages_read_engagement"}


def get(path: str, **params) -> dict:
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body
        raise SystemExit(f"Meta API error {e.code}: {msg}")


def main() -> int:
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        print("Set IG_ACCESS_TOKEN first (see INSTAGRAM-SETUP.md).", file=sys.stderr)
        return 2

    me = get("me", fields="id,name", access_token=token)
    print(f"Token OK. Facebook user: {me.get('name')} ({me.get('id')})")

    perms = get("me/permissions", access_token=token).get("data", [])
    granted = {p["permission"] for p in perms if p.get("status") == "granted"}
    missing = NEEDED - granted
    print(f"Granted permissions: {', '.join(sorted(granted)) or 'none'}")
    if missing:
        print(f"MISSING permissions: {', '.join(sorted(missing))}")
        print("Regenerate the token in Graph API Explorer with those permissions ticked.")
        return 3

    pages = get("me/accounts", fields="id,name", access_token=token).get("data", [])
    if not pages:
        print("No Facebook Pages visible to this token. Link @jacksonsworld16 to a Page first.")
        return 4

    found = []
    for page in pages:
        info = get(page["id"], fields="instagram_business_account{id,username}", access_token=token)
        ig = info.get("instagram_business_account")
        if ig:
            found.append((page["name"], ig["id"], ig.get("username")))

    if not found:
        print("Pages found, but none has an Instagram Business/Creator account linked:")
        for page in pages:
            print(f"  - {page['name']} ({page['id']})")
        print("Instagram app -> Settings -> Business tools and controls -> Connect a Facebook Page.")
        return 5

    print("\nLinked Instagram accounts:")
    for page_name, ig_id, username in found:
        print(f"  Page '{page_name}'  ->  @{username}  IG_USER_ID={ig_id}")

    target = next((f for f in found if (f[2] or "").lower() == "jacksonsworld16"), found[0])
    print("\nREADY. Store these two secrets in the cloud environment (never in git):")
    print(f"  IG_USER_ID={target[1]}")
    print("  IG_ACCESS_TOKEN=<the token you just used>")
    print("\nThen post with:")
    print("  python post_to_instagram.py --image-url https://... --caption-file captions.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
