--!strict
-- ServerScriptService > Modules > ZoneService  (ModuleScript)
-- The server owns the story state: which zone each player is in, their checkpoint,
-- the puzzle progress inside the zone (Hole orbs, Glass Box blocks, Chains bells),
-- and Insight collection. Clients only draw what the server confirms.
-- Positions used for validation come from the zone kits in ReplicatedStorage and
-- from the Workspace (the server always has every part, streaming only affects clients).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local Progression = require(Shared:WaitForChild("Progression"))

local ProgressStore = require(script.Parent:WaitForChild("ProgressStore"))
local Badges = require(script.Parent:WaitForChild("Badges"))
local Chains = require(script.Parent:WaitForChild("Chains"))

local Remotes = ReplicatedStorage:WaitForChild("Remotes")
local ZoneEventRemote = Remotes:WaitForChild("ZoneEvent") :: RemoteEvent
local StateRemote = Remotes:WaitForChild("State") :: RemoteEvent
local NotifyRemote = Remotes:WaitForChild("Notify") :: RemoteEvent

type PlayerData = {
	zone: string,
	state: Types.ZoneState,
	checkpoint: CFrame,
	checkpointIndex: number,
	traveling: boolean,
	token: number, -- changes on every zone change; stale timelines stop
	dropTimes: { [number]: number },
	lastNotice: number,
	lastTouchTravel: number,
}

local ZoneService = {}

local players: { [Player]: PlayerData } = {}
local spawnPads: { [string]: BasePart } = {}
local insightParts: { [string]: BasePart } = {}
local holeOrbs: { Vector3 } = {}
local pitCenter = Vector3.zero
local glassBlocks: { [number]: Vector3 } = {}
local glassBlockCount = 0
local glassDoor: Vector3? = nil
local glassDoorwayZ = math.huge

-- ---------------------------------------------------------------------------- helpers
local function rootOf(player: Player): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if root and root:IsA("BasePart") then root else nil
end

-- Highest point of a part, whatever its rotation.
local function topOf(part: BasePart): number
	local cf, s = part.CFrame, part.Size
	local r = cf.RightVector
	local u = cf.UpVector
	local b = -cf.LookVector
	return part.Position.Y + math.abs(r.Y) * s.X / 2 + math.abs(u.Y) * s.Y / 2 + math.abs(b.Y) * s.Z / 2
end

-- Where a character stands on a pad: 3.2 studs above its top, facing the pad's front.
local function standOn(pad: BasePart): CFrame
	local pos = Vector3.new(pad.Position.X, topOf(pad) + 3.2, pad.Position.Z)
	local look = pad.CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	if flat.Magnitude < 0.01 then
		flat = Vector3.new(0, 0, -1)
	end
	return CFrame.lookAt(pos, pos + flat.Unit)
end

local function send(player: Player, name: string, data: { [string]: any })
	ZoneEventRemote:FireClient(player, name, data)
end

function ZoneService.notify(player: Player, text: string)
	NotifyRemote:FireClient(player, text)
end

local function noticeOnce(player: Player, text: string)
	local data = players[player]
	if data and os.clock() - data.lastNotice > 3 then
		data.lastNotice = os.clock()
		ZoneService.notify(player, text)
	end
end

function ZoneService.snapshot(player: Player): Types.Snapshot
	local data = players[player]
	local session = ProgressStore.get(player)
	local defaults = Types.defaultSettings(Config.DefaultMusicVolume, Config.DefaultVoiceVolume, Config.DefaultSfxVolume)
	local profile = if session then session.profile else nil
	return {
		insights = if profile then table.clone(profile.insights) else {},
		settings = if profile then table.clone(profile.settings) else defaults,
		persistent = session ~= nil and session.persistent,
		auraOwned = player:GetAttribute("AuraOwned") == true,
		auraOffered = Config.GamePassId > 0,
		tipOffered = (Config.DevProductIds.TipBrandon or 0) > 0,
		tips = if profile then profile.tips else 0,
		finaleSeen = if profile then profile.finaleSeen else false,
		zone = if data then data.zone else "hub",
		zoneState = if data then data.state else Types.newZoneState("hub"),
	}
end

function ZoneService.pushState(player: Player)
	StateRemote:FireClient(player, ZoneService.snapshot(player))
end

local function moveCharacter(player: Player, cf: CFrame)
	pcall(function()
		player:RequestStreamAroundAsync(cf.Position, 4)
	end)
	local character = player.Character
	if character then
		character:PivotTo(cf)
		local root = rootOf(player)
		if root then
			root.AssemblyLinearVelocity = Vector3.zero
			root.AssemblyAngularVelocity = Vector3.zero
		end
	end
end

-- ---------------------------------------------------------------------------- zones
local function startGlassTimeline(player: Player, data: PlayerData)
	local token = data.token
	task.spawn(function()
		task.wait(Config.GlassFirstDropSeconds)
		for i = 1, glassBlockCount do
			if players[player] ~= data or data.token ~= token or data.state.exited then
				return
			end
			data.state.dropped = i
			table.insert(data.state.present, i)
			data.dropTimes[i] = os.clock()
			send(player, "glass_drop", { index = i, present = table.clone(data.state.present) })
			task.wait(Config.GlassDropIntervalSeconds)
		end
	end)
