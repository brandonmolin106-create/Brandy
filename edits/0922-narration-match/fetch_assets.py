"""Download the narration WAVs and clips into work/.

The download links for the Higgsfield generations are private to the
account, so they are not in this repo. Put them in `assets.local.tsv`
(git-ignored) as `<generation id><TAB><url>` lines -- copy them from the
Higgsfield library, or ask Claude to pull them with the Higgsfield connector.
"""
import subprocess
from pathlib import Path

import edl

ROOT = Path(__file__).resolve().parent


def main():
    urls = dict(l.rstrip("\n").split("\t", 1) for l in open(ROOT / "assets.local.tsv") if "\t" in l)
    jobs = [(gid, ROOT / "work/narr" / f"part{p}.wav") for p, gid in edl.NARRATION_PARTS.items()]
    jobs += [(gid, ROOT / "work/clips" / f"{gid}.mp4") for gid in edl.CLIPS.values()]
    missing = [gid for gid, _ in jobs if gid not in urls]
    if missing:
        raise SystemExit(f"no URL in assets.local.tsv for: {', '.join(missing)}")
    for gid, dest in jobs:
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sSfL", "-o", str(dest), urls[gid]], check=True)
        print("got", dest.relative_to(ROOT))


if __name__ == "__main__":
    main()
