-- tools/check_place.luau  (run by tools/validate_place.py)
--   lune run tools/check_place.luau NothingBecomesEverything.rbxlx <project root>
-- Loads the place with Lune's Roblox DOM (rbx-dom, the same library Rojo uses) and
-- checks the structure the scripts rely on, cross-checked with Content and Config.

local fs = require("@lune/fs")
local roblox = require("@lune/roblox")
local process = require("@lune/process")

local placePath = process.args[1]
local root = process.args[2] or "."
local game = roblox.deserializePlace(fs.readFile(placePath))
local Content = require("../src/ReplicatedStorage/Content")
local Config = require("../src/ReplicatedStorage/Config")

local failures = 0
local function check(cond: any, msg: string)
	if not cond then
		failures += 1
		print("FAIL: " .. msg)
	end
end

local function tagged(container, tag: string)
	local out = {}
	for _, d in container:GetDescendants() do
		if d:HasTag(tag) then
			table.insert(out, d)
		end
	end
	return out
end

local ws = game:GetService("Workspace")
local rs = game:GetService("ReplicatedStorage")
local journey = { "time", "hole", "glass", "road", "chains", "everything" }
local all = { "hub", "time", "hole", "glass", "road", "chains", "everything" }

-- ---------------------------------------------------------------- services & settings
check(ws.StreamingEnabled == true, "Workspace.StreamingEnabled is on")
local sp = game:GetService("StarterPlayer")
check(sp.CharacterUseJumpPower == true and sp.CharacterJumpPower == 50, "StarterPlayer uses JumpPower 50")
local sound = game:GetService("SoundService")
for _, g in { "Music", "Voice", "SFX" } do
	local group = sound:FindFirstChild(g)
	check(group and group.ClassName == "SoundGroup", "SoundGroup " .. g)
end
local remotes = rs:FindFirstChild("Remotes")
for _, n in { "GetState", "State", "ZoneEvent", "Travel", "ZoneAction", "SaveSettings", "Notify" } do
	check(remotes and remotes:FindFirstChild(n), "remote " .. n)
end
local lighting = game:GetService("Lighting")
for _, n in { "Atmosphere", "Sky", "Bloom", "Grade", "SunRays" } do
	check(lighting:FindFirstChild(n), "Lighting." .. n)
end

-- ---------------------------------------------------------------- zones
local zones = ws:FindFirstChild("Zones")
check(zones ~= nil, "Workspace.Zones")
for _, id in all do
	local z = zones and zones:FindFirstChild(id)
	check(z and z:GetAttribute("Zone") == id, "zone model " .. id)
	local arrival = false
	if z then
		for _, cp in tagged(z, "Checkpoint") do
			if cp:GetAttribute("Zone") == id and cp:GetAttribute("Index") == 0 then
				arrival = true
			end
		end
	end
	check(arrival, id .. " has an arrival pad (Checkpoint Index 0)")
end

local parts, unanchored = 0, 0
for _, d in game:GetDescendants() do
	if d:IsA("BasePart") then
		parts += 1
		if not d.Anchored then
			unanchored += 1
		end
	end
end
check(unanchored == 0, "every part is anchored (" .. unanchored .. " are not)")

-- insights, portals, screens
local insights, portals, screens = {}, {}, {}
for _, p in tagged(ws, "Insight") do
	insights[p:GetAttribute("Zone")] = p
	local prompt = p:FindFirstChildOfClass("ProximityPrompt")
	check(prompt and prompt:GetAttribute("Action") == "insight" and prompt:GetAttribute("Zone") == p:GetAttribute("Zone"),
		"insight prompt for " .. tostring(p:GetAttribute("Zone")))
end
for _, g in tagged(ws, "Portal") do
	portals[g:GetAttribute("Zone")] = g
end
for _, v in tagged(ws, "ZoneScreen") do
	check(v.ClassName == "VideoFrame", "ZoneScreen is a VideoFrame")
	local zone = v:GetAttribute("Zone")
	screens[zone] = v
	check(v:GetAttribute("VideoKey") ~= nil and Config.Videos[v:GetAttribute("VideoKey")] ~= nil,
		"screen " .. tostring(zone) .. " has a Config.Videos key")
	local gui = v.Parent
	check(gui and gui.ClassName == "SurfaceGui" and gui:FindFirstChild("Placeholder"), "screen " .. tostring(zone) .. " placeholder")
	local screenPart = gui and gui.Parent
	if screenPart and screenPart:IsA("BasePart") then
		local s = screenPart.Size
		check(math.abs(s.X / s.Y - 9 / 16) < 1e-3, "screen " .. tostring(zone) .. " is 9:16")
	end
	local placeholder = gui and gui:FindFirstChild("Placeholder")
	local title = placeholder and placeholder:FindFirstChild("Title")
	check(title and title.Text == "Brandon's video goes here", "placeholder text on " .. tostring(zone))
