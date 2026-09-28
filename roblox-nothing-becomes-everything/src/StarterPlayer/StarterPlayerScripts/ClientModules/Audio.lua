--!strict
-- StarterPlayerScripts > ClientModules > Audio  (ModuleScript)
-- All sound comes from three uploaded files ("packs"): voice, SFX and music.
-- Each line, effect or track is a slice of its pack, played with
-- Sound.PlaybackRegionsEnabled + Sound.PlaybackRegion (NumberRange, seconds), and
-- music loops inside its slice with Sound.LoopRegion. With a pack id of 0 nothing
-- plays, but every function still returns the right durations (captions keep working).

local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local Content = require(ReplicatedStorage:WaitForChild("Content"))

local Audio = {}

local MUSIC_LEVEL = 0.8
local VOICE_LEVEL = 1.4
local SFX_COUNT = 8

local musicGroup: SoundGroup
local voiceGroup: SoundGroup
local sfxGroup: SoundGroup
local voiceSound: Sound
local musicSounds: { Sound } = {}
local sfxPool: { Sound } = {}
local sfxTokens: { [Sound]: number } = {}
local sfxNext = 1
local activeMusic: Sound? = nil
local currentTrack: string? = nil
local afterTrack: string? = nil
local musicEnabled = true
local ducked = false
local lineToken = 0
local musicToken = 0
local underwater: EqualizerSoundEffect

local function contentId(id: number): string
	return if id > 0 then "rbxassetid://" .. tostring(math.floor(id)) else ""
end

local function newSound(name: string, packId: number, group: SoundGroup, parent: Instance): Sound
	local s = Instance.new("Sound")
	s.Name = name
	s.SoundId = contentId(packId)
	s.SoundGroup = group
	s.PlaybackRegionsEnabled = true
	s.Looped = false
	s.Volume = 1
	s.Parent = parent
	return s
end

local function group(name: string): SoundGroup
	local g = SoundService:FindFirstChild(name)
	if g and g:IsA("SoundGroup") then
		return g
	end
	local created = Instance.new("SoundGroup")
	created.Name = name
	created.Parent = SoundService
	return created
end

function Audio.init()
	musicGroup = group("Music")
	voiceGroup = group("Voice")
	sfxGroup = group("SFX")
	local folder = Instance.new("Folder")
	folder.Name = "ClientAudio"
	folder.Parent = SoundService
	voiceSound = newSound("Voice", Config.VoicePackId, voiceGroup, folder)
	voiceSound.Volume = VOICE_LEVEL
	for i = 1, 2 do
		local m = newSound("Music" .. i, Config.MusicPackId, musicGroup, folder)
		m.Volume = 0
		table.insert(musicSounds, m)
	end
	for i = 1, SFX_COUNT do
		local s = newSound("Sfx" .. i, Config.SfxPackId, sfxGroup, folder)
		table.insert(sfxPool, s)
		sfxTokens[s] = 0
	end
	underwater = Instance.new("EqualizerSoundEffect")
	underwater.Name = "Underwater"
	underwater.LowGain = 2
	underwater.MidGain = -10
	underwater.HighGain = -30
	underwater.Enabled = false
	underwater.Parent = musicGroup
end

function Audio.hasVoice(): boolean
	return Config.VoicePackId > 0
end

-- ---------------------------------------------------------------------------- voice
function Audio.lineDuration(lineId: string): number
	local line = Content.Lines[lineId]
	return if line then math.max(line.stop - line.start, 0.5) else 0
end

-- Plays one of Brandon's lines. Returns its length in seconds (0 if unknown).
function Audio.playLine(lineId: string): number
	local line = Content.Lines[lineId]
	if not line then
		return 0
	end
	local duration = math.max(line.stop - line.start, 0.5)
	lineToken += 1
	local token = lineToken
	if voiceSound.SoundId ~= "" then
		voiceSound:Stop()
		voiceSound.PlaybackRegion = NumberRange.new(line.start, math.max(line.stop, line.start + 0.1))
		voiceSound.TimePosition = line.start
		voiceSound:Play()
		task.delay(duration + 0.2, function()
			if token == lineToken then
				voiceSound:Stop()
			end
		end)
	end
	return duration
end

function Audio.stopLine()
	lineToken += 1
	if voiceSound then
		voiceSound:Stop()
	end
end

