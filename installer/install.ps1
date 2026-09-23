# TMNT Turtle Power: Story Mode - one-click installer for Minecraft Java (Windows).
#
# Puts the mod in .minecraft\mods, the pre-built world in .minecraft\saves, and adds a
# "TMNT Story Mode" profile to the Minecraft Launcher that opens the world as soon as you press Play.
#
# Forge asks people not to auto-download it (their download page ads pay for Forge), so this
# script does not download Forge. If Forge 1.20.1 isn't installed yet it opens the official Forge
# page; you click "Installer", and next time this script finds that file in Downloads and installs
# it for you.
#
# The mod + world are glued to the end of the .bat file (base64) so everything is in one file.

$ErrorActionPreference = 'Stop'
$WorldName = 'TMNT Story Mode'
$ProfileId = 'tmnt-story-mode'
$VersionId = 'TMNT-Story-Mode'
$ForgePage = 'https://files.minecraftforge.net/net/minecraftforge/forge/index_1.20.1.html'

function Say([string]$text, [string]$color = 'White') { Write-Host $text -ForegroundColor $color }
# Join-Path that just gives $null when the base folder variable doesn't exist on this PC.
function J($base, [string]$child) { if ($base) { Join-Path $base $child } else { $null } }
function Quit([string]$text) {
    Say ''
    Say $text 'Yellow'
    exit 1
}

Say '=============================================' 'Green'
Say '   TMNT TURTLE POWER: STORY MODE  - installer' 'Green'
Say '=============================================' 'Green'
Say ''

# --- 1. Find Minecraft --------------------------------------------------------------------------
$mc = Join-Path $env:APPDATA '.minecraft'
$profilesFile = Join-Path $mc 'launcher_profiles.json'
if (-not (Test-Path $profilesFile)) {
    Quit "I can't find Minecraft Java Edition on this computer.`nOpen the Minecraft Launcher once (and log in), close it, then double-click me again."
}
Say "Found Minecraft: $mc" 'Gray'

# --- 2. Find Java (the Minecraft Launcher brings its own) ----------------------------------------
$java = $null
$cmd = Get-Command java -ErrorAction SilentlyContinue
if ($cmd) { $java = $cmd.Source }
if (-not $java) {
    $roots = @(
        (J $mc 'runtime'),
        (J $env:LOCALAPPDATA 'Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\runtime'),
        (J ${env:ProgramFiles(x86)} 'Minecraft Launcher\runtime'),
        (J $env:ProgramFiles 'Minecraft Launcher\runtime'),
        (J $env:USERPROFILE 'curseforge\minecraft\Install\runtime')
    )
    foreach ($r in $roots) {
        if ($r -and (Test-Path $r)) {
            $j = Get-ChildItem $r -Recurse -Filter 'java.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($j) { $java = $j.FullName; break }
        }
    }
}

# --- 3. Forge 1.20.1 ----------------------------------------------------------------------------
$versions = Join-Path $mc 'versions'
$forge = $null
if (Test-Path $versions) {
    $forge = Get-ChildItem $versions -Directory -Filter '1.20.1-forge-47.*' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
}
if (-not $forge) {
    $downloads = J $env:USERPROFILE 'Downloads'
    $here = Split-Path -Parent $env:TMNT_SELF
    $installer = @($downloads, $here) | Where-Object { $_ -and (Test-Path $_) } | ForEach-Object {
        Get-ChildItem $_ -File -Filter 'forge-1.20.1-47.*-installer.jar' -ErrorAction SilentlyContinue
    } | Sort-Object Name -Descending | Select-Object -First 1

    if (-not $installer) {
        Say 'Step 1 of 2: you need Forge 1.20.1 (the thing that lets Minecraft load mods).' 'Cyan'
        Say 'I am opening the official Forge page for you now.' 'Cyan'
        Say ''
        Say '  1. Click the "Installer" button under "Download Recommended".'
        Say '  2. The ad page will show a "SKIP" button at the top right after a few seconds - click it.'
        Say '  3. Save the file (it goes to your Downloads folder). You do NOT need to open it.'
        Say '  4. Double-click this installer again. I will do the rest.'
        try { Start-Process $ForgePage } catch { Say "Open this in your browser: $ForgePage" 'Yellow' }
        exit 0
    }
    if (-not $java) {
        Quit "I found the Forge installer but no Java to run it.`nStart Minecraft once from the launcher (normal 1.20.1, no mods), close it, then run me again."
    }
    Say "Installing Forge from $($installer.Name) (this takes a minute or two)..." 'Cyan'
    & $java -jar $installer.FullName --installClient $mc | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Quit "Forge didn't install. Try double-clicking the Forge file in Downloads and choosing 'Install client', then run me again."
    }
    $forge = Get-ChildItem $versions -Directory -Filter '1.20.1-forge-47.*' | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $forge) { Quit "Forge didn't install. Try double-clicking the Forge file in Downloads and choosing 'Install client'." }
}
Say "Forge is ready: $($forge.Name)" 'Green'

