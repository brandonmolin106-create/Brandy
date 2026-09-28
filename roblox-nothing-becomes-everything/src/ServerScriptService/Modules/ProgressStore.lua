--!strict
-- ServerScriptService > Modules > ProgressStore  (ModuleScript)
-- Saves each player's journey with DataStoreService.
--
--  * Every call is wrapped in pcall and retried with a growing wait.
--  * Saving uses UpdateAsync with a MERGE: collected Insights are a union (earliest
--    date wins), purchase receipts are a union, settings are last-writer-wins. So two
--    servers saving at once, or a save after a failed load, can never erase progress.
--  * If data stores can't be used at all (Studio without "Enable Studio Access to API
--    Services", or a place that was never published) the game keeps working with
--    in-memory progress and tells the client (persistent = false).

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local Progression = require(Shared:WaitForChild("Progression"))
local Signal = require(Shared:WaitForChild("Signal"))

export type Profile = {
	version: number,
	insights: { [string]: number },
	settings: Types.Settings,
	settingsUpdated: number,
	tips: number,
	receipts: { [string]: number },
	finaleSeen: boolean,
	firstJoin: number,
	visits: number,
}

export type Session = {
	player: Player,
	profile: Profile,
	loaded: boolean, -- loading finished (with data or with the fallback)
	persistent: boolean, -- data stores usable for this player
	loadFailed: boolean, -- live outage: keep retrying the load in the background
	dirty: boolean,
	settingsChanged: boolean,
	pendingReceipts: { [string]: number }, -- granted this session, not yet confirmed saved
	saving: boolean,
	lastSave: number,
}

local ProgressStore = {}
ProgressStore.Loaded = Signal.new() :: Signal.Signal<Player, Session>
ProgressStore.Updated = Signal.new() :: Signal.Signal<Player>

local VERSION = 1
local MAX_RECEIPTS = 100
local AUTOSAVE_SECONDS = 90

local sessions: { [Player]: Session } = {}
local store: DataStore? = nil
local storeDisabledReason: string? = nil

local function isAccessError(message: string): boolean
	local m = string.lower(message)
	return string.find(m, "studioaccesstoapisnotallowed", 1, true) ~= nil
		or string.find(m, "403", 1, true) ~= nil
		or string.find(m, "publish", 1, true) ~= nil
		or string.find(m, "not allowed", 1, true) ~= nil
		or string.find(m, "api services", 1, true) ~= nil
end

local function disableStore(reason: string)
	if storeDisabledReason == nil then
		storeDisabledReason = reason
		warn("[ProgressStore] Progress will not be saved this session: " .. reason)
		if RunService:IsStudio() then
			warn("[ProgressStore] To test saving in Studio: Game Settings > Security > Enable Studio Access to API Services (use a test copy of the game).")
		end
	end
end

do
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(Config.DataStoreName)
	end)
	if ok then
		store = result
	else
		disableStore(tostring(result))
	end
end

local function defaultProfile(): Profile
	return {
		version = VERSION,
		insights = {},
		settings = Types.defaultSettings(Config.DefaultMusicVolume, Config.DefaultVoiceVolume, Config.DefaultSfxVolume),
		settingsUpdated = 0,
		tips = 0,
		receipts = {},
		finaleSeen = false,
		firstJoin = os.time(),
		visits = 0,
	}
end

local function num(v: any, default: number, lo: number, hi: number): number
	if type(v) ~= "number" or v ~= v then
		return default
	end
	return math.clamp(v, lo, hi)
end

local function bool(v: any, default: boolean): boolean
	if type(v) == "boolean" then
		return v
	end
	return default
end

function ProgressStore.sanitizeSettings(raw: any, fallback: Types.Settings): Types.Settings
	if type(raw) ~= "table" then
		return table.clone(fallback)
	end
	return {
		music = num(raw.music, fallback.music, 0, 1),
		voice = num(raw.voice, fallback.voice, 0, 1),
		sfx = num(raw.sfx, fallback.sfx, 0, 1),
		captions = bool(raw.captions, fallback.captions),
		reduceMotion = bool(raw.reduceMotion, fallback.reduceMotion),
		aura = bool(raw.aura, fallback.aura),
	}
end

-- Turns whatever is stored (possibly nil, old or damaged) into a valid Profile.
local function sanitize(raw: any): Profile
	local p = defaultProfile()
	if type(raw) ~= "table" then
		return p
	end
	if type(raw.insights) == "table" then
		for zone, t in raw.insights do
			if Progression.isJourneyZone(zone) and type(t) == "number" then
				p.insights[zone] = t
			end
		end
	end
	p.settings = ProgressStore.sanitizeSettings(raw.settings, p.settings)
	p.settingsUpdated = num(raw.settingsUpdated, 0, 0, math.huge)
	p.tips = math.floor(num(raw.tips, 0, 0, 1e9))
	if type(raw.receipts) == "table" then
		for id, t in raw.receipts do
			if type(id) == "string" and type(t) == "number" then
				p.receipts[id] = t
			end
		end
	end
	p.finaleSeen = bool(raw.finaleSeen, false)
	p.firstJoin = num(raw.firstJoin, os.time(), 0, math.huge)
	p.visits = math.floor(num(raw.visits, 0, 0, 1e9))
	return p
