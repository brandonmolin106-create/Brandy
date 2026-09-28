--!strict
-- StarterPlayerScripts > ClientModules > Zones > Hub  (ModuleScript)
-- The Clearing: shows each portal as locked / open / complete for THIS player,
-- keeps the stone map up to date, flickers the campfire, plays Brandon's welcome
-- the first time you arrive, and sparkles when someone tips.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Progression = require(Shared:WaitForChild("Progression"))
local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local State = require(Modules:WaitForChild("State"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))
local Theme = require(Modules:WaitForChild("Theme"))

local Hub = {}

local bin = ZoneContext.bin()
local welcomed = false

local LOCKED = Color3.fromRGB(70, 72, 90)

local function stylePortal(gate: Instance)
	if not gate:IsA("BasePart") then
		return
	end
	local zone = gate:GetAttribute("Zone")
	if type(zone) ~= "string" then
		return
	end
	local unlocked = State.isUnlocked(zone)
	local done = State.isCollected(zone)
	local color = Progression.color(zone)
	gate.Color = if unlocked then color else LOCKED
	gate.Transparency = if unlocked then 0.45 else 0.7
	for _, d in gate:GetChildren() do
		if d:IsA("ParticleEmitter") then
			d.Enabled = unlocked
		elseif d:IsA("PointLight") then
			d.Enabled = unlocked
		elseif d:IsA("ProximityPrompt") then
			d.ActionText = if unlocked then (if done then "Visit again" else "Enter") else "Locked"
		end
	end
	local status = gate:FindFirstChild("Status")
	local label = if status then status:FindFirstChild("State") else nil
	if label and label:IsA("TextLabel") then
		label.Text = if done then "\u{2713}  COMPLETE" elseif unlocked then "" else "LOCKED"
		label.TextColor3 = if done then Theme.Gold else Theme.White
	end
end

local function styleMap(tablet: Instance)
	local map = tablet:FindFirstChild("Map")
	if not map then
		return
	end
	for _, row in map:GetChildren() do
		local zone = string.match(row.Name, "^Row_(.+)$")
		local mark = row:FindFirstChild("Mark")
		if zone and mark and mark:IsA("TextLabel") then
			if zone == "hub" then
				mark.Text = "YOU ARE HERE"
				mark.TextColor3 = Theme.Cyan
			elseif State.isCollected(zone) then
				mark.Text = "\u{2713}"
				mark.TextColor3 = Theme.Gold
			elseif State.isUnlocked(zone) then
				mark.Text = "OPEN"
				mark.TextColor3 = Progression.color(zone)
			else
				mark.Text = "LOCKED"
				mark.TextColor3 = Theme.Dim
			end
		end
	end
end

local function refresh()
	for _, gate in CollectionService:GetTagged("Portal") do
		stylePortal(gate)
	end
	for _, tablet in CollectionService:GetTagged("MapTablet") do
		styleMap(tablet)
	end
end

function Hub.start(_ctx: ZoneContext.Context)
	refresh()
	bin:add(CollectionService:GetInstanceAddedSignal("Portal"):Connect(stylePortal))
	bin:add(CollectionService:GetInstanceAddedSignal("MapTablet"):Connect(styleMap))
	bin:add(State.Changed:Connect(refresh))

	-- campfire flicker
	local lights: { PointLight } = {}
	local function addFlicker(inst: Instance)
		local light = inst:FindFirstChild("FireLight")
		if light and light:IsA("PointLight") then
			table.insert(lights, light)
		end
	end
	for _, inst in CollectionService:GetTagged("Flicker") do
		addFlicker(inst)
	end
	bin:add(CollectionService:GetInstanceAddedSignal("Flicker"):Connect(addFlicker))
	local t = 0
	bin:add(RunService.Heartbeat:Connect(function(dt: number)
		t += dt
		local b = 2.2 + math.sin(t * 7.3) * 0.25 + math.sin(t * 13.1) * 0.15
		for _, light in lights do
			if light.Parent then
				light.Brightness = b
			end
		end
	end))

	if not welcomed then
		welcomed = true
		bin:add(task.delay(4.2, function()
			Voice.sayOnce("hub_welcome")
		end))
	end
end

function Hub.stop()
	bin:clean()
end

function Hub.onEvent(name: string, _data: { [string]: any })
	if name == "tip_thanks" then
		Audio.playSfx("collect", 0.9)
		for _, inst in CollectionService:GetTagged("Flicker") do
			local embers = inst:FindFirstChild("Embers")
			if embers and embers:IsA("ParticleEmitter") then
				embers:Emit(60)
			end
		end
	end
end

return Hub
