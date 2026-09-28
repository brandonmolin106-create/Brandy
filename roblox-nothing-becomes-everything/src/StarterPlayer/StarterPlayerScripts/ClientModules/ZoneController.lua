--!strict
-- StarterPlayerScripts > ClientModules > ZoneController  (ModuleScript)
-- Runs the zone the player is in: clones this player's zone kit (steps, blocks,
-- water, the wall, clock hands...) into a local folder, animates it, switches the
-- lighting, music and video screen, shows the intro card, starts the zone's module
-- and passes it the server's zone events. Also handles Insights and story beats.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")
local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local Progression = require(Shared:WaitForChild("Progression"))

local ZoneContext = require(script.Parent:WaitForChild("ZoneContext"))
local State = require(script.Parent:WaitForChild("State"))
local HUD = require(script.Parent:WaitForChild("HUD"))
local Audio = require(script.Parent:WaitForChild("Audio"))
local Voice = require(script.Parent:WaitForChild("Voice"))
local LightingFX = require(script.Parent:WaitForChild("LightingFX"))
local Videos = require(script.Parent:WaitForChild("Videos"))
local Kinetics = require(script.Parent:WaitForChild("Kinetics"))
local Theme = require(script.Parent:WaitForChild("Theme"))

local Zones = script.Parent:WaitForChild("Zones")
local modules: { [string]: ZoneContext.Module } = {
	hub = require(Zones:WaitForChild("Hub")),
	time = require(Zones:WaitForChild("Time")),
	hole = require(Zones:WaitForChild("Hole")),
	glass = require(Zones:WaitForChild("Glass")),
	road = require(Zones:WaitForChild("Road")),
	chains = require(Zones:WaitForChild("Chains")),
	everything = require(Zones:WaitForChild("Summit")),
}

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local ZoneEvent = Remotes:WaitForChild("ZoneEvent") :: RemoteEvent
local ZoneAction = Remotes:WaitForChild("ZoneAction") :: RemoteEvent
local Travel = Remotes:WaitForChild("Travel") :: RemoteEvent

local ZoneController = {}

local currentZone: string? = nil
local current: ZoneContext.Module? = nil
local kitClone: Instance? = nil
local unbindKinetics: (() -> ())? = nil
local zoneFolder: Folder
local beatConnection: RBXScriptConnection? = nil
local travelToken = 0
local visits: { [string]: number } = {}

local function root(): BasePart?
	local character = (Players.LocalPlayer :: Player).Character
	local r = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if r and r:IsA("BasePart") then r else nil
end

local function action(name: string, arg: number?)
	ZoneAction:FireServer(name, arg)
end

local function fadeWithTimeout()
	travelToken += 1
	local my = travelToken
	HUD.fade(true, 0.35)
	Audio.playSfx("portal", 0.8)
	task.delay(6, function()
		if travelToken == my then
			HUD.fade(false, 0.5) -- the server said no (e.g. a locked zone)
		end
	end)
end

-- Ask the server to take the player somewhere (Return button, the finale portal).
function ZoneController.travel(zone: string)
	if zone == currentZone and zone == "hub" then
		return
	end
	fadeWithTimeout()
	Travel:FireServer(zone)
end

-- The server is handling a portal prompt: just fade.
function ZoneController.expectTravel()
	fadeWithTimeout()
end

function ZoneController.folder(): Folder
	return zoneFolder
end

function ZoneController.zone(): string?
	return currentZone
end

-- ---------------------------------------------------------------------------- insights
local function styleInsight(inst: Instance)
	if not inst:IsA("BasePart") then
		return
	end
	local zone = inst:GetAttribute("Zone")
	if type(zone) ~= "string" then
		return
	end
	local collected = State.isCollected(zone)
	local prompt = inst:FindFirstChildOfClass("ProximityPrompt")
	if prompt then
		prompt.ActionText = if collected then "Hear it again" else "Collect Insight"
	end
	inst.Color = if collected then Theme.Gold else Progression.color(zone)
end

local function styleAllInsights()
	for _, inst in CollectionService:GetTagged("Insight") do
		styleInsight(inst)
	end
end

local function onInsight(data: { [string]: any })
	local zone = data.zone
	if type(zone) ~= "string" then
		return
	end
	local z = Progression.zone(zone)
	if not z then
		return
	end
	Audio.playSfx("zone_complete", 0.9)
	HUD.insightCard(zone, z.insight or "")
	local line = z.insightLine
	if line and not Voice.playedWithin(line, 45) then
		Voice.say(line, true)
	end
	local nextZone = data.nextZone
	if data.first == true and type(nextZone) == "string" then
		task.delay(7.5, function()
			HUD.toast("New zone open: " .. Progression.name(nextZone), Progression.color(nextZone))
		end)
	end
	if zone ~= "everything" then
		task.delay(9, function()
			if currentZone == zone then
				HUD.toast("Return to the Clearing whenever you're ready.")
			end
		end)
	end
	styleAllInsights()
