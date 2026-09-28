--!strict
-- ServerScriptService > Server  (Script)
-- Starts the server systems and connects remotes and proximity prompts.
-- Every request from a client is type-checked and rate-limited; the server decides.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ProximityPromptService = game:GetService("ProximityPromptService")

local Modules = script.Parent:WaitForChild("Modules")
local ProgressStore = require(Modules:WaitForChild("ProgressStore"))
local ZoneService = require(Modules:WaitForChild("ZoneService"))
local Purchases = require(Modules:WaitForChild("Purchases"))

local Progression = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Progression"))

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local GetState = Remotes:WaitForChild("GetState") :: RemoteFunction
local Travel = Remotes:WaitForChild("Travel") :: RemoteEvent
local ZoneAction = Remotes:WaitForChild("ZoneAction") :: RemoteEvent
local SaveSettings = Remotes:WaitForChild("SaveSettings") :: RemoteEvent
local ZoneEvent = Remotes:WaitForChild("ZoneEvent") :: RemoteEvent

-- ---------------------------------------------------------------------------- rate limits
type Bucket = { tokens: number, t: number }
local buckets: { [Player]: { [string]: Bucket } } = {}

local function allow(player: Player, key: string, perSecond: number, burst: number): boolean
	local mine = buckets[player]
	if not mine then
		mine = {}
		buckets[player] = mine
	end
	local now = os.clock()
	local b = mine[key]
	if not b then
		b = { tokens = burst, t = now }
		mine[key] = b
	end
	b.tokens = math.min(burst, b.tokens + (now - b.t) * perSecond)
	b.t = now
	if b.tokens < 1 then
		return false
	end
	b.tokens -= 1
	return true
end

-- ---------------------------------------------------------------------------- start
ProgressStore.start()
ZoneService.start()
Purchases.start({
	notify = ZoneService.notify,
	event = function(player: Player, name: string, data: { [string]: any })
		ZoneEvent:FireClient(player, name, data)
	end,
	pushState = ZoneService.pushState,
})

ProgressStore.Updated:Connect(function(player: Player)
	ZoneService.pushState(player)
end)

local function onPlayerAdded(player: Player)
	ZoneService.addPlayer(player)
	player.CharacterAdded:Connect(function(character: Model)
		character:WaitForChild("HumanoidRootPart", 10)
		Purchases.applyAura(player)
	end)
	Purchases.checkOwnership(player)
	local session = ProgressStore.load(player)
	if player.Parent then
		ZoneService.pushState(player)
		if not session.persistent then
			ZoneService.notify(player, "Progress isn't being saved in this session.")
		end
	end
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end
Players.PlayerRemoving:Connect(function(player: Player)
	ZoneService.removePlayer(player)
	buckets[player] = nil
end)

-- ---------------------------------------------------------------------------- remotes
GetState.OnServerInvoke = function(player: Player)
	ProgressStore.waitFor(player, 12)
	return ZoneService.snapshot(player)
end

Travel.OnServerEvent:Connect(function(player: Player, zone: any)
	if not allow(player, "travel", 0.5, 2) or not Progression.isZone(zone) then
		return
	end
	ZoneService.travel(player, zone)
end)

ZoneAction.OnServerEvent:Connect(function(player: Player, action: any, arg: any)
	if type(action) ~= "string" or #action > 16 or not allow(player, "action", 6, 10) then
		return
	end
	if arg ~= nil and type(arg) ~= "number" then
		return
	end
	ZoneService.action(player, action, arg)
end)

SaveSettings.OnServerEvent:Connect(function(player: Player, settings: any)
	if type(settings) ~= "table" or not allow(player, "settings", 1, 3) then
		return
	end
	if ProgressStore.setSettings(player, settings) then
		Purchases.applyAura(player)
	end
end)

-- ---------------------------------------------------------------------------- prompts
-- Prompts carry an "Action" attribute. Server actions are handled here; the others
-- (listen, journal, video, letgo, door) are purely client-side.
ProximityPromptService.PromptTriggered:Connect(function(prompt: ProximityPrompt, player: Player)
	if not allow(player, "prompt", 4, 6) then
		return
	end
	local action = prompt:GetAttribute("Action")
	local zone = prompt:GetAttribute("Zone")
	local index = prompt:GetAttribute("Index")
	if action == "portal" and type(zone) == "string" then
		ZoneService.travel(player, zone)
	elseif action == "return" then
		ZoneService.travel(player, "hub")
	elseif action == "insight" and type(zone) == "string" then
		ZoneService.collectInsight(player, zone)
	elseif action == "bell" and type(index) == "number" then
		ZoneService.ringBell(player, index)
	elseif action == "tip" then
		Purchases.promptTip(player)
	elseif action == "aura" then
		Purchases.promptAura(player)
	end
end)
