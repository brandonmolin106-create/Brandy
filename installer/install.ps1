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
# It also downloads the pack's extra mods from Modrinth (Verity, Simple Voice Chat, Embeddium, JEI,
# Xaero's maps...). The list lives in installer/mods.lock.json and is glued into this script by
# build_installer.py (into the $ModsJson here-string below). Every file is checked against its SHA-1.
#
# Verity is an AI friend you can TALK to (hold V). Its voice (speech-to-text + text-to-speech) runs
# offline, inside the mod. Its brain needs a free Groq API key (console.groq.com); the installer asks
# for one and writes it into Verity's config, or you can add it later in Mods > Verity > Config.
#
# The TMNT mod + world are glued to the end of the .bat file (base64) so everything is in one file.

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # makes downloads much faster in Windows PowerShell
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }
$WorldName = 'TMNT Story Mode'
$ProfileId = 'tmnt-story-mode'
$VersionId = 'TMNT-Story-Mode'
$NeoVersion = '1.20.1-47.1.106'
$NeoUrl = "https://maven.neoforged.net/releases/net/neoforged/forge/$NeoVersion/forge-$NeoVersion-installer.jar"
$JreUrl = 'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jre/hotspot/normal/eclipse'
$InstalledList = 'tmnt-story-mode.installed.json'   # which mod jars we put in mods\, so updates can clean up
$ModsJson = @'
__MODS__
'@

function Say([string]$text, [string]$color = 'White') { Write-Host $text -ForegroundColor $color }
# Join-Path that just gives $null when the base folder variable doesn't exist on this PC.
function J($base, [string]$child) { if ($base) { Join-Path $base $child } else { $null } }
function Quit([string]$text) {
    Say ''
    Say $text 'Yellow'
    exit 1
}
$utf8 = New-Object System.Text.UTF8Encoding($false)

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

# --- 4. Unpack the TMNT mod and the world -------------------------------------------------------
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
Say '  TMNT mod -> mods folder' 'Gray'

# The starting world is never overwritten: if it is already there, the player's progress stays.
$saves = Join-Path $mc 'saves'
$world = Join-Path $saves $WorldName
New-Item -ItemType Directory -Force -Path $saves | Out-Null
if (Test-Path $world) {
    Say "  You already have the '$WorldName' world, so I kept it (your progress is safe)." 'Gray'
} else {
    Copy-Item (Join-Path $unpack "saves\$WorldName") $saves -Recurse -Force
    Say '  starting world -> saves folder' 'Gray'
}
Remove-Item $zip, $unpack -Recurse -Force -ErrorAction SilentlyContinue

# --- 5. The extra mods: Verity, voice chat and the rest, from Modrinth --------------------------
$modList = @((ConvertFrom-Json $ModsJson).mods)
$totalMb = [math]::Round((($modList | Measure-Object -Property size -Sum).Sum) / 1MB)
Say "Getting $($modList.Count) mods from Modrinth (about $totalMb MB, Verity alone is 246 MB)..." 'Cyan'

function Get-Mod($mod, [string]$dir) {
    $target = Join-Path $dir $mod.filename
    if (Test-Path $target) {
        if ((Get-FileHash $target -Algorithm SHA1).Hash.ToLower() -eq $mod.sha1) {
            Say "  ok       $($mod.filename)" 'Gray'
            return
        }
        Remove-Item $target -Force
    }
    $mb = [math]::Round($mod.size / 1MB, 1)
    Say "  getting  $($mod.title) ($mb MB)" 'Gray'
    $tmp = "$target.part"
    for ($try = 1; $try -le 3; $try++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $mod.url -OutFile $tmp
            if ((Get-FileHash $tmp -Algorithm SHA1).Hash.ToLower() -ne $mod.sha1) { throw 'the file came down damaged (checksum mismatch)' }
            Move-Item $tmp $target -Force
            return
        } catch {
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
            if ($try -eq 3) { throw "Couldn't download $($mod.filename): $_" }
            Say "  retrying $($mod.filename) ($try/3)..." 'Yellow'
            Start-Sleep -Seconds (3 * $try)
        }
    }
}