-- ---------------------------------------------------------------------------- sfx
function Audio.playSfx(id: string, volume: number?, speed: number?)
	local region = Content.Sfx[id]
	if not region or #sfxPool == 0 or sfxPool[1].SoundId == "" then
		return
	end
	local sound: Sound? = nil
	for _ = 1, #sfxPool do
		local candidate = sfxPool[sfxNext]
		sfxNext = sfxNext % #sfxPool + 1
		if not candidate.IsPlaying then
			sound = candidate
			break
		end
	end
	local s = sound or sfxPool[sfxNext]
	local rate = speed or 1
	sfxTokens[s] += 1
	local token = sfxTokens[s]
	s:Stop()
	s.PlaybackSpeed = rate
	s.Volume = volume or 0.9
	s.PlaybackRegion = NumberRange.new(region.start, math.max(region.stop, region.start + 0.05))
	s.TimePosition = region.start
	s:Play()
	task.delay((region.stop - region.start) / rate + 0.15, function()
		if sfxTokens[s] == token then
			s:Stop()
		end
	end)
end

-- ---------------------------------------------------------------------------- music
local function musicTarget(): number
	return MUSIC_LEVEL * (if ducked then Config.MusicDuckWhileTalking else 1)
end

local function crossfadeTo(trackId: string)
	local track = Content.Music[trackId]
	if not track or #musicSounds < 2 or musicSounds[1].SoundId == "" then
		return
	end
	musicToken += 1
	local token = musicToken
	local outgoing = activeMusic
	local incoming = if outgoing == musicSounds[1] then musicSounds[2] else musicSounds[1]
	local fade = TweenInfo.new(Config.MusicCrossfadeSeconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
	incoming:Stop()
	incoming.Looped = track.loop
	incoming.PlaybackRegion = NumberRange.new(track.start, track.stop)
	incoming.LoopRegion = NumberRange.new(track.start, track.stop)
	incoming.TimePosition = track.start
	incoming.Volume = 0
	incoming:Play()
	TweenService:Create(incoming, fade, { Volume = musicTarget() }):Play()
	activeMusic = incoming
	if outgoing then
		TweenService:Create(outgoing, fade, { Volume = 0 }):Play()
		task.delay(Config.MusicCrossfadeSeconds + 0.1, function()
			if activeMusic ~= outgoing then
				outgoing:Stop()
			end
		end)
	end
	if not track.loop then
		task.delay(track.stop - track.start, function()
			local nextTrack = afterTrack
			if token == musicToken and nextTrack then
				afterTrack = nil
				currentTrack = nextTrack
				if musicEnabled then
					crossfadeTo(nextTrack)
				end
			end
		end)
	end
end

-- Switches the music (crossfade). thenTrack: what to play after a one-shot track.
function Audio.setMusic(trackId: string, thenTrack: string?)
	afterTrack = thenTrack
	if trackId == currentTrack and activeMusic and activeMusic.IsPlaying then
		return
	end
	currentTrack = trackId
	if musicEnabled then
		crossfadeTo(trackId)
	end
end

function Audio.setMusicEnabled(on: boolean)
	if musicEnabled == on then
		return
	end
	musicEnabled = on
	if on then
		if currentTrack then
			crossfadeTo(currentTrack)
		end
	else
		musicToken += 1
		for _, m in musicSounds do
			TweenService:Create(m, TweenInfo.new(0.6), { Volume = 0 }):Play()
		end
		local stopped = activeMusic
		activeMusic = nil
		task.delay(0.7, function()
			if stopped and activeMusic ~= stopped then
				stopped:Stop()
			end
		end)
	end
end

function Audio.isMusicEnabled(): boolean
	return musicEnabled
end

-- Lowers the music while Brandon is talking.
function Audio.setDuck(on: boolean)
	if ducked == on then
		return
	end
	ducked = on
	local m = activeMusic
	if m then
		TweenService:Create(m, TweenInfo.new(0.5), { Volume = musicTarget() }):Play()
	end
end

-- Player volume settings (0..1 each), through the SoundGroups.
function Audio.setVolumes(music: number, voice: number, sfx: number)
	musicGroup.Volume = math.clamp(music, 0, 1)
	voiceGroup.Volume = math.clamp(voice, 0, 1)
	sfxGroup.Volume = math.clamp(sfx, 0, 1)
end

function Audio.voiceVolume(): number
	return if voiceGroup then voiceGroup.Volume else 1
end

function Audio.setUnderwater(on: boolean)
	if underwater then
		underwater.Enabled = on
	end
end

return Audio
