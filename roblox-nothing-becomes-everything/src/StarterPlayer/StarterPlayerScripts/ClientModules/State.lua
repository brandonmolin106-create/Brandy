--!strict
-- StarterPlayerScripts > ClientModules > State  (ModuleScript)
-- The client's copy of the player's progress, pushed by the server.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local Progression = require(Shared:WaitForChild("Progression"))
local Signal = require(Shared:WaitForChild("Signal"))

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local GetState = Remotes:WaitForChild("GetState") :: RemoteFunction
local StateRemote = Remotes:WaitForChild("State") :: RemoteEvent
local SaveSettings = Remotes:WaitForChild("SaveSettings") :: RemoteEvent

local State = {}
State.Changed = Signal.new() :: Signal.Signal<Types.Snapshot>

local current: Types.Snapshot = {
	insights = {},
	settings = Types.defaultSettings(Config.DefaultMusicVolume, Config.DefaultVoiceVolume, Config.DefaultSfxVolume),
	persistent = true,
	auraOwned = false,
	auraOffered = false,
	tipOffered = false,
	tips = 0,
	finaleSeen = false,
	zone = "hub",
	zoneState = Types.newZoneState("hub"),
}

local function accept(raw: any)
	if type(raw) ~= "table" or type(raw.insights) ~= "table" or type(raw.settings) ~= "table" then
		return
	end
	current = raw :: Types.Snapshot
	State.Changed:Fire(current)
end

-- Fetches the first snapshot (retries until the server answers).
function State.init()
	StateRemote.OnClientEvent:Connect(accept)
	for attempt = 1, 10 do
		local ok, result = pcall(function()
			return GetState:InvokeServer()
		end)
		if ok and type(result) == "table" then
			accept(result)
			return
		end
		task.wait(math.min(attempt, 4))
	end
	warn("[State] could not get progress from the server; using defaults")
end

function State.get(): Types.Snapshot
	return current
end

function State.settings(): Types.Settings
	return current.settings
end

function State.isUnlocked(zone: string): boolean
	return Progression.isUnlocked(current.insights, zone)
end

function State.isCollected(zone: string): boolean
	return current.insights[zone] ~= nil
end

local saveQueued = false
-- Changes settings locally right away and saves them on the server shortly after.
function State.updateSettings(changes: { [string]: any })
	local s = table.clone(current.settings) :: any
	for k, v in changes do
		s[k] = v
	end
	current.settings = s :: Types.Settings
	State.Changed:Fire(current)
	if not saveQueued then
		saveQueued = true
		task.delay(1.5, function()
			saveQueued = false
			SaveSettings:FireServer(current.settings)
		end)
	end
end

return State
