#!/usr/bin/env python3
"""
Builds the one-click installers in download/:

  Play-TMNT-Story-Mode.bat  TMNT mod + "TMNT Story Mode" New York world + all 26 mods (Verity, voice chat...)
  Play-Verity.bat           just Verity (with its offline voice) + a fresh world called "verity"

Each .bat is three parts glued together:
  1. a few lines of batch that start PowerShell and run part 2
  2. installer/install.ps1 (between ##PS markers) with the pack's placeholders filled in and its mod
     list from installer/mods.lock.json glued in, so the installer downloads the right jars from
     Modrinth and checks their SHA-1s
  3. the world (+ our own mod jar, if the pack has one) as a base64 zip, after the ##PAYLOAD marker

Run from the repo root:  python3 installer/build_installer.py
(Run installer/resolve_mods.py first if you changed installer/mods.json.)
"""
import base64
import io
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD = os.path.join(ROOT, "download")
TMNT_JAR = os.path.join(DOWNLOAD, "turtlepower-1.0.0.jar")
LOGO = os.path.join(ROOT, "tmnt-story-mode", "src", "main", "resources", "turtlepower_logo.png")
PS1 = os.path.join(ROOT, "installer", "install.ps1")
LOCK = os.path.join(ROOT, "installer", "mods.lock.json")

PACKS = [
    {
        "out": "Play-TMNT-Story-Mode.bat",
        "title": "TMNT Turtle Power: Story Mode",
        "banner": "TMNT TURTLE POWER: STORY MODE  - installer",
        "world": "TMNT Story Mode",
        "world_zip": "TMNT-Story-Mode-World.zip",
        "jar": TMNT_JAR,
        "profile_id": "tmnt-story-mode",
        "profile_name": "TMNT Story Mode",
        "icon": "logo",                 # the TMNT logo as a data URI
        "mods": None,                   # every mod in the lock file
        "done": "ALL DONE! COWABUNGA!",
        "play": "Minecraft loads straight into the lair. You are Raphael!",
    },
    {
        "out": "Play-Verity.bat",
        "title": "Verity",
        "banner": "VERITY  - installer",
        "world": "verity",
        "world_zip": "verity-world.zip",
        "jar": None,
        "profile_id": "verity",
        "profile_name": "verity",
        "icon": "Glowstone",            # a built-in launcher icon (yellow, like him)
        "mods": ["verity-je-official", "yacl", "geckolib"],
        "done": "ALL DONE! Say hi to Verity.",
        "play": "Minecraft loads straight into the verity world. Verity shows up in his box after a bit.",
    },
]

HEADER = r"""@echo off
setlocal
title {title}
set "TMNT_SELF=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText($env:TMNT_SELF); $m='#'+'#PS'; $p=$t.Split(@($m),[StringSplitOptions]::None); Invoke-Expression $p[1]"
echo.
pause
exit /b
"""


def payload(pack):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if pack["jar"]:
            z.write(pack["jar"], "mods/" + os.path.basename(pack["jar"]))
        with zipfile.ZipFile(os.path.join(DOWNLOAD, pack["world_zip"])) as w:
            names = [i.filename for i in w.infolist() if not i.is_dir()]
            assert all(n.startswith(pack["world"] + "/") for n in names), names[:3]
            for n in names:
                z.writestr("saves/" + n, w.read(n))
    return buf.getvalue()


def mods_json(pack):
    """The lock file, trimmed to what the installer needs, as compact JSON (one mod per line)."""
    with open(LOCK) as f:
        mods = json.load(f)["mods"]
    if pack["mods"] is not None:
        by_slug = {m["slug"]: m for m in mods}
        mods = [by_slug[s] for s in pack["mods"]]
    keep = ("title", "filename", "url", "size", "sha1")
    rows = [json.dumps({k: m[k] for k in keep}) for m in mods]
    text = '{"mods": [\n' + ",\n".join(rows) + "\n]}"
    assert "'@" not in text and "##" not in text, "lock JSON would break the PowerShell here-string"
    return text


def icon(pack):
    if pack["icon"] == "logo":
        with open(LOGO, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return pack["icon"]


def build(pack, template):
    fill = {
        "__PACK_TITLE__": pack["title"],
        "__PLACEHOLDERS__": "placeholders",
        "__BANNER__": pack["banner"],
        "__WORLD_NAME__": pack["world"],
        "__PROFILE_ID__": pack["profile_id"],
        "__PROFILE_NAME__": pack["profile_name"],
        "__ICON__": icon(pack),
        "__DONE_LINE__": pack["done"],
        "__PLAY_LINE__": pack["play"],
        "__MODS__": mods_json(pack),
    }
    script = template
    for k, v in fill.items():
        assert k in script, k
        if k != "__MODS__":
            assert "'" not in v and '"' not in v, f"{k} would break a quoted string"
        script = script.replace(k, v)
    assert "__" not in script, "unfilled placeholder"
    assert "##PS" not in script and "##PAYLOAD" not in script
    data = base64.encodebytes(payload(pack)).decode()  # 76-char lines
    text = HEADER.format(title=pack["title"]) + "##PS\n" + script + "\n##PS\n##PAYLOAD\n" + data
    out = os.path.join(DOWNLOAD, pack["out"])
    with open(out, "w", newline="\r\n") as f:
        f.write(text)
    print(f"{out}: {os.path.getsize(out) / 1024 / 1024:.2f} MB")


def main():
    with open(PS1) as f:
        template = f.read()
    for pack in PACKS:
        build(pack, template)


if __name__ == "__main__":
    main()
