--!strict
-- StarterPlayerScripts > ClientModules > SetupCheck  (ModuleScript)
-- Tells Brandon why there's no sound or video, instead of the game just staying quiet.
-- It checks the IDs in Config: which files aren't uploaded yet (ID 0), and which
-- uploaded IDs fail to load, with the fix for each. It only shows in Studio or when the
-- game's owner plays it; other players never see it.

local ContentProvider = game:GetService("ContentProvider")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage:WaitForChild("Config"))

local SetupCheck = {}

local GREEN = Color3.fromRGB(120, 222, 150)
local RED = Color3.fromRGB(255, 125, 115)
local AMBER = Color3.fromRGB(255, 205, 110)
local BLUE = Color3.fromRGB(150, 200, 255)
local INK = Color3.fromRGB(235, 238, 245)

local FIX_LOAD = "Fix: wait a few minutes (Roblox may still be checking it), make sure you pasted the ID from "
	.. "Asset Manager > right-click > Copy Asset ID, and publish the game with the same account that uploaded it."

local function shouldShow(): boolean
	if RunService:IsStudio() then
		return true
	end
	local player = Players.LocalPlayer
	return player ~= nil and game.CreatorType == Enum.CreatorType.User and game.CreatorId == player.UserId
end

local function asset(id: number): string
	return "rbxassetid://" .. tostring(math.floor(id))
end

-- Loads one asset through ContentProvider and reports whether Roblox served it.
local function loads(target: Instance | string): boolean
	local status: Enum.AssetFetchStatus? = nil
	local ok = pcall(function()
		ContentProvider:PreloadAsync({ target }, function(_: string, s: Enum.AssetFetchStatus)
			status = s
		end)
	end)
	if not ok then
		return false
	end
	return status == Enum.AssetFetchStatus.Success
end

local function soundLoads(id: number): boolean
	local s = Instance.new("Sound")
	s.SoundId = asset(id)
	local result = loads(s) or s.IsLoaded
	s:Destroy()
	return result
end

local function videoLoads(id: number): boolean
	local v = Instance.new("VideoFrame")
	v.Video = asset(id)
	local result = loads(v) or v.IsLoaded
	v:Destroy()
	return result
end

-- ---------------------------------------------------------------------------- panel
type Panel = { gui: ScreenGui, list: Frame, add: (text: string, color: Color3) -> TextLabel }

local function panel(): Panel
	local player = Players.LocalPlayer
	local gui = Instance.new("ScreenGui")
	gui.Name = "SetupCheck"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 60
	gui.IgnoreGuiInset = true

	local frame = Instance.new("Frame")
	frame.AnchorPoint = Vector2.new(0.5, 0)
	frame.Position = UDim2.new(0.5, 0, 0, 64)
	frame.Size = UDim2.new(0.92, 0, 0, 0)
	frame.AutomaticSize = Enum.AutomaticSize.Y
	frame.BackgroundColor3 = Color3.fromRGB(14, 18, 28)
	frame.BackgroundTransparency = 0.06
	frame.Parent = gui
	local limit = Instance.new("UISizeConstraint")
	limit.MaxSize = Vector2.new(600, math.huge)
	limit.Parent = frame
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 12)
	corner.Parent = frame
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.fromRGB(90, 200, 225)
	stroke.Thickness = 1.5
	stroke.Transparency = 0.3
	stroke.Parent = frame
	local pad = Instance.new("UIPadding")
	pad.PaddingTop = UDim.new(0, 14)
	pad.PaddingBottom = UDim.new(0, 14)
	pad.PaddingLeft = UDim.new(0, 16)
	pad.PaddingRight = UDim.new(0, 16)
	pad.Parent = frame
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = frame

	local order = 0
	local function add(text: string, color: Color3): TextLabel
		order += 1
		local label = Instance.new("TextLabel")
		label.LayoutOrder = order
		label.BackgroundTransparency = 1
		label.Size = UDim2.new(1, 0, 0, 0)
		label.AutomaticSize = Enum.AutomaticSize.Y
		label.Font = Enum.Font.GothamMedium
		label.TextSize = 16
		label.TextWrapped = true
		label.RichText = true
		label.TextXAlignment = Enum.TextXAlignment.Left
		label.TextColor3 = color
		label.Text = text
		label.Parent = frame
		return label
	end

	add("<b>SETUP CHECK</b>  <font color=\"#9aa4b6\">(only you can see this)</font>", INK)

	local close = Instance.new("TextButton")
	close.Name = "Hide"
	close.AnchorPoint = Vector2.new(1, 0)
	close.Position = UDim2.new(1, 4, 0, -6)
	close.Size = UDim2.new(0, 64, 0, 28)
	close.BackgroundColor3 = Color3.fromRGB(40, 48, 66)
	close.TextColor3 = INK
	close.Font = Enum.Font.GothamBold
	close.TextSize = 14
	close.Text = "Hide"
	close.ZIndex = 2
	close.Parent = frame
	local closeCorner = Instance.new("UICorner")
	closeCorner.CornerRadius = UDim.new(0, 8)
	closeCorner.Parent = close
	close.Activated:Connect(function()
		gui:Destroy()
	end)

	if player then
		gui.Parent = player:WaitForChild("PlayerGui")
	end
	return { gui = gui, list = frame, add = add }