# Remove jars that an older version of this installer put there and that are not in the list anymore.
$stamp = Join-Path $mods $InstalledList
$previous = @()
if (Test-Path $stamp) { try { $previous = @(Get-Content $stamp -Raw | ConvertFrom-Json) } catch { } }
$wantedNames = @($modList | ForEach-Object { $_.filename })
foreach ($old in $previous) {
    if ($old -and ($wantedNames -notcontains $old) -and (Test-Path (Join-Path $mods $old))) {
        Remove-Item (Join-Path $mods $old) -Force -ErrorAction SilentlyContinue
        Say "  removed old $old" 'Gray'
    }
}
foreach ($mod in $modList) { Get-Mod $mod $mods }
[IO.File]::WriteAllText($stamp, (ConvertTo-Json -InputObject $wantedNames), $utf8)
Say "  all $($modList.Count) mods are in place" 'Green'

# --- 6. Verity: voice on, brain = Groq ------------------------------------------------------------
# Verity's config is a Forge TOML (config\verity-client.toml + verity-common.toml, same keys). We only
# set the keys we care about; Forge fills in the rest with defaults on first launch.
function Set-TomlValue([string]$path, [string]$section, [string]$key, [string]$literal) {
    $path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($path)
    $lines = @()
    if (Test-Path $path) { $lines = @(Get-Content $path) }
    $indent = ''
    $start = 0
    $end = $lines.Count
    if ($section) {
        $indent = "`t"
        $idx = -1
        for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim() -eq "[$section]") { $idx = $i; break } }
        if ($idx -lt 0) { $lines += "[$section]"; $idx = $lines.Count - 1 }
        $start = $idx + 1
        $end = $lines.Count
        for ($i = $start; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim().StartsWith('[')) { $end = $i; break } }
    } else {
        for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim().StartsWith('[')) { $end = $i; break } }
    }
    $pattern = '^\s*' + [regex]::Escape($key) + '\s*='
    for ($i = $start; $i -lt $end; $i++) {
        if ($lines[$i] -match $pattern) {
            $lines[$i] = "$indent$key = $literal"
            [IO.File]::WriteAllLines($path, [string[]]$lines, $utf8)
            return
        }
    }
    $new = @()
    if ($end -gt 0) { $new += $lines[0..($end - 1)] }
    $new += "$indent$key = $literal"
    if ($end -lt $lines.Count) { $new += $lines[$end..($lines.Count - 1)] }
    [IO.File]::WriteAllLines($path, [string[]]$new, $utf8)
}
function TomlString([string]$s) { '"' + $s.Replace('\', '\\').Replace('"', '\"') + '"' }

$cfgDir = Join-Path $mc 'config'
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$verityCfgs = @((Join-Path $cfgDir 'verity-client.toml'), (Join-Path $cfgDir 'verity-common.toml'))

$existingKey = ''
foreach ($p in $verityCfgs) {
    if ((Test-Path $p) -and ((Get-Content $p -Raw) -match '(?m)^\s*apiKey\s*=\s*"([^"]+)"')) { $existingKey = $Matches[1]; break }
}
$groqKey = ''
if ($env:GROQ_API_KEY) { $groqKey = $env:GROQ_API_KEY.Trim() }
Say ''
Say 'VERITY - your AI helper friend (hold V to talk to him, he talks back)' 'Magenta'
Say 'His voice works offline. His BRAIN needs a free Groq key:' 'White'
Say '  1. go to https://console.groq.com  and make a free account' 'Gray'
Say '  2. API Keys -> Create API Key -> copy it (it starts with gsk_)' 'Gray'
if ($existingKey) {
    Say '  (You already have a key saved. Press Enter to keep it.)' 'Gray'
} else {
    Say '  (No key yet? Press Enter to skip. Verity still spawns, you can add the key later in' 'Gray'
    Say '   Mods > Verity > Config > AI Settings > API Key.)' 'Gray'
}
if (-not $groqKey) {
    try {
        $secure = Read-Host 'Paste your Groq API key here' -AsSecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        $groqKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr).Trim()
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    } catch { $groqKey = '' }
}
if ($groqKey -and -not $groqKey.StartsWith('gsk_')) {
    Say "  Hmm, Groq keys start with gsk_ - I'll save it anyway, but double-check it in Mods > Verity > Config." 'Yellow'
}
foreach ($p in $verityCfgs) {
    Set-TomlValue $p '' 'playVideo' 'false'                 # keep the TMNT title screen, not Verity's intro video
    Set-TomlValue $p '' 'canCrash' 'false'                  # Verity may not kick you out of story mode
    Set-TomlValue $p 'AISettings' 'aiProvider' '"GROQ"'
    Set-TomlValue $p 'AISettings' 'useLocalStt' 'true'      # offline speech-to-text (built into the mod)
    Set-TomlValue $p 'AISettings' 'useLocalTts' 'true'      # offline text-to-speech (built into the mod)
    if ($groqKey) { Set-TomlValue $p 'AISettings' 'apiKey' (TomlString $groqKey) }
}
if ($groqKey) { Say '  Groq key saved. Verity has a brain.' 'Green' }
elseif ($existingKey) { Say '  Kept your saved Groq key.' 'Green' }
else { Say '  No key saved. Verity will spawn but stay quiet until you add one.' 'Yellow' }

# Key binds: Verity talks on V and Simple Voice Chat's menu is also V (and both use M), so the voice
# chat menu moves to B, voice chat mute to . and Verity's "cycle mic" to , - only if you haven't
# bound them yourself already. Change any of them in Options > Controls (Controlling adds a search box).
$opts = Join-Path $mc 'options.txt'
$optLines = @()
if (Test-Path $opts) { $optLines = @(Get-Content $opts) }
$remap = [ordered]@{
    'key_key.voice_chat'       = 'key.keyboard.b'
    'key_key.mute_microphone'  = 'key.keyboard.period'
    'key_key.verity.cycle_mic' = 'key.keyboard.comma'
}
$added = 0
foreach ($k in $remap.Keys) {
    $prefix = $k + ':'
    if (-not ($optLines | Where-Object { $_.StartsWith($prefix) })) { $optLines += ($prefix + $remap[$k]); $added++ }
}
if ($added -gt 0) { [IO.File]::WriteAllLines($opts, [string[]]$optLines, $utf8) }
Say '  key binds: V = talk to Verity, B = voice chat menu, M = world map' 'Gray'

# --- 7. A launcher version that opens the world straight away -----------------------------------
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
[IO.File]::WriteAllText((Join-Path $vdir "$VersionId.json"), ($version | ConvertTo-Json -Depth 8), $utf8)

# --- 8. Add the "TMNT Story Mode" profile and pick it ------------------------------------------
# 26 mods + Verity's speech models want more than the launcher's 2 GB default.
$ramGb = 8
try { $ramGb = [math]::Floor((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB) } catch { }
$xmx = if ($ramGb -ge 12) { '4G' } elseif ($ramGb -ge 8) { '3G' } else { '2G' }
$javaArgs = "-Xmx$xmx -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"
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
        javaArgs      = $javaArgs
        icon          = 'data:image/png;base64,__ICON__'
    }
    $lp.profiles | Add-Member -NotePropertyName $ProfileId -NotePropertyValue $newProfile -Force
    [IO.File]::WriteAllText($profilesFile, ($lp | ConvertTo-Json -Depth 64), $utf8)
    Say "  added 'TMNT Story Mode' to the Minecraft Launcher ($xmx of RAM for the game)" 'Gray'
} catch {
    Say "  (Couldn't add the launcher profile. In the launcher, pick 'forge' next to PLAY instead.)" 'Yellow'
}

# --- 9. Done! -----------------------------------------------------------------------------------
Say ''
Say 'ALL DONE! COWABUNGA!' 'Green'
Say ''
Say 'Opening the Minecraft Launcher...' 'Cyan'
Say "Press the big green PLAY button ('TMNT Story Mode' should already be picked next to it)."
Say 'Minecraft loads straight into the lair. You are Raphael!'
Say 'Verity shows up in his box after a bit. Hold V and talk to him. Be nice... or not.' 'Magenta'
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
