#!/usr/bin/env python3
"""
Turns installer/mods.json (a list of Modrinth slugs) into installer/mods.lock.json: the exact
jar for each mod for Forge 1.20.1 (newest release, or newest beta when there is no release),
with download URL, size and sha1/sha512, plus every *required* dependency, resolved recursively.

The lock file is what build_installer.py and build_packs.py read, so the installer and the
.mrpack always agree on the exact files.

Run from the repo root:  python3 installer/resolve_mods.py
Pin a version by adding  "version": "5.7.4"  next to a slug in mods.json.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS_JSON = os.path.join(ROOT, "installer", "mods.json")
LOCK_JSON = os.path.join(ROOT, "installer", "mods.lock.json")
API = "https://api.modrinth.com/v2"
UA = "EchoesInTheDark-TMNT-Story-Mode/1.0 (github.com/brandonmolin106-create/Brandy)"


def get(path, **params):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode({k: json.dumps(v) if not isinstance(v, str) else v
                                              for k, v in params.items()})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def pick_version(versions, pinned=None):
    """Newest release; if none, newest beta; if none, newest alpha. Or the pinned version_number."""
    if pinned:
        for v in versions:
            if v["version_number"] == pinned:
                return v
        raise SystemExit(f"pinned version {pinned!r} not found")
    for kind in ("release", "beta", "alpha"):
        for v in versions:  # API returns newest first
            if v["version_type"] == kind:
                return v
    raise SystemExit("no versions at all")


def main():
    with open(MODS_JSON) as f:
        spec = json.load(f)
    mc, loader = spec["minecraft"], spec["loader"]
    wanted = {m["slug"]: m for m in spec["mods"]}
    queue = list(wanted)
    done = {}        # project_id -> lock entry
    slug_of = {}     # project_id -> slug

    while queue:
        key = queue.pop(0)  # slug or project id
        project = get(f"/project/{key}")
        pid = project["id"]
        if pid in done:
            continue
        slug_of[pid] = project["slug"]
        versions = get(f"/project/{project['slug']}/version", loaders=[loader], game_versions=[mc])
        if not versions:
            raise SystemExit(f"{project['slug']}: no {loader} {mc} versions")
        v = pick_version(versions, wanted.get(project["slug"], {}).get("version"))
        primary = next((f for f in v["files"] if f["primary"]), v["files"][0])
        entry = {
            "slug": project["slug"],
            "title": project["title"],
            "project_id": pid,
            "version_id": v["id"],
            "version": v["version_number"],
            "version_type": v["version_type"],
            "filename": primary["filename"],
            "url": primary["url"],
            "size": primary["size"],
            "sha1": primary["hashes"]["sha1"],
            "sha512": primary["hashes"]["sha512"],
            "client_side": project["client_side"],
            "server_side": project["server_side"],
            "requested": project["slug"] in wanted,
            "why": wanted.get(project["slug"], {}).get("why", "dependency"),
            "requires": [],
        }
        for d in v["dependencies"]:
            if d["dependency_type"] == "required" and d.get("project_id"):
                entry["requires"].append(d["project_id"])
                if d["project_id"] not in done:
                    queue.append(d["project_id"])
        done[pid] = entry
        print(f"{project['slug']:28} {v['version_number']:24} {v['version_type']:8} {primary['size'] / 1e6:8.1f} MB")

    for e in done.values():
        e["requires"] = [slug_of[p] for p in e["requires"]]
    order = {m["slug"]: i for i, m in enumerate(spec["mods"])}   # keep mods.json order, deps last
    mods = sorted(done.values(), key=lambda e: (not e["requested"], order.get(e["slug"], 0), e["slug"]))
    lock = {
        "minecraft": mc,
        "loader": loader,
        "total_bytes": sum(e["size"] for e in mods),
        "mods": mods,
    }
    with open(LOCK_JSON, "w") as f:
        json.dump(lock, f, indent=2)
        f.write("\n")
    print(f"\n{len(mods)} mods, {lock['total_bytes'] / 1e6:.0f} MB -> {os.path.relpath(LOCK_JSON, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