end

-- ---------------------------------------------------------------------------- checks
type Item = { name: string, id: number, kind: string }

function SetupCheck.run()
	if not shouldShow() then
		return
	end
	local p = panel()
	local problems = 0

	if game.PlaceId == 0 then
		problems += 1
		p.add("<b>Game not published yet.</b> File > Publish to Roblox (it stays private). Your uploads can't play "
			.. "until the game is published with the same account.", AMBER)
	end

	local items: { Item } = {
		{ name = "Voice pack (voice_pack.ogg)", id = Config.VoicePackId, kind = "sound" },
		{ name = "Music pack (music_pack.ogg)", id = Config.MusicPackId, kind = "sound" },
		{ name = "Sound effects (sfx_pack.ogg)", id = Config.SfxPackId, kind = "sound" },
		{ name = "Loading screen (loading_screen.png)", id = Config.LoadingImageId, kind = "image" },
	}
	local missing: { string } = {}
	for _, item in items do
		if item.id <= 0 then
			problems += 1
			table.insert(missing, item.name)
			p.add(`<b>{item.name}</b>: not uploaded yet (ID is 0).`, RED)
		else
			local row = p.add(`<b>{item.name}</b>: checking ID {item.id}...`, AMBER)
			task.spawn(function()
				local good = if item.kind == "sound" then soundLoads(item.id) else loads(asset(item.id))
				if good then
					row.Text = `<b>{item.name}</b>: working.`
					row.TextColor3 = GREEN
				else
					problems += 1
					row.Text = `<b>{item.name}</b>: ID {item.id} didn't load. {FIX_LOAD}`
					row.TextColor3 = RED
				end
			end)
		end
	end
	if #missing > 0 then
		p.add("<b>How to add sound (free):</b> Window > Asset Manager > Import, pick the files from the "
			.. "\"upload\" folder, then right-click each one > Copy Asset ID and paste it into "
			.. "ReplicatedStorage > Config (VoicePackId, MusicPackId, SfxPackId, LoadingImageId). "
			.. "Captions work without it; your voice and music need it.", INK)
	end

	local videos, set = 0, 0
	for zone, id in Config.Videos do
		videos += 1
		if id > 0 then
			set += 1
			local row = p.add(`<b>Video: {zone}</b>: checking ID {id}...`, AMBER)
			task.spawn(function()
				if videoLoads(id) then
					row.Text = `<b>Video: {zone}</b>: working.`
					row.TextColor3 = GREEN
				else
					row.Text = `<b>Video: {zone}</b>: ID {id} didn't load. It may still be under review or was rejected. {FIX_LOAD}`
					row.TextColor3 = RED
				end
			end)
		end
	end
	if set == 0 then
		p.add(`<b>Videos: 0 of {videos} uploaded.</b> That's why the screens say "Brandon's video goes here". Roblox `
			.. "can't play video files from your computer: each video has to be uploaded to Roblox (2,000 Robux each, "
			.. "13+ and ID-verified), then its ID goes in Config.Videos. Upload one first and wait for approval.", BLUE)
	end

	task.delay(12, function()
		if problems == 0 and p.gui.Parent then
			p.add("Everything's set up. This panel closes by itself.", GREEN)
			task.wait(4)
			p.gui:Destroy()
		end
	end)
end

return SetupCheck
