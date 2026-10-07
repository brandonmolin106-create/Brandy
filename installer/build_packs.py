#!/usr/bin/env python3
"""
Builds the other downloads from the same ingredients as the .bat installer:

  download/TMNT-Story-Mode.mrpack          Modrinth pack: every mod as a download entry (hashes from
                                           mods.lock.json) + the TMNT jar, world and configs as overrides.
                                           Import it in the Modrinth App, Prism, ATLauncher, MultiMC...
  download/TMNT-Story-Mode-AllInOne.zip    Unzip into .minecraft: TMNT jar + world + configs. The extra
                                           mods are NOT inside (Verity alone is 246 MB); MODS.txt lists
                                           the exact files to get from Modrinth.
  download/TMNT-Story-Mode-CurseForge.zip  CurseForge import: TMNT jar + world + configs. Same note.
  download/MODS.txt                        Human-readable list of the pack's mods and where they come from.

Run from the repo root:  python3 installer/build_packs.py
(Run installer/resolve_mods.py first if you changed installer/mods.json.)
"""
import io
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD = os.path.join(ROOT, "download")
JAR = os.path.join(DOWNLOAD, "turtlepower-1.0.0.jar")
WORLD_ZIP = os.path.join(DOWNLOAD, "verity-world.zip")
LOCK = os.path.join(ROOT, "installer", "mods.lock.json")

PACK_NAME = "TMNT Story Mode"
PACK_VERSION = "1.1.0"
MC = "1.20.1"
FORGE = "47.4.10"
SUMMARY = ("Fan-made TMNT story mode: you are Raphael. Pre-built New York world, Verity (the AI friend "
           "you can talk to), voice chat, maps, performance mods.")

# Verity's config, same keys in both files (it registers one spec as CLIENT and COMMON).
# Forge fills in every other key with its default on first launch.
VERITY_TOML = """\
#Play the Verity Edit on the startup of the client.
playVideo = false
#Allow Verity to kick you from the server.
canCrash = false

[AISettings]
\t#Choose the AI Provider to use for Verity.
\taiProvider = "GROQ"
\t#Put your Groq API Key here to give Verity a brain. Free key: https://console.groq.com
\tapiKey = ""
\t#Offline speech-to-text (built into the mod)
\tuseLocalStt = true
\t#Offline text-to-speech (built into the mod)
\tuseLocalTts = true
"""

# Verity talks on V and Simple Voice Chat's menu is V too (and both use M): move the voice chat keys.
OPTIONS_TXT = """\
key_key.voice_chat:key.keyboard.b
key_key.mute_microphone:key.keyboard.period
key_key.verity.cycle_mic:key.keyboard.comma
"""

HOW_TO = """\
TMNT STORY MODE - ALL IN ONE (Minecraft Java 1.20.1, Forge)

This zip has the TMNT mod, the saved New York world (named "verity") and the configs together.
The EASIEST way to play is the one-file installer: Play-Verity.bat (Windows). It does
all of this for you and also downloads the extra mods (Verity, voice chat, maps...).

By hand:
1. Install Forge 1.20.1 once: https://files.minecraftforge.net  (pick 1.20.1, "Installer", run it, "Install client").
2. Open your .minecraft folder:
     Windows: press Win+R, type  %appdata%\\.minecraft  and press Enter
     Mac:     ~/Library/Application Support/minecraft
3. Unzip THIS file right into that .minecraft folder.
   It puts the mod in  mods/ , the world in  saves/  and the configs in  config/ .
4. Extra mods: download every file listed in MODS.txt into  mods/  (all free, from modrinth.com).
   Or skip them - the TMNT story works with just the TMNT mod.
5. Verity's brain: get a free Groq API key at https://console.groq.com and paste it into
   config/verity-client.toml (apiKey = "gsk_...") or in-game: Mods > Verity > Config > AI Settings.
6. Start Minecraft with the "forge" profile -> Singleplayer -> "verity".
   Give the game 3-4 GB of RAM in the launcher (Installations > Edit > More options > JVM arguments: -Xmx4G).

You are Raphael. Hold V to talk to Verity. Have fun!
(Unofficial fan project. TMNT belongs to its owners. Not for sale.)
"""


def lock():
    with open(LOCK) as f:
        return json.load(f)


def world_files():
    with zipfile.ZipFile(WORLD_ZIP) as w:
        for info in w.infolist():
            if not info.is_dir():
                yield info.filename, w.read(info.filename)