end

-- ---------------------------------------------------------------------------- story beats
-- BeatMarker parts in the kit auto-play their line once when the player comes near.
local function startBeats(kit: Instance)
	local markers: { { part: BasePart, line: string, radius: number } } = {}
	for _, d in kit:GetDescendants() do
		local line = d:GetAttribute("LineId")
		local radius = d:GetAttribute("Radius")
		if d:IsA("BasePart") and d.Name == "BeatMarker" and type(line) == "string" and type(radius) == "number" then
			table.insert(markers, { part = d, line = line, radius = radius })
		end
	end
	if #markers == 0 then
		return
	end
	local last = 0
	beatConnection = RunService.Heartbeat:Connect(function()
		if os.clock() - last < 0.25 then
			return
		end
		last = os.clock()
		local r = root()
		if not r then
			return
		end
		for _, m in markers do
			if (r.Position - m.part.Position).Magnitude <= m.radius then
				Voice.sayOnce(m.line)
			end
		end
	end)
end

-- ---------------------------------------------------------------------------- zones
function ZoneController.enter(zone: string, state: Types.ZoneState)
	travelToken += 1
	local previous = current
	if previous then
		local ok, err = pcall(function()
			previous.stop()
		end)
		if not ok then
			warn("[ZoneController] stop failed:", err)
		end
	end
	current = nil
	if unbindKinetics then
		unbindKinetics()
		unbindKinetics = nil
	end
	if beatConnection then
		beatConnection:Disconnect()
		beatConnection = nil
	end
	if kitClone then
		kitClone:Destroy()
		kitClone = nil
	end
	local fromZone = currentZone
	currentZone = zone
	visits[zone] = (visits[zone] or 0) + 1

	local source = ReplicatedStorage:WaitForChild("ZoneKits"):FindFirstChild(zone)
	if source then
		local clone = source:Clone()
		clone.Parent = zoneFolder
		kitClone = clone
		unbindKinetics = Kinetics.bind(clone)
		startBeats(clone)
	end

	LightingFX.apply(zone)
	local z = Progression.zone(zone)
	if z then
		Audio.setMusic(z.music)
	end
	Videos.setZone(zone)
	HUD.setZone(zone)
	HUD.setProgress(State.get())
	HUD.arrive(0.9) -- from black, even when the server moved us (walking into a portal)
	if zone ~= "hub" or fromZone ~= nil or visits.hub == 1 then
		task.delay(0.3, function()
			if currentZone == zone then
				HUD.zoneCard(zone)
				Audio.playSfx("whoosh", 0.6)
			end
		end)
	end
	styleAllInsights()

	local module = modules[zone]
	if module then
		current = module
		local ctx: ZoneContext.Context = {
			zone = zone,
			kit = kitClone,
			state = state,
			action = action,
			travel = ZoneController.travel,
			root = root,
		}
		task.spawn(function()
			local ok, err = pcall(function()
				module.start(ctx)
			end)
			if not ok then
				warn("[ZoneController] " .. zone .. " failed to start:", err)
			end
		end)
	end
end

function ZoneController.forward(name: string, data: { [string]: any })
	local module = current
	if module then
		task.spawn(module.onEvent, name, data)
	end
end

function ZoneController.init()
	zoneFolder = Instance.new("Folder")
	zoneFolder.Name = "ClientZone"
	zoneFolder.Parent = Workspace

	for _, inst in CollectionService:GetTagged("Insight") do
		styleInsight(inst)
	end
	CollectionService:GetInstanceAddedSignal("Insight"):Connect(styleInsight)
	State.Changed:Connect(function()
		styleAllInsights()
	end)

	ZoneEvent.OnClientEvent:Connect(function(name: any, data: any)
		if type(name) ~= "string" then
			return
		end
		local payload: { [string]: any } = if type(data) == "table" then data else {}
		if name == "enter" then
			local zone = payload.zone
			local state = payload.state
			if Progression.isZone(zone) and type(state) == "table" then
				ZoneController.enter(zone, state :: Types.ZoneState)
			end
		elseif name == "insight" then
			onInsight(payload)
			ZoneController.forward(name, payload)
		else
			ZoneController.forward(name, payload)
		end
	end)
end

return ZoneController
