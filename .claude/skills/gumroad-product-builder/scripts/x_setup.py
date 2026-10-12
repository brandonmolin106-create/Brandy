#!/usr/bin/env python3
"""One-shot X (Twitter) setup checker.

Reads X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET from the environment and:
  1. confirms the four keys are present
  2. calls /2/users/me to prove they sign correctly
  3. prints which account they post as (should be @jacksonf5l)

Usage:
    python x_setup.py

Exit 0 = ready to post. Anything else = the printed message says what is missing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xapi  # noqa: E402


def main() -> int:
    missing = [k for k in xapi.NEEDED if not os.environ.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}  (see X-SETUP.md)", file=sys.stderr)
        return 2

    c = xapi.creds()
    me = xapi.get("/2/users/me", c)
    data = me.get("data") or {}
    username = data.get("username")
    if not username:
        print(f"Keys accepted but no user returned: {me}")
        return 3

    print(f"Keys OK. Posting as @{username} (id {data.get('id')}, name '{data.get('name')}')")
    if username.lower() != "jacksonf5l":
        print("WARNING: this is not @jacksonf5l. Regenerate the Access Token while logged in as that account.")
        return 4

    print("\nREADY. Post with:")
    print("  python post_to_x.py --image banner-x-1200x675.png --caption-file captions.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
