--!strict
-- StarterPlayerScripts > Client  (LocalScript)
-- Starts every client system: progress, sound, captions, HUD, journal, settings,
-- lighting, video screens, prompts and the current zone.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local PlayerPolicy = require(Shared:WaitForChild("PlayerPolicy"))

local Modules = script.Parent:WaitForChild("ClientModules")
local State = require(Modules:WaitForChild("State"))
local UIKit = require(Modules:WaitForChild("UIKit"))
local Audio = require(Modules:WaitForChild("Audio"))
local Captions = require(Modules:WaitForChild("Captions"))
local Voice = require(Modules:WaitForChild("Voice"))
local HUD = require(Modules:WaitForChild("HUD"))
local Journal = require(Modules:WaitForChild("Journal"))
local SettingsMenu = require(Modules:WaitForChild("SettingsMenu"))
local LightingFX = require(Modules:WaitForChild("LightingFX"))
local Videos = require(Modules:WaitForChild("Videos"))
local Interactions = require(Modules:WaitForChild("Interactions"))
local ZoneController = require(Modules:WaitForChild("ZoneController"))

local Notify = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("Notify") :: RemoteEvent

local function click()
	Audio.playSfx("ui_click", 0.6)
end

-- ---------------------------------------------------------------------------- systems
Audio.init()
Captions.init()
LightingFX.init()
HUD.init({
	onJournal = function()
		click()
		Journal.open()
	end,
	onSettings = function()
		click()
		SettingsMenu.open()
	end,
	onReturn = function()
		click()
		ZoneController.travel("hub")
	end,
	onMusic = function()
		click()
		Audio.setMusicEnabled(true)
		HUD.showMusicButton(false)
	end,
})
Journal.init(function(lineId: string)
	Voice.say(lineId, true)
end, click)
SettingsMenu.init(function(key: string, value: any)
	State.updateSettings({ [key] = value })
end, click)
Interactions.init()
ZoneController.init()

Notify.OnClientEvent:Connect(function(text: any)
	if type(text) == "string" then
		HUD.toast(text)
	end
end)

Voice.Started:Connect(function()
	Videos.setTalking(true)
end)
Voice.Finished:Connect(function()
	if Voice.current() == nil then
		Videos.setTalking(false)
	end
end)

-- ---------------------------------------------------------------------------- settings
local function apply(snapshot: Types.Snapshot)
	local s = snapshot.settings
	Audio.setVolumes(s.music, s.voice, s.sfx)
	Captions.setEnabled(s.captions)
	UIKit.reduceMotion = s.reduceMotion
	HUD.setProgress(snapshot)
	Journal.refresh(snapshot)
	SettingsMenu.refresh(snapshot)
end

State.Changed:Connect(apply)
State.init()
apply(State.get())

-- Music may start by itself only where Roblox allows endless autoplay; elsewhere the
-- player taps "Play music". Videos follow the same rule (see Videos).
Audio.setMusicEnabled(false) -- until the policy answers
task.spawn(function()
	local allowed = PlayerPolicy.autoplayAllowed(Config.AlwaysAutoplayInStudio)
	Audio.setMusicEnabled(allowed)
	HUD.showMusicButton(not allowed and Config.MusicPackId > 0)
end)
task.spawn(Videos.init)

-- Start the first zone once the loading screen has gone, so its intro card is seen.
local playerGui = (Players.LocalPlayer :: Player):WaitForChild("PlayerGui")
local deadline = os.clock() + 20
while playerGui:FindFirstChild("LoadingScreen") and os.clock() < deadline do
	task.wait(0.2)
end
local snapshot = State.get()
ZoneController.enter(snapshot.zone, snapshot.zoneState)