# --- 4. Unpack the mod and the world ------------------------------------------------------------
Say 'Unpacking the TMNT mod and the New York world...' 'Cyan'
$all = [IO.File]::ReadAllText($env:TMNT_SELF)
$marker = '#' + '#PAYLOAD'
$parts = $all.Split(@($marker), [StringSplitOptions]::None)
if ($parts.Count -lt 2) { Quit 'This installer file is damaged. Download it again.' }
$zip = Join-Path $env:TEMP 'tmnt-story-mode-payload.zip'
[IO.File]::WriteAllBytes($zip, [Convert]::FromBase64String($parts[1].Trim()))
$unpack = Join-Path $env:TEMP 'tmnt-story-mode-payload'
if (Test-Path $unpack) { Remove-Item $unpack -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $unpack -Force

$mods = Join-Path $mc 'mods'
New-Item -ItemType Directory -Force -Path $mods | Out-Null
Get-ChildItem $mods -Filter 'turtlepower-*.jar' -ErrorAction SilentlyContinue | Remove-Item -Force
Copy-Item (Join-Path $unpack 'mods\*') $mods -Force
Say '  mod -> mods folder' 'Gray'

$saves = Join-Path $mc 'saves'
$world = Join-Path $saves $WorldName
New-Item -ItemType Directory -Force -Path $saves | Out-Null
if (Test-Path $world) {
    Say "  You already have the '$WorldName' world, so I kept it (your progress is safe)." 'Gray'
} else {
    Copy-Item (Join-Path $unpack "saves\$WorldName") $saves -Recurse -Force
    Say '  world -> saves folder' 'Gray'
}
Remove-Item $zip, $unpack -Recurse -Force -ErrorAction SilentlyContinue

# --- 5. A launcher version that opens the world straight away -----------------------------------
$forgeJson = Get-Content (Join-Path $forge.FullName "$($forge.Name).json") -Raw | ConvertFrom-Json
$vdir = Join-Path $versions $VersionId
New-Item -ItemType Directory -Force -Path $vdir | Out-Null
$now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'")
$version = [ordered]@{
    id           = $VersionId
    inheritsFrom = $forge.Name
    type         = 'release'
    time         = $now
    releaseTime  = $now
    mainClass    = $forgeJson.mainClass
    libraries    = @()
    arguments    = [ordered]@{ game = @('--quickPlaySingleplayer', $WorldName); jvm = @() }
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $vdir "$VersionId.json"), ($version | ConvertTo-Json -Depth 8), $utf8)

# --- 6. Add the "TMNT Story Mode" profile and pick it ------------------------------------------
try {
    Copy-Item $profilesFile "$profilesFile.before-tmnt" -Force
    $lp = Get-Content $profilesFile -Raw | ConvertFrom-Json
    if (-not $lp.profiles) { $lp | Add-Member -NotePropertyName profiles -NotePropertyValue ([pscustomobject]@{}) -Force }
    $newProfile = [pscustomobject][ordered]@{
        name          = 'TMNT Story Mode'
        type          = 'custom'
        lastVersionId = $VersionId
        lastUsed      = $now
        created       = $now
        icon          = 'data:image/png;base64,__ICON__'
    }
    $lp.profiles | Add-Member -NotePropertyName $ProfileId -NotePropertyValue $newProfile -Force
    [IO.File]::WriteAllText($profilesFile, ($lp | ConvertTo-Json -Depth 64), $utf8)
    Say "  added 'TMNT Story Mode' to the Minecraft Launcher" 'Gray'
} catch {
    Say "  (Couldn't add the launcher profile. In the launcher, pick 'forge' next to Play instead.)" 'Yellow'
}

# --- 7. Done! -----------------------------------------------------------------------------------
Say ''
Say 'ALL DONE! COWABUNGA!' 'Green'
Say ''
Say 'Opening the Minecraft Launcher...' 'Cyan'
Say "Make sure 'TMNT Story Mode' is picked next to the big green PLAY button, then press PLAY."
Say 'Minecraft will load straight into the lair. You are Raphael!'
$launched = $false
foreach ($exe in @((J ${env:ProgramFiles(x86)} 'Minecraft Launcher\MinecraftLauncher.exe'),
                   (J $env:ProgramFiles 'Minecraft Launcher\MinecraftLauncher.exe'))) {
    if (-not $launched -and $exe -and (Test-Path $exe)) {
        try { Start-Process $exe; $launched = $true } catch { }
    }
}
if (-not $launched -and $env:OS -eq 'Windows_NT') {
    try { Start-Process 'shell:AppsFolder\Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft'; $launched = $true } catch { }
}
if (-not $launched) { Say '(Open the Minecraft Launcher yourself - everything is installed.)' 'Yellow' }