end

local function leaveZone(player: Player, data: PlayerData)
	if data.zone == "chains" then
		Chains.reset(player)
	end
end

local function enterZone(player: Player, data: PlayerData)
	if data.zone == "chains" then
		Chains.reset(player)
	elseif data.zone == "glass" then
		startGlassTimeline(player, data)
	end
end

function ZoneService.travel(player: Player, zone: string)
	local data = players[player]
	if not data or data.traveling or not Progression.isZone(zone) then
		return
	end
	local session = ProgressStore.get(player)
	local insights = if session then session.profile.insights else {}
	if not Progression.isUnlocked(insights, zone) then
		local i = Progression.index(zone)
		local previous = Progression.Journey[i - 1]
		noticeOnce(player, `{Progression.name(zone)} opens after you collect the Insight in {Progression.name(previous or "hub")}.`)
		return
	end
	local pad = spawnPads[zone]
	if not pad then
		warn("[ZoneService] no arrival pad for zone " .. zone)
		return
	end
	data.traveling = true
	leaveZone(player, data)
	data.zone = zone
	data.token += 1
	data.state = Types.newZoneState(zone)
	data.dropTimes = {}
	data.checkpoint = standOn(pad)
	data.checkpointIndex = 0
	player:SetAttribute("Zone", zone)
	moveCharacter(player, data.checkpoint)
	enterZone(player, data)
	send(player, "enter", { zone = zone, state = data.state })
	data.traveling = false
end

