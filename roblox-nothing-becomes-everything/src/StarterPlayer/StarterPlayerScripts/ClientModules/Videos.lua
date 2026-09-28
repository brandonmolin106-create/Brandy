--!strict
-- StarterPlayerScripts > ClientModules > Videos  (ModuleScript)
-- The video manager. Only the screen in the player's current zone may play; every
-- other screen is paused and unloaded (Roblox allows at most 2 videos playing at
-- once; this game never plays more than 1). PolicyService decides autoplay:
-- if endless autoplay isn't allowed, the screen waits for "Play video" and plays once.
-- With a video id of 0 the screen keeps its "Brandon's video goes here" panel.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local PlayerPolicy = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("PlayerPolicy"))
local Audio = require(script.Parent:WaitForChild("Audio"))

local Videos = {}

local MAX_PLAYING = 2
local currentZone = "hub"
local autoplay = false
local talking = false
local frames: { [VideoFrame]: boolean } = {}

local function videoId(frame: VideoFrame): number
	local key = frame:GetAttribute("VideoKey")
	local id = if type(key) == "string" then Config.Videos[key] else nil
	return if type(id) == "number" then id else 0
end

local function zoneOf(inst: Instance): string?
	local z = inst:GetAttribute("Zone")
	return if type(z) == "string" then z else nil
end

local function placeholder(frame: VideoFrame): GuiObject?
	local parent = frame.Parent
	local ph = if parent then parent:FindFirstChild("Placeholder") else nil
	return if ph and ph:IsA("GuiObject") then ph else nil
end

local function volume(): number
	return Config.VideoVolume * Audio.voiceVolume() * (if talking then 0.3 else 1)
end

local function playingCount(): number
	local n = 0
	for frame in frames do
		if frame.Playing then
			n += 1
		end
	end
	return n
end

local function unload(frame: VideoFrame)
	if frame.Playing then
		frame:Pause()
	end
	if frame.Video ~= "" then
		frame.Video = ""
	end
	frame.Visible = false
	local ph = placeholder(frame)
	if ph then
		ph.Visible = true
	end
end

local function refresh(frame: VideoFrame)
	local id = videoId(frame)
	if zoneOf(frame) ~= currentZone or id <= 0 then
		unload(frame)
		return
	end
	local content = "rbxassetid://" .. tostring(id)
	if frame.Video ~= content then
		frame.Video = content
	end
	frame.Visible = true
	frame.Looped = autoplay
	frame.Volume = volume()
	local ph = placeholder(frame)
	if ph then
		ph.Visible = not frame.IsLoaded -- keep the panel up until the video has loaded
	end
	if autoplay and not frame.Playing and playingCount() < MAX_PLAYING then
		frame:Play()
	end
end

local function track(inst: Instance)
	if not inst:IsA("VideoFrame") then
		return
	end
	local frame = inst
	frames[frame] = true
	frame.Loaded:Connect(function()
		local ph = placeholder(frame)
		if ph and frame.Visible then
			ph.Visible = false
		end
	end)
	frame.Ended:Connect(function()
		if not autoplay then
			frame.TimePosition = 0
		end
	end)
	refresh(frame)
end

local function untrack(inst: Instance)
	if inst:IsA("VideoFrame") then
		frames[inst] = nil
	end
end

-- Hide the "Play video" prompt of screens that have no video yet.
local function syncPrompt(prompt: ProximityPrompt)
	if prompt:GetAttribute("Action") ~= "video" then
		return
	end
	local zone = zoneOf(prompt)
	local id = if zone then Config.Videos[zone] else nil
	prompt.Enabled = type(id) == "number" and id > 0
	prompt.ActionText = if autoplay then "Watch from the start" else "Play video"
end

function Videos.init()
	autoplay = PlayerPolicy.autoplayAllowed(Config.AlwaysAutoplayInStudio)
	for _, inst in CollectionService:GetTagged("ZoneScreen") do
		track(inst)
	end
	CollectionService:GetInstanceAddedSignal("ZoneScreen"):Connect(track)
	CollectionService:GetInstanceRemovedSignal("ZoneScreen"):Connect(untrack)
	local function scan(inst: Instance)
		if inst:IsA("ProximityPrompt") then
			syncPrompt(inst)
		end
	end
	for _, d in workspace:GetDescendants() do
		scan(d)
	end
	workspace.DescendantAdded:Connect(scan)
	-- keep the volume in step with the Voice slider and with Brandon talking
	local last = 0
	RunService.Heartbeat:Connect(function()
		if os.clock() - last < 0.5 then
			return
		end
		last = os.clock()
		for frame in frames do
			if frame.Visible then
				frame.Volume = volume()
			end
		end
	end)
end

function Videos.setZone(zone: string)
	currentZone = zone
	for frame in frames do
		refresh(frame)
	end
end

function Videos.setTalking(on: boolean)
	talking = on
end

-- "Play video" on a screen's console: play from the start (once if no autoplay).
function Videos.playRequested(zone: string)
	for frame in frames do
		if zoneOf(frame) == zone and videoId(frame) > 0 then
			currentZone = zone
			refresh(frame)
			frame.Looped = autoplay
			frame.TimePosition = 0
			if playingCount() < MAX_PLAYING or frame.Playing then
				frame:Play()
			end
		end
	end
end

return Videos