end

type ReceiptEntry = { id: string, t: number }

local function newestFirst(a: ReceiptEntry, b: ReceiptEntry): boolean
	return a.t > b.t
end

local function trimReceipts(receipts: { [string]: number })
	local list: { ReceiptEntry } = {}
	for id, t in receipts do
		table.insert(list, { id = id, t = t })
	end
	if #list <= MAX_RECEIPTS then
		return
	end
	table.sort(list, newestFirst)
	for i = MAX_RECEIPTS + 1, #list do
		receipts[list[i].id] = nil
	end
end

-- The UpdateAsync transform: stored data + this session's changes. Never yields.
local function merge(stored: any, session: Session, receipts: { [string]: number }): Profile
	local base = sanitize(stored)
	local mine = session.profile
	for zone, t in mine.insights do
		local existing = base.insights[zone]
		if existing == nil or t < existing then
			base.insights[zone] = t
		end
	end
	if session.settingsChanged and mine.settingsUpdated >= base.settingsUpdated then
		base.settings = table.clone(mine.settings)
		base.settingsUpdated = mine.settingsUpdated
	end
	for id, t in receipts do
		if base.receipts[id] == nil then
			base.receipts[id] = t
			base.tips += 1
		end
	end
	trimReceipts(base.receipts)
	base.finaleSeen = base.finaleSeen or mine.finaleSeen
	base.firstJoin = math.min(base.firstJoin, mine.firstJoin)
	base.visits = math.max(base.visits, mine.visits)
	return base
end

local function keyFor(player: Player): string
	return "player_" .. tostring(player.UserId)
end

local function waitForBudget(requestType: Enum.DataStoreRequestType)
	for _ = 1, 20 do
		local ok, budget = pcall(function()
			return DataStoreService:GetRequestBudgetForRequestType(requestType)
		end)
		if not ok or budget > 0 then
			return
		end
		task.wait(1)
	end
end

-- Reads a player's data with retries. Returns ok, data.
local function readAsync(player: Player): (boolean, any)
	local ds = store
	if not ds or storeDisabledReason then
		return false, nil
	end
	local key = keyFor(player)
	for attempt = 1, 4 do
		waitForBudget(Enum.DataStoreRequestType.GetAsync)
		local ok, result = pcall(function()
			return ds:GetAsync(key)
		end)
		if ok then
			return true, result
		end
		local message = tostring(result)
		if isAccessError(message) then
			disableStore(message)
			return false, nil
		end
		warn(`[ProgressStore] load failed for {player.Name} (attempt {attempt}): {message}`)
		task.wait(attempt * 1.5)
	end
	return false, nil
end

-- Folds loaded data into the live session (used by the background retry after an outage).
local function absorb(session: Session, loaded: Profile)
	local mine = session.profile
	for zone, t in loaded.insights do
		if mine.insights[zone] == nil or t < mine.insights[zone] then
			mine.insights[zone] = t
		end
	end
	if not session.settingsChanged then
		mine.settings = loaded.settings
		mine.settingsUpdated = loaded.settingsUpdated
	end
	for id, t in loaded.receipts do
		mine.receipts[id] = mine.receipts[id] or t
	end
	mine.tips = math.max(mine.tips, loaded.tips)
	mine.finaleSeen = mine.finaleSeen or loaded.finaleSeen
	mine.firstJoin = math.min(mine.firstJoin, loaded.firstJoin)
	mine.visits = math.max(mine.visits, loaded.visits)
end

function ProgressStore.load(player: Player): Session
	local session: Session = {
		player = player,
		profile = defaultProfile(),
		loaded = false,
		persistent = store ~= nil and storeDisabledReason == nil,
		loadFailed = false,
		dirty = false,
		settingsChanged = false,
		pendingReceipts = {},
		saving = false,
		lastSave = os.clock(),
	}
	sessions[player] = session
	local ok, data = readAsync(player)
	if sessions[player] ~= session then
		return session -- left while loading
	end
	if ok then
		session.profile = sanitize(data)
	elseif storeDisabledReason then
		session.persistent = false
	else
		-- a live outage: play on with defaults, keep saving (the merge is safe) and retry the load
		session.loadFailed = true
		task.spawn(function()
			for _ = 1, 10 do
				task.wait(20)
				if sessions[player] ~= session then
					return
				end
				local ok2, data2 = readAsync(player)
				if ok2 then
					absorb(session, sanitize(data2))
					session.loadFailed = false
					ProgressStore.Updated:Fire(player)
					return
				end
			end
		end)
	end
	session.profile.visits += 1
	session.dirty = true
	session.loaded = true
	ProgressStore.Loaded:Fire(player, session)
	return session
end

function ProgressStore.get(player: Player): Session?
	return sessions[player]
end