-- ---------------------------------------------------------------------------- actions
function ZoneService.action(player: Player, action: string, arg: any)
	local data = players[player]
	local root = rootOf(player)
	if not data or data.traveling or not root then
		return
	end
	local state = data.state
	local index = tonumber(arg)
	if action == "orb" and data.zone == "hole" and index then
		if index ~= state.orbs + 1 or index > #holeOrbs then
			return
		end
		local pos = holeOrbs[index]
		if (root.Position - pos).Magnitude > 12 then
			return
		end
		state.orbs = index
		local stand = Vector3.new(pos.X, pos.Y - 0.2, pos.Z)
		data.checkpoint = CFrame.lookAt(stand, Vector3.new(pitCenter.X, stand.Y, pitCenter.Z))
		data.checkpointIndex = index
		send(player, "hole_orb", { count = index })
	elseif action == "letgo" and data.zone == "glass" and index then
		local at = table.find(state.present, index)
		local pos = glassBlocks[index]
		if not at or not pos then
			return
		end
		local dropped = data.dropTimes[index]
		if dropped and os.clock() - dropped < 1 then
			return -- still falling
		end
		if (root.Position - pos).Magnitude > 18 then
			return
		end
		table.remove(state.present, at)
		send(player, "glass_letgo", { index = index, remaining = #state.present, present = table.clone(state.present) })
	elseif action == "door" and data.zone == "glass" then
		if state.door then
			return
		end
		local door = glassDoor
		if door and (root.Position - door).Magnitude > 16 then
			return
		end
		state.door = true
		send(player, "glass_door", {})
	elseif action == "exit" and data.zone == "glass" then
		if not state.door or state.exited or root.Position.Z > glassDoorwayZ + 2 then
			return
		end
		state.exited = true
		send(player, "glass_exit", {})
	end
end

function ZoneService.ringBell(player: Player, index: number)
	local data = players[player]
	if data and data.zone == "chains" and not data.traveling then
		Chains.ring(player, data.state, index)
	end
end

function ZoneService.collectInsight(player: Player, zone: string)
	local data = players[player]
	local root = rootOf(player)
	local part = insightParts[zone]
	if not data or not root or not part or data.zone ~= zone or not Progression.isJourneyZone(zone) then
		return
	end
	if (root.Position - part.Position).Magnitude > 18 then
		return
	end
	local state = data.state
	if zone == "hole" and state.orbs < #holeOrbs then
		noticeOnce(player, "Collect every Better Thought first.")
		return
	elseif zone == "glass" and not (state.door or state.exited) then
		noticeOnce(player, "Find the way out of the glass box first.")
		return
	elseif zone == "chains" and not state.broken then
		noticeOnce(player, "Ring the three I CAN bells first.")
		return
	end
	if not ProgressStore.waitFor(player, 8) then
		return
	end
	local first, t = ProgressStore.collectInsight(player, zone)
	if first then
		Badges.award(player, zone)
	end
	send(player, "insight", { zone = zone, first = first, time = t, nextZone = Progression.nextZone(zone) })
	if zone == "everything" and not state.finale then
		state.finale = true
		ProgressStore.setFinaleSeen(player)
		Badges.award(player, "finale")
		send(player, "finale", { first = first })
	end
	ZoneService.pushState(player)
end

-- ---------------------------------------------------------------------------- players
function ZoneService.addPlayer(player: Player)
	local hubPad = spawnPads.hub
	local data: PlayerData = {
		zone = "hub",
		state = Types.newZoneState("hub"),
		checkpoint = if hubPad then standOn(hubPad) else CFrame.new(0, 5, 30),
		checkpointIndex = 0,
		traveling = false,
		token = 0,
		dropTimes = {},
		lastNotice = 0,
		lastTouchTravel = 0,
	}
	players[player] = data
	player:SetAttribute("Zone", "hub")
	local function onCharacter(character: Model)
		if players[player] ~= data then
			return
		end
		Chains.onCharacter(player, data.state)
		send(player, "respawn", { zone = data.zone, state = data.state })
		if data.zone == "hub" then
			return -- the SpawnLocation already put them in the Clearing
		end
		task.defer(function()
			local root = character:WaitForChild("HumanoidRootPart", 10)
			if root and players[player] == data and player.Character == character then
				moveCharacter(player, data.checkpoint)
			end
		end)
	end
	player.CharacterAdded:Connect(onCharacter)
	if player.Character then
		task.spawn(onCharacter, player.Character)
	end
end

function ZoneService.removePlayer(player: Player)
	players[player] = nil
	Badges.forget(player)
end

function ZoneService.zoneOf(player: Player): string
	local data = players[player]
	return if data then data.zone else "hub"
end

local function onCheckpointTouched(pad: BasePart, zone: string, index: number, hit: BasePart)
	local model = hit:FindFirstAncestorOfClass("Model")
	local player = if model then Players:GetPlayerFromCharacter(model) else nil
	local data = if player then players[player] else nil
	if not data or data.zone ~= zone or data.traveling or index < data.checkpointIndex then
		return
	end
	data.checkpoint = standOn(pad)
	data.checkpointIndex = index
end

local function onPortalTouched(gate: BasePart, hit: BasePart)
	local zone = gate:GetAttribute("Zone")
	local model = hit:FindFirstAncestorOfClass("Model")
	local player = if model then Players:GetPlayerFromCharacter(model) else nil
	local data = if player then players[player] else nil
	if not player or not data or type(zone) ~= "string" or data.zone ~= "hub" then
		return
	end
	if os.clock() - data.lastTouchTravel < 2 then
		return
	end
	data.lastTouchTravel = os.clock()
	task.spawn(ZoneService.travel, player, zone)
end

-- ---------------------------------------------------------------------------- start
function ZoneService.start()
	for _, inst in CollectionService:GetTagged("Checkpoint") do
		local zone = inst:GetAttribute("Zone")
		local index = inst:GetAttribute("Index")
		if inst:IsA("BasePart") and type(zone) == "string" and type(index) == "number" then
			if index == 0 then
				spawnPads[zone] = inst
			end
			inst.Touched:Connect(function(hit)
				onCheckpointTouched(inst, zone, index, hit)
			end)
		end
	end
	for _, inst in CollectionService:GetTagged("Insight") do
		local zone = inst:GetAttribute("Zone")
		if inst:IsA("BasePart") and type(zone) == "string" then
			insightParts[zone] = inst
		end
	end
	for _, inst in CollectionService:GetTagged("Portal") do
		if inst:IsA("BasePart") then
			inst.Touched:Connect(function(hit)
				onPortalTouched(inst, hit)
			end)
		end
	end
	local kits = ReplicatedStorage:WaitForChild("ZoneKits")
	local hole = kits:WaitForChild("hole")
	local center = hole:GetAttribute("PitCenter")
	if typeof(center) == "Vector3" then
		pitCenter = center
	end
	local orbs = hole:FindFirstChild("Orbs")
	if orbs then
		for k = 1, 99 do
			local orb = orbs:FindFirstChild("Orb" .. k)
			local core = if orb then orb:FindFirstChild("Core") else nil
			if not core or not core:IsA("BasePart") then
				break
			end
			holeOrbs[k] = core.Position
		end
	end
	local glass = kits:WaitForChild("glass")
	local blocks = glass:FindFirstChild("Blocks")
	if blocks then
		for _, b in blocks:GetChildren() do
			local i = b:GetAttribute("Index")
			if b:IsA("BasePart") and type(i) == "number" then
				glassBlocks[i] = b.Position
				glassBlockCount = math.max(glassBlockCount, i)
			end
		end
	end
	local door = glass:FindFirstChild("Door")
	local leaf = if door then door:FindFirstChild("DoorLeaf") else nil
	if leaf and leaf:IsA("BasePart") then
		glassDoor = leaf.Position
	end
	local doorway = glass:GetAttribute("DoorwayZ")
	if type(doorway) == "number" then
		glassDoorwayZ = doorway
	end
	Chains.init(send)

	-- fall safety + chains polling
	task.spawn(function()
		while true do
			task.wait(0.2)
			for player, data in players do
				local root = rootOf(player)
				if root and not data.traveling then
					local cp = data.checkpoint.Position
					local v = root.AssemblyLinearVelocity.Y
					if (root.Position.Y < cp.Y - 14 and v < -70) or root.Position.Y < -160 then
						moveCharacter(player, data.checkpoint)
					elseif data.zone == "chains" then
						Chains.poll(player, data.state)
					end
				end
			end
		end
	end)
end

return ZoneService
