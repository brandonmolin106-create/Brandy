# TMNT Turtle Power: Story Mode - double-click to install and play (Minecraft Java, Windows).
#
# Puts the mod in .minecraft\mods, the pre-built world in .minecraft\saves, and adds a
# "TMNT Story Mode" profile to the Minecraft Launcher that opens the world as soon as you press Play.
#
# It downloads and installs NeoForge 1.20.1 (the mod loader) by itself, and a Java runtime from
# Adoptium if the computer doesn't have one, so there is nothing else to download by hand.
# (Regular Forge asks people not to automate its download, so we use NeoForge, which runs Forge
# 1.20.1 mods.)
#
# The mod + world are glued to the end of the .bat file (base64) so everything is in one file.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # makes downloads much faster in Windows PowerShell
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }
$WorldName = 'TMNT Story Mode'
$ProfileId = 'tmnt-story-mode'
$VersionId = 'TMNT-Story-Mode'
$NeoVersion = '1.20.1-47.1.106'
$NeoUrl = "https://maven.neoforged.net/releases/net/neoforged/forge/$NeoVersion/forge-$NeoVersion-installer.jar"
$JreUrl = 'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jre/hotspot/normal/eclipse'

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
function Find-Java {
    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $roots = @(
        (J $env:LOCALAPPDATA 'TMNT-Story-Mode\jre'),
        (J $mc 'runtime'),
        (J $env:LOCALAPPDATA 'Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\runtime'),
        (J ${env:ProgramFiles(x86)} 'Minecraft Launcher\runtime'),
        (J $env:ProgramFiles 'Minecraft Launcher\runtime'),
        (J $env:USERPROFILE 'curseforge\minecraft\Install\runtime')
    )
    foreach ($r in $roots) {
        if ($r -and (Test-Path $r)) {
            $j = Get-ChildItem $r -Recurse -Include 'java.exe', 'java' -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Directory.Name -eq 'bin' } | Select-Object -First 1
            if ($j) { return $j.FullName }
        }
    }
    return $null
}

# --- 3. Mod loader: NeoForge 1.20.1 (downloaded for you) -----------------------------------------
# NeoForge is the community version of Forge; Forge 1.20.1 mods run on it. Unlike Forge it doesn't
# ask people not to automate installs, so this downloads it from the official NeoForged server.
$versions = Join-Path $mc 'versions'
$loader = $null
if (Test-Path $versions) {
    $loader = Get-ChildItem $versions -Directory -Filter '1.20.1-forge-47.*' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
}
if (-not $loader) {
    $java = Find-Java
    if (-not $java) {
        Say 'Getting Java (needed once to set up the mod loader, about 45 MB)...' 'Cyan'
        $jreZip = Join-Path $env:TEMP 'tmnt-jre.zip'
        $jreDir = Join-Path $env:LOCALAPPDATA 'TMNT-Story-Mode\jre'
        Invoke-WebRequest -UseBasicParsing -Uri $JreUrl -OutFile $jreZip
        if (Test-Path $jreDir) { Remove-Item $jreDir -Recurse -Force }
        Expand-Archive -Path $jreZip -DestinationPath $jreDir -Force
        Remove-Item $jreZip -Force -ErrorAction SilentlyContinue
        $java = Find-Java
        if (-not $java) { Quit "Couldn't set up Java. Check your internet and run me again." }
    }
    Say "Downloading NeoForge $NeoVersion (the mod loader)..." 'Cyan'
    $installerJar = Join-Path $env:TEMP "neoforge-$NeoVersion-installer.jar"
    Invoke-WebRequest -UseBasicParsing -Uri $NeoUrl -OutFile $installerJar
    Say 'Installing NeoForge... this takes a minute or two, please wait.' 'Cyan'
    $log = Join-Path $env:TEMP 'tmnt-neoforge-install.log'
    $proc = Start-Process -FilePath $java -WorkingDirectory $env:TEMP -Wait -PassThru -NoNewWindow `
        -ArgumentList @('-jar', "`"$installerJar`"", '--installClient', "`"$mc`"") `
        -RedirectStandardOutput $log -RedirectStandardError "$log.err"
    Remove-Item $installerJar -Force -ErrorAction SilentlyContinue
    if ($proc.ExitCode -ne 0) {
        Get-Content $log -Tail 15 -ErrorAction SilentlyContinue | Out-Host
        Quit "The mod loader didn't install (details above). Check your internet and run me again."
    }
    $loader = Get-ChildItem $versions -Directory -Filter '1.20.1-forge-47.*' | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $loader) { Quit "The mod loader didn't install. Check your internet and run me again." }
}
Say "Mod loader is ready: $($loader.Name)" 'Green'

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
$loaderJson = Get-Content (Join-Path $loader.FullName "$($loader.Name).json") -Raw | ConvertFrom-Json
$vdir = Join-Path $versions $VersionId
New-Item -ItemType Directory -Force -Path $vdir | Out-Null
$now = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'")
$version = [ordered]@{
    id           = $VersionId
    inheritsFrom = $loader.Name
    type         = 'release'
    time         = $now
    releaseTime  = $now
    mainClass    = $loaderJson.mainClass
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
    Say "  (Couldn't add the launcher profile. In the launcher, pick 'forge' next to PLAY instead.)" 'Yellow'
}

# --- 7. Done! -----------------------------------------------------------------------------------
Say ''
Say 'ALL DONE! COWABUNGA!' 'Green'
Say ''
Say 'Opening the Minecraft Launcher...' 'Cyan'
Say "Press the big green PLAY button ('TMNT Story Mode' should already be picked next to it)."
Say 'Minecraft loads straight into the lair. You are Raphael!'
Say 'Next time you can just open the Minecraft Launcher and press PLAY, or double-click me again.' 'Gray'
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