-- Waits (up to timeout seconds) until the player's data has loaded.
function ProgressStore.waitFor(player: Player, timeout: number): Session?
	local deadline = os.clock() + timeout
	while os.clock() < deadline do
		local s = sessions[player]
		if s and s.loaded then
			return s
		end
		if player.Parent == nil then
			return nil
		end
		task.wait(0.1)
	end
	local s = sessions[player]
	return if s and s.loaded then s else nil
end

function ProgressStore.isPersistent(player: Player): boolean
	local s = sessions[player]
	return s ~= nil and s.persistent
end

-- Saves now. Returns true when the data is safely stored (or saving is impossible
-- here and the session is in-memory only, in which case it returns false).
function ProgressStore.saveAsync(player: Player, reason: string): boolean
	local session = sessions[player]
	local ds = store
	if not session or not session.loaded or not session.persistent or not ds then
		return false
	end
	while session.saving do
		task.wait(0.1)
	end
	session.saving = true
	local receipts = table.clone(session.pendingReceipts)
	local settingsWereChanged = session.settingsChanged
	local key = keyFor(player)
	local saved: Profile? = nil
	for attempt = 1, 4 do
		waitForBudget(Enum.DataStoreRequestType.UpdateAsync)
		local ok, result = pcall(function()
			return ds:UpdateAsync(key, function(stored)
				return merge(stored, session, receipts)
			end)
		end)
		if ok then
			saved = sanitize(result)
			break
		end
		local message = tostring(result)
		if isAccessError(message) then
			disableStore(message)
			session.persistent = false
			break
		end
		warn(`[ProgressStore] save ({reason}) failed for {player.Name} (attempt {attempt}): {message}`)
		task.wait(attempt * 1.5)
	end
	session.saving = false
	if not saved then
		return false
	end
	for id in receipts do
		session.pendingReceipts[id] = nil
	end
	if settingsWereChanged and session.profile.settingsUpdated <= saved.settingsUpdated then
		session.settingsChanged = false
	end
	-- adopt anything another server added, keep what changed while we were saving
	absorb(session, saved)
	session.profile.tips = saved.tips
	for id in session.pendingReceipts do
		if saved.receipts[id] == nil then
			session.profile.tips += 1
		end
	end
	session.dirty = next(session.pendingReceipts) ~= nil
	session.lastSave = os.clock()
	return true
end

function ProgressStore.markDirty(player: Player)
	local s = sessions[player]
	if s then
		s.dirty = true
	end
end

-- Returns (firstTime, timestamp).
function ProgressStore.collectInsight(player: Player, zone: string): (boolean, number)
	local s = sessions[player]
	if not s then
		return false, os.time()
	end
	local existing = s.profile.insights[zone]
	if existing then
		return false, existing
	end
	local t = os.time()
	s.profile.insights[zone] = t
	s.dirty = true
	task.spawn(ProgressStore.saveAsync, player, "insight")
	return true, t
end

function ProgressStore.setFinaleSeen(player: Player)
	local s = sessions[player]
	if s and not s.profile.finaleSeen then
		s.profile.finaleSeen = true
		s.dirty = true
	end
end

function ProgressStore.setSettings(player: Player, raw: any): Types.Settings?
	local s = sessions[player]
	if not s or not s.loaded then
		return nil
	end
	s.profile.settings = ProgressStore.sanitizeSettings(raw, s.profile.settings)
	s.profile.settingsUpdated = os.time()
	s.settingsChanged = true
	s.dirty = true
	return s.profile.settings
end

-- Developer product receipts (see Purchases). Returns "new" or "known".
function ProgressStore.recordReceipt(player: Player, purchaseId: string): string
	local s = sessions[player]
	if not s then
		return "known"
	end
	if s.profile.receipts[purchaseId] then
		return "known"
	end
	local t = os.time()
	s.profile.receipts[purchaseId] = t
	s.pendingReceipts[purchaseId] = t
	s.profile.tips += 1
	s.dirty = true
	return "new"
end

function ProgressStore.receiptIsSaved(player: Player, purchaseId: string): boolean
	local s = sessions[player]
	return s ~= nil and s.profile.receipts[purchaseId] ~= nil and s.pendingReceipts[purchaseId] == nil
end

function ProgressStore.release(player: Player)
	local s = sessions[player]
	if not s then
		return
	end
	if s.loaded and s.persistent and s.dirty then
		ProgressStore.saveAsync(player, "leave")
	end
	sessions[player] = nil
end

function ProgressStore.start()
	Players.PlayerRemoving:Connect(function(player)
		ProgressStore.release(player)
	end)
	task.spawn(function()
		while true do
			task.wait(15)
			for player, s in sessions do
				if s.loaded and s.persistent and s.dirty and os.clock() - s.lastSave > AUTOSAVE_SECONDS then
					task.spawn(ProgressStore.saveAsync, player, "autosave")
				end
			end
		end
	end)
	game:BindToClose(function()
		if RunService:IsStudio() and storeDisabledReason then
			return
		end
		local pending = 0
		for player in sessions do
			pending += 1
			task.spawn(function()
				ProgressStore.release(player)
				pending -= 1
			end)
		end
		local deadline = os.clock() + 25
		while pending > 0 and os.clock() < deadline do
			task.wait(0.2)
		end
	end)
end

return ProgressStore