end
for _, id in journey do
	check(insights[id] ~= nil, "insight in " .. id)
	check(portals[id] ~= nil, "portal to " .. id)
end
for _, id in all do
	check(screens[id] ~= nil, "video screen in " .. id)
end

-- ---------------------------------------------------------------- prompts & lines
local ACTIONS = {
	portal = { "Zone" }, ["return"] = {}, insight = { "Zone" }, listen = { "LineId" }, journal = {}, tip = {}, aura = {},
	video = { "Zone" }, bell = { "Index" }, letgo = { "Index" }, door = {},
}
local promptCount, stoneLines = 0, {}
for _, d in game:GetDescendants() do
	if d.ClassName == "ProximityPrompt" then
		promptCount += 1
		local action = d:GetAttribute("Action")
		local needs = ACTIONS[action]
		check(needs ~= nil, "prompt " .. d:GetFullName() .. " has a known Action (" .. tostring(action) .. ")")
		for _, a in needs or {} do
			check(d:GetAttribute(a) ~= nil, "prompt " .. d:GetFullName() .. " has " .. a)
		end
		if action == "listen" then
			local line = d:GetAttribute("LineId")
			check(Content.Lines[line] ~= nil, "speech stone line " .. tostring(line) .. " exists in Content")
			stoneLines[line] = true
		end
	end
	local beat = d:GetAttribute("LineId")
	if beat ~= nil and d.Name == "BeatMarker" then
		check(Content.Lines[beat] ~= nil, "beat marker line " .. tostring(beat) .. " exists in Content")
		stoneLines[beat] = true
	end
end

-- ---------------------------------------------------------------- scripts == src/, and what they reference
local sources = {}
local function collectScripts(inst, rel)
	for _, child in inst:GetChildren() do
		local path = rel .. "/" .. child.Name
		if child.ClassName == "Script" then
			sources[path .. ".server.lua"] = child.Source
		elseif child.ClassName == "LocalScript" then
			sources[path .. ".client.lua"] = child.Source
		elseif child.ClassName == "ModuleScript" then
			sources[path .. ".lua"] = child.Source
		end
		if child.ClassName == "Folder" or child:IsA("LuaSourceContainer") or child.ClassName == "StarterPlayerScripts" then
			collectScripts(child, path)
		end
	end
end
collectScripts(game:GetService("ReplicatedFirst"), "ReplicatedFirst")
collectScripts(rs, "ReplicatedStorage")
collectScripts(game:GetService("ServerScriptService"), "ServerScriptService")
collectScripts(sp:FindFirstChild("StarterPlayerScripts"), "StarterPlayer/StarterPlayerScripts")
local count, allSource = 0, ""
for rel, src in sources do
	count += 1
	local ok, disk = pcall(fs.readFile, root .. "/src/" .. rel)
	check(ok and disk == src, "script " .. rel .. " matches src/" .. rel)
	allSource ..= src .. "\n"
end
check(count >= 30, "all scripts present (" .. count .. ")")

local usedLines = table.clone(stoneLines)
for _, z in Content.Zones do
	if z.insightLine then
		usedLines[z.insightLine] = true
	end
	check(Content.Music[z.music] ~= nil, "zone " .. z.id .. " music track exists")
end
for id in allSource:gmatch('say%a*%("([%w_]+)"') do
	check(Content.Lines[id] ~= nil, "scripted line " .. id .. " exists in Content")
end
for id in Content.Lines do
	if allSource:find('"' .. id .. '"', 1, true) then
		usedLines[id] = true -- referenced by a script (story beat)
	end
end
local missingLines = {}
for id in Content.Lines do
	if not usedLines[id] then
		table.insert(missingLines, id)
	end
