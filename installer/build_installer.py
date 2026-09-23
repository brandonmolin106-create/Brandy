#!/usr/bin/env python3
"""
Builds download/TMNT-Install-Windows.bat: a single double-click installer.

The .bat is three parts glued together:
  1. a few lines of batch that start PowerShell and run part 2
  2. installer/install.ps1 (between ##PS markers)
  3. the mod jar + pre-built world as a base64 zip (after the ##PAYLOAD marker)

Run from the repo root:  python3 installer/build_installer.py
"""
import base64
import io
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD = os.path.join(ROOT, "download")
JAR = os.path.join(DOWNLOAD, "turtlepower-1.0.0.jar")
WORLD_ZIP = os.path.join(DOWNLOAD, "TMNT-Story-Mode-World.zip")
LOGO = os.path.join(ROOT, "tmnt-story-mode", "src", "main", "resources", "turtlepower_logo.png")
PS1 = os.path.join(ROOT, "installer", "install.ps1")
OUT = os.path.join(DOWNLOAD, "TMNT-Install-Windows.bat")

HEADER = r"""@echo off
setlocal
title TMNT Turtle Power: Story Mode - Installer
set "TMNT_SELF=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText($env:TMNT_SELF); $m='#'+'#PS'; $p=$t.Split(@($m),[StringSplitOptions]::None); Invoke-Expression $p[1]"
echo.
pause
exit /b
"""


def payload():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(JAR, "mods/turtlepower-1.0.0.jar")
        with zipfile.ZipFile(WORLD_ZIP) as w:
            for info in w.infolist():
                if not info.is_dir():
                    z.writestr("saves/" + info.filename, w.read(info.filename))
    return buf.getvalue()


def main():
    with open(PS1) as f:
        script = f.read()
    with open(LOGO, "rb") as f:
        script = script.replace("__ICON__", base64.b64encode(f.read()).decode())
    assert "##PS" not in script and "##PAYLOAD" not in script
    data = base64.encodebytes(payload()).decode()  # 76-char lines
    text = HEADER + "##PS\n" + script + "\n##PS\n##PAYLOAD\n" + data
    with open(OUT, "w", newline="\r\n") as f:
        f.write(text)
    print(f"{OUT}: {os.path.getsize(OUT) / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
