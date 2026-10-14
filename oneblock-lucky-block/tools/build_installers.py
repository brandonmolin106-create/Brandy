#!/usr/bin/env python3
"""Build double-click installers that carry the world inside them.

Run after build_oneblock_world.py:
  python3 tools/build_installers.py

Produces, next to the zip:
  Install OneBlock Lucky Block - Windows.bat   (double-click: installs + opens the launcher)
  Install OneBlock Lucky Block - Mac.command   (double-click: installs + opens Minecraft)
  Install OneBlock Lucky Block - Mac.zip       (same, zipped so the run permission survives download)
"""
from __future__ import annotations

import base64
import stat
import textwrap
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "OneBlock_Lucky_Block.zip"
WORLD_NAME = "OneBlock Lucky Block"

payload = base64.b64encode(ZIP_PATH.read_bytes()).decode("ascii")
b64_lines = textwrap.wrap(payload, 76)

# ---------------------------------------------------------------------------
# Windows: a .bat that decodes itself with PowerShell, unzips into saves,
# then opens the Minecraft Launcher (Store or classic install).
# ---------------------------------------------------------------------------
WIN = r'''@echo off
setlocal EnableExtensions
title One Block: Lucky Block Edition - installer
echo.
echo  =============================================
echo   ONE BLOCK: LUCKY BLOCK EDITION  (Java Edition)
echo   by Echoes in the Dark
echo  =============================================
echo.
set "SAVES=%APPDATA%\.minecraft\saves"
if not exist "%APPDATA%\.minecraft" (
  echo  Could not find your Minecraft folder at %APPDATA%\.minecraft
  echo  Install and run Minecraft: Java Edition once, then run this again.
  echo.
  pause
  exit /b 1
)
if not exist "%SAVES%" mkdir "%SAVES%"
set "ZIPFILE=%TEMP%\OneBlock_Lucky_Block.zip"
echo  Unpacking the world...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines = Get-Content -LiteralPath '%~f0' | Where-Object { $_ -like 'B64:*' } | ForEach-Object { $_.Substring(4) }; [IO.File]::WriteAllBytes('%ZIPFILE%', [Convert]::FromBase64String(($lines -join '')))"
if errorlevel 1 goto :fail
echo  Installing into %SAVES%\__WORLD__ ...
if exist "%SAVES%\__WORLD__" rmdir /s /q "%SAVES%\__WORLD__"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIPFILE%' -DestinationPath '%SAVES%' -Force"
if errorlevel 1 goto :fail
del "%ZIPFILE%" >nul 2>&1
echo.
echo  DONE. The world "__WORLD__" is installed.
echo  Opening the Minecraft Launcher... click PLAY, then Singleplayer,
echo  and the world with the yellow lucky block icon is at the top.
echo.
set "LAUNCHED="
if exist "%ProgramFiles(x86)%\Minecraft Launcher\MinecraftLauncher.exe" ( start "" "%ProgramFiles(x86)%\Minecraft Launcher\MinecraftLauncher.exe" & set "LAUNCHED=1" )
if not defined LAUNCHED if exist "%ProgramFiles%\Minecraft Launcher\MinecraftLauncher.exe" ( start "" "%ProgramFiles%\Minecraft Launcher\MinecraftLauncher.exe" & set "LAUNCHED=1" )
if not defined LAUNCHED if exist "C:\XboxGames\Minecraft Launcher\Content\Minecraft.exe" ( start "" "C:\XboxGames\Minecraft Launcher\Content\Minecraft.exe" & set "LAUNCHED=1" )
if not defined LAUNCHED ( start "" explorer.exe shell:AppsFolder\Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft & set "LAUNCHED=1" )
timeout /t 8 >nul
exit /b 0
:fail
echo.
echo  Something went wrong. Plan B: unzip OneBlock_Lucky_Block.zip by hand into
echo  %SAVES%
echo.
pause
exit /b 1
'''.replace("__WORLD__", WORLD_NAME)

win_text = WIN.replace("\n", "\r\n") + "\r\n" + "\r\n".join("B64:" + ln for ln in b64_lines) + "\r\n"
(ROOT / "Install OneBlock Lucky Block - Windows.bat").write_text(win_text, encoding="ascii", newline="")

# ---------------------------------------------------------------------------
# Mac: a .command (bash) with the zip appended after a marker.
# ---------------------------------------------------------------------------
MAC = r'''#!/bin/bash
# One Block: Lucky Block Edition - installer (Minecraft: Java Edition, macOS)
set -e
WORLD="__WORLD__"
SAVES="$HOME/Library/Application Support/minecraft/saves"
echo
echo " ONE BLOCK: LUCKY BLOCK EDITION  (Java Edition)"
echo " by Echoes in the Dark"
echo
if [ ! -d "$HOME/Library/Application Support/minecraft" ]; then
  echo " Could not find your Minecraft folder. Install and run Minecraft: Java Edition once, then run this again."
  read -r -p " Press Enter to close." _
  exit 1
fi
mkdir -p "$SAVES"
TMPZIP="${TMPDIR:-/tmp}/oneblock_lucky_$$.zip"
echo " Unpacking the world..."
sed -n '/^__PAYLOAD__$/,$p' "$0" | tail -n +2 | base64 -d > "$TMPZIP"
rm -rf "$SAVES/$WORLD"
echo " Installing into $SAVES/$WORLD ..."
unzip -q -o "$TMPZIP" -d "$SAVES"
rm -f "$TMPZIP"
echo
echo " DONE. Opening Minecraft... click PLAY, then Singleplayer,"
echo " and the world with the yellow lucky block icon is at the top."
echo
open -a "Minecraft" 2>/dev/null || open -a "Minecraft Launcher" 2>/dev/null || echo " (Could not auto-open the launcher. Open Minecraft yourself.)"
sleep 3
exit 0
__PAYLOAD__
'''.replace("__WORLD__", WORLD_NAME)

mac_text = MAC + "\n".join(b64_lines) + "\n"
mac_path = ROOT / "Install OneBlock Lucky Block - Mac.command"
mac_path.write_text(mac_text, encoding="ascii")
mac_path.chmod(mac_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# zip it so the executable bit survives a browser download
with zipfile.ZipFile(ROOT / "Install OneBlock Lucky Block - Mac.zip", "w", zipfile.ZIP_DEFLATED) as z:
    info = zipfile.ZipInfo(mac_path.name)
    info.external_attr = (0o755 << 16)
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, mac_text)

print("installers built:")
for p in sorted(ROOT.glob("Install *")):
    print(f"  {p.name}  ({p.stat().st_size // 1024} KB)")