def add_overrides(z, prefix):
    z.write(JAR, prefix + "mods/turtlepower-1.0.0.jar")
    for name, data in world_files():
        z.writestr(prefix + "saves/" + name, data)
    z.writestr(prefix + "config/verity-client.toml", VERITY_TOML)
    z.writestr(prefix + "config/verity-common.toml", VERITY_TOML)
    z.writestr(prefix + "options.txt", OPTIONS_TXT)


def mods_txt(lk):
    lines = [
        f"TMNT STORY MODE {PACK_VERSION} - MODS  (Minecraft {MC}, Forge {FORGE})",
        "",
        "The TMNT mod (turtlepower-1.0.0.jar) is ours. Everything below is a free mod from modrinth.com.",
        "Play-Verity.bat downloads all of them for you. The .mrpack has them too.",
        f"Total: {len(lk['mods'])} mods, {lk['total_bytes'] / 1e6:.0f} MB.",
        "",
    ]
    for m in lk["mods"]:
        tag = "" if m["requested"] else "   (needed by another mod)"
        lines.append(f"{m['title']}  {m['version']}{tag}")
        lines.append(f"    {m['why']}")
        lines.append(f"    file: {m['filename']}")
        lines.append(f"    page: https://modrinth.com/mod/{m['slug']}/version/{m['version_id']}")
        lines.append("")
    lines += [
        "VERITY - the AI friend (hold V to talk, he talks back)",
        "  Voice (speech-to-text + text-to-speech) runs offline inside the mod.",
        "  His brain needs a free Groq API key: https://console.groq.com -> API Keys -> Create.",
        "  Paste it in Mods > Verity > Config > AI Settings > API Key (or the installer asks for it).",
        "  Never paste the key into chat, screenshots or logs.",
        "",
        "KEYS: V = talk to Verity | B = voice chat menu (Simple Voice Chat) | . = mute mic | , = Verity cycle mic",
        "      M = world map (Xaero) | Options > Controls has a search box (Controlling) if anything clashes.",
        "",
        "Left out on purpose: Create, Cobblemon, Terralith, Biomes O' Plenty and other world-gen/content",
        "mods. They would change the New York world and the TMNT story.",
    ]
    return "\n".join(lines) + "\n"


def build_mrpack(lk):
    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": PACK_VERSION,
        "name": PACK_NAME,
        "summary": SUMMARY,
        "files": [
            {
                "path": "mods/" + m["filename"],
                "hashes": {"sha1": m["sha1"], "sha512": m["sha512"]},
                "env": {"client": m["client_side"], "server": m["server_side"]},
                "downloads": [m["url"]],
                "fileSize": m["size"],
            }
            for m in lk["mods"]
        ],
        "dependencies": {"minecraft": MC, "forge": FORGE},
    }
    out = os.path.join(DOWNLOAD, "TMNT-Story-Mode.mrpack")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("modrinth.index.json", json.dumps(index, indent=2))
        add_overrides(z, "overrides/")
    return out


def build_allinone(lk):
    out = os.path.join(DOWNLOAD, "TMNT-Story-Mode-AllInOne.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        add_overrides(z, "")
        z.writestr("HOW TO INSTALL.txt", HOW_TO)
        z.writestr("MODS.txt", mods_txt(lk))
    return out


def build_curseforge(lk):
    # CurseForge manifests can only reference CurseForge file IDs, not Modrinth downloads, so this
    # zip carries the TMNT mod, world and configs; MODS.txt says which extra mods to add.
    manifest = {
        "minecraft": {"version": MC, "modLoaders": [{"id": f"forge-{FORGE}", "primary": True}]},
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": PACK_NAME,
        "version": PACK_VERSION,
        "author": "Echoes in the Dark",
        "files": [],
        "overrides": "overrides",
    }
    out = os.path.join(DOWNLOAD, "TMNT-Story-Mode-CurseForge.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
        add_overrides(z, "overrides/")
        z.writestr("MODS.txt", mods_txt(lk))
    return out


def main():
    lk = lock()
    outs = [build_mrpack(lk), build_allinone(lk), build_curseforge(lk)]
    mods_path = os.path.join(DOWNLOAD, "MODS.txt")
    with open(mods_path, "w") as f:
        f.write(mods_txt(lk))
    outs.append(mods_path)
    for o in outs:
        print(f"{os.path.relpath(o, ROOT)}: {os.path.getsize(o) / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