end
check(#missingLines == 0, "every voice line is used somewhere (unused: " .. table.concat(missingLines, ", ") .. ")")

local usedSfx = {}
for id in allSource:gmatch('playSfx%("([%w_]+)"') do
	check(Content.Sfx[id] ~= nil, "sfx " .. id .. " exists in Content")
	usedSfx[id] = true
end
local missingSfx = {}
for id in Content.Sfx do
	if not usedSfx[id] then
		table.insert(missingSfx, id)
	end
end
check(#missingSfx == 0, "every sound effect is used (unused: " .. table.concat(missingSfx, ", ") .. ")")
check(allSource:find('setMusic%("finale"') ~= nil, "the finale track is used")
check(allSource:find("PlaybackRegion", 1, true) and allSource:find("LoopRegion", 1, true)
	and allSource:find("PlaybackRegionsEnabled", 1, true), "audio uses PlaybackRegion / LoopRegion")
check(allSource:find("IsEndlessContentAutoplayAllowed", 1, true) ~= nil, "PolicyService autoplay check present")
check(allSource:find("ProcessReceipt", 1, true) ~= nil and allSource:find("UpdateAsync", 1, true) ~= nil,
	"ProcessReceipt + UpdateAsync present")

-- ---------------------------------------------------------------- kits
local kits = rs:FindFirstChild("ZoneKits")
check(kits ~= nil, "ReplicatedStorage.ZoneKits")
local hole = kits:FindFirstChild("hole")
local flights = hole:FindFirstChild("Flights")
local steps = 0
for f = 1, 7 do
	local fl = flights:FindFirstChild("Flight" .. f)
	check(fl ~= nil, "hole flight " .. f)
	for s = 1, 6 do
		local st = fl and fl:FindFirstChild("Step" .. s)
		check(st and st:GetAttribute("Index") == s, "hole flight " .. f .. " step " .. s)
		steps += if st then 1 else 0
	end
	local orb = hole.Orbs:FindFirstChild("Orb" .. f)
	check(orb and orb:FindFirstChild("Core") and orb:GetAttribute("Phrase") == Content.Story.betterThoughts[f],
		"better thought orb " .. f)
end
check(typeof(hole:GetAttribute("PitCenter")) == "Vector3", "hole PitCenter attribute")

local glass = kits:FindFirstChild("glass")
local blockCount = 0
for _, b in glass.Blocks:GetChildren() do
	blockCount += 1
	local prompt = b:FindFirstChildOfClass("ProximityPrompt")
	check(prompt and prompt.ActionText == "Let it go" and prompt:GetAttribute("Action") == "letgo", "block " .. b.Name .. " prompt")
	check(table.find(Content.Story.glassWords, b:GetAttribute("Word")) ~= nil, "block word " .. tostring(b:GetAttribute("Word")))
end
check(blockCount == #Content.Story.glassWords, "one block per glass word")
local door = glass:FindFirstChild("Door")
check(door and typeof(door:GetAttribute("Hinge")) == "Vector3" and door:FindFirstChild("DoorLeaf"), "glass door")
local water = glass:FindFirstChild("Water")
check(water and water.CanCollide == false and water.CanTouch == false and water.CanQuery == false,
	"glass water is visual only (no collision, no touch)")
local panels = 0
for _, p in glass.Box:GetChildren() do
	panels += 1
	check(typeof(p:GetAttribute("Outward")) == "Vector3", "box piece " .. p.Name .. " knows which way to shatter")
end
check(panels > 30, "glass box has its panels")

local road = kits:FindFirstChild("road")
check(road:FindFirstChild("Wall") and typeof(road.Wall:GetAttribute("Pivot")) == "Vector3" and road:FindFirstChild("Rock"),
	"road wall + rock")
check(type(road:GetAttribute("WallZ")) == "number", "road WallZ")
check(kits.chains:FindFirstChild("ChainArea"), "chains area")
check(kits.everything:FindFirstChild("HomePortal"), "summit home portal")
local kinetic = 0
for _, d in kits.time:GetDescendants() do
	if d:GetAttribute("Kinetic") ~= nil then
		kinetic += 1
		check(typeof(d:GetAttribute("Pivot")) == "Vector3" and typeof(d:GetAttribute("Axis")) == "Vector3",
			"kinetic " .. d.Name .. " has Pivot and Axis")
	end
end
check(kinetic >= 10, "clock tower moving parts (" .. kinetic .. ")")
local bells = 0
for _, b in tagged(ws, "Bell") do
	bells += 1
end
check(bells == 3, "three I CAN bells")

-- ---------------------------------------------------------------- config defaults
check(Config.VoicePackId == 0 and Config.SfxPackId == 0 and Config.MusicPackId == 0 and Config.LoadingImageId == 0,
	"asset ids start at 0 (placeholders)")
for _, id in all do
	check(Config.Videos[id] == 0, "Config.Videos." .. id .. " = 0")
end
for _, id in journey do
	check(Config.BadgeIds[id] == 0, "Config.BadgeIds." .. id)
end
check(Config.BadgeIds.finale == 0 and Config.GamePassId == 0 and Config.DevProductIds.TipBrandon == 0, "shop/badge ids 0")

local n = 0
for _ in game:GetDescendants() do
	n += 1
end
print(string.format("Lune loaded %d instances (%d parts, %d prompts, %d hole steps, %d glass blocks, %d scripts); %d failures",
	n, parts, promptCount, steps, blockCount, count, failures))
if failures > 0 then
	process.exit(1)
end
