--!strict
-- StarterPlayerScripts > ClientModules > HUD  (ModuleScript)
-- Mobile-first HUD: a compact 6-dot zone tracker (top centre), Journal / Settings /
-- Return buttons (top right, 44 px touch targets) and toasts. A cinematic layer adds
-- the letterbox bars, the zone intro card, the Insight card, fades and the credits.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Content = require(ReplicatedStorage:WaitForChild("Content"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local Progression = require(Shared:WaitForChild("Progression"))
local Theme = require(script.Parent:WaitForChild("Theme"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

export type Callbacks = {
	onJournal: () -> (),
	onSettings: () -> (),
	onReturn: () -> (),
	onMusic: () -> (),
}

local HUD = {}

local hudGui: ScreenGui
local cineGui: ScreenGui
local dots: { [string]: Frame } = {}
local zoneLabel: TextLabel
local returnButton: TextButton
local musicButton: TextButton
local toasts: Frame
local fadeFrame: Frame
local topBar: Frame
local bottomBar: Frame
local zoneCard: CanvasGroup
local cardNumeral: TextLabel
local cardName: TextLabel
local cardTheme: TextLabel
local cardLine: Frame
local insightCard: CanvasGroup
local insightText: TextLabel
local insightZone: TextLabel
local insightHint: TextLabel
local creditsFrame: Frame

local currentZone = "hub"
local cardToken = 0
local letterboxUsers = 0

local function playerGui(): PlayerGui
	return (Players.LocalPlayer :: Player):WaitForChild("PlayerGui") :: PlayerGui
end

-- ---------------------------------------------------------------------------- build
local function buildHud(callbacks: Callbacks)
	hudGui = Instance.new("ScreenGui")
	hudGui.Name = "HUD"
	hudGui.ResetOnSpawn = false
	hudGui.DisplayOrder = 10
	hudGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	hudGui.Parent = playerGui()

	-- zone tracker
	local tracker = UIKit.frame(hudGui, "Tracker", UDim2.fromOffset(236, 46), UDim2.new(0.5, 0, 0, 6), Theme.Ink, 0.45)
	tracker.AnchorPoint = Vector2.new(0.5, 0)
	UIKit.corner(tracker, 12)
	local line = UIKit.frame(tracker, "Line", UDim2.fromOffset(196, 2), UDim2.fromOffset(20, 13), Theme.Dim, 0.3)
	line.ZIndex = 1
	for i, id in Progression.Journey do
		local dot = UIKit.frame(tracker, "Dot_" .. id, UDim2.fromOffset(16, 16), UDim2.fromOffset(20 + (i - 1) * 39 - 8, 6),
			Theme.Navy, 0)
		dot.ZIndex = 2
		UIKit.corner(dot, 1, 1)
		UIKit.stroke(dot, Theme.Dim, 2, 0)
		dots[id] = dot
	end
	zoneLabel = UIKit.label(tracker, "Zone", "The Clearing", UDim2.new(1, -12, 0, 16), UDim2.fromOffset(6, 26),
		Theme.title(), Theme.Soft, 15)

	-- buttons
	local column = Instance.new("Frame")
	column.Name = "Buttons"
	column.AnchorPoint = Vector2.new(1, 0)
	column.Position = UDim2.new(1, -8, 0, 6)
	column.Size = UDim2.fromOffset(108, 200)
	column.BackgroundTransparency = 1
	column.Parent = hudGui
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Right
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = column
	local journal = UIKit.button(column, "Journal", "Journal", UDim2.fromOffset(104, 44), UDim2.new())
	journal.LayoutOrder = 1
	local settings = UIKit.button(column, "Settings", "Settings", UDim2.fromOffset(104, 44), UDim2.new())
	settings.LayoutOrder = 2
	returnButton = UIKit.button(column, "Return", "Return", UDim2.fromOffset(104, 44), UDim2.new()) -- to the Clearing
	returnButton.LayoutOrder = 3
	returnButton.Visible = false
	musicButton = UIKit.button(column, "Music", "Play music", UDim2.fromOffset(104, 44), UDim2.new(), Theme.NavySoft,
		Theme.Gold)
	musicButton.LayoutOrder = 4
	musicButton.Visible = false
	journal.Activated:Connect(function()
		callbacks.onJournal()
	end)
	settings.Activated:Connect(function()
		callbacks.onSettings()
	end)
	returnButton.Activated:Connect(function()
		callbacks.onReturn()
	end)
	musicButton.Activated:Connect(function()
		callbacks.onMusic()
	end)

	-- toasts
	toasts = Instance.new("Frame")
	toasts.Name = "Toasts"
	toasts.AnchorPoint = Vector2.new(0.5, 0)
	toasts.Position = UDim2.new(0.5, 0, 0, 60)
	toasts.Size = UDim2.new(0.56, 0, 0, 150)
	toasts.BackgroundTransparency = 1
	toasts.Parent = hudGui
	local tl = Instance.new("UIListLayout")
	tl.Padding = UDim.new(0, 6)
	tl.HorizontalAlignment = Enum.HorizontalAlignment.Center
	tl.SortOrder = Enum.SortOrder.LayoutOrder
	tl.Parent = toasts
end

local function buildCinematic()
	cineGui = Instance.new("ScreenGui")
	cineGui.Name = "Cinematic"
	cineGui.ResetOnSpawn = false
	cineGui.IgnoreGuiInset = true
	cineGui.ScreenInsets = Enum.ScreenInsets.None
	cineGui.DisplayOrder = 40
	cineGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	cineGui.Parent = playerGui()

	topBar = UIKit.frame(cineGui, "TopBar", UDim2.fromScale(1, 0.12), UDim2.fromScale(0, -0.12), Color3.new(0, 0, 0), 0)
	bottomBar = UIKit.frame(cineGui, "BottomBar", UDim2.fromScale(1, 0.12), UDim2.fromScale(0, 1), Color3.new(0, 0, 0), 0)

	zoneCard = Instance.new("CanvasGroup")
	zoneCard.Name = "ZoneCard"
	zoneCard.AnchorPoint = Vector2.new(0.5, 0.5)
	zoneCard.Position = UDim2.fromScale(0.5, 0.44)
	zoneCard.Size = UDim2.fromScale(0.86, 0.34)
	zoneCard.BackgroundTransparency = 1
	zoneCard.GroupTransparency = 1
	zoneCard.Visible = false
	zoneCard.Parent = cineGui
	UIKit.sizeLimit(zoneCard, 1000, 320)
	cardNumeral = UIKit.label(zoneCard, "Numeral", "", UDim2.fromScale(1, 0.16), UDim2.fromScale(0, 0), Theme.title(),
		Theme.Gold, 34)
	cardName = UIKit.label(zoneCard, "Name", "", UDim2.fromScale(1, 0.42), UDim2.fromScale(0, 0.15), Theme.title(),
		Theme.White, 84)
	local nameStroke = UIKit.stroke(cardName, Color3.new(0, 0, 0), 1, 0.6)
	nameStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	cardLine = UIKit.frame(zoneCard, "Line", UDim2.fromScale(0.22, 0.012), UDim2.fromScale(0.39, 0.62), Theme.Cyan, 0.1)
	cardTheme = UIKit.label(zoneCard, "Theme", "", UDim2.fromScale(0.9, 0.24), UDim2.fromScale(0.05, 0.68),
		Theme.title(nil, true), Theme.Soft, 34)

	insightCard = Instance.new("CanvasGroup")
	insightCard.Name = "InsightCard"
	insightCard.AnchorPoint = Vector2.new(0.5, 0.5)
	insightCard.Position = UDim2.fromScale(0.5, 0.47)
	insightCard.Size = UDim2.fromScale(0.78, 0.5)
	insightCard.BackgroundColor3 = Theme.Navy
	insightCard.BackgroundTransparency = 0.18
	insightCard.GroupTransparency = 1
	insightCard.Visible = false
	insightCard.Parent = cineGui
	UIKit.sizeLimit(insightCard, 820, 380)
	UIKit.corner(insightCard, 18)
	UIKit.stroke(insightCard, Theme.Gold, 2, 0.25)
	UIKit.label(insightCard, "Label", "INSIGHT", UDim2.fromScale(0.6, 0.1), UDim2.fromScale(0.2, 0.07), Theme.ui(Enum.FontWeight.Bold),
		Theme.Gold, 22)
	insightText = UIKit.label(insightCard, "Text", "", UDim2.fromScale(0.86, 0.5), UDim2.fromScale(0.07, 0.2),
		Theme.title(nil, true), Theme.White, 44)
	insightZone = UIKit.label(insightCard, "Zone", "", UDim2.fromScale(0.8, 0.1), UDim2.fromScale(0.1, 0.72), Theme.title(),
		Theme.Cyan, 26)
	insightHint = UIKit.label(insightCard, "Hint", "Added to your Journal", UDim2.fromScale(0.8, 0.08),
		UDim2.fromScale(0.1, 0.85), Theme.ui(), Theme.Dim, 18)

	creditsFrame = Instance.new("Frame")
	creditsFrame.Name = "Credits"
	creditsFrame.Size = UDim2.fromScale(1, 1)
	creditsFrame.BackgroundTransparency = 1
	creditsFrame.ClipsDescendants = true
	creditsFrame.Visible = false
	creditsFrame.Parent = cineGui

	fadeFrame = UIKit.frame(cineGui, "Fade", UDim2.fromScale(1, 1), UDim2.new(), Color3.new(0, 0, 0), 1)
	fadeFrame.ZIndex = 20
end

function HUD.init(callbacks: Callbacks)
	buildHud(callbacks)
	buildCinematic()
end

-- ---------------------------------------------------------------------------- tracker
function HUD.setZone(zone: string)
	currentZone = zone
	zoneLabel.Text = Progression.name(zone)
	returnButton.Visible = zone ~= "hub"
end

function HUD.setProgress(snapshot: Types.Snapshot)
	for _, id in Progression.Journey do
		local dot = dots[id]
		local stroke = dot:FindFirstChildOfClass("UIStroke")
		local color = Progression.color(id)
		local collected = snapshot.insights[id] ~= nil
		local unlocked = Progression.isUnlocked(snapshot.insights, id)
		dot.BackgroundColor3 = if collected then color else Theme.Navy
		dot.BackgroundTransparency = if unlocked or collected then 0 else 0.5
		if stroke then
			stroke.Color = if unlocked or collected then color else Theme.Dim
			stroke.Transparency = if unlocked or collected then 0 else 0.4
			stroke.Thickness = if id == currentZone then 3.5 else 2
		end
	end
end

function HUD.setHudVisible(on: boolean)
	hudGui.Enabled = on
end

function HUD.showMusicButton(on: boolean)
	musicButton.Visible = on
end

-- ---------------------------------------------------------------------------- toasts
function HUD.toast(text: string, color: Color3?)
	local t = Instance.new("TextLabel")
	t.Name = "Toast"
	t.Size = UDim2.new(1, 0, 0, 0)
	t.AutomaticSize = Enum.AutomaticSize.Y
	t.BackgroundColor3 = Theme.Ink
	t.BackgroundTransparency = 1
	t.Text = text
	t.TextWrapped = true
	t.FontFace = Theme.ui(Enum.FontWeight.SemiBold)
	t.TextSize = 17
	t.TextColor3 = color or Theme.White
	t.TextTransparency = 1
	t.Parent = toasts
	UIKit.corner(t, 10)
	UIKit.padding(t, 8)
	local items: { TextLabel } = {}
	for _, c in toasts:GetChildren() do
		if c:IsA("TextLabel") then
			table.insert(items, c)
		end
	end
	while #items > 3 do
		local oldest = table.remove(items, 1)
		if oldest then
			oldest:Destroy()
		end
	end
	UIKit.tween(t, 0.3, { BackgroundTransparency = 0.25, TextTransparency = 0 })
	task.delay(4.2, function()
		if t.Parent then
			UIKit.tween(t, 0.5, { BackgroundTransparency = 1, TextTransparency = 1 })
			task.delay(0.55, function()
				t:Destroy()
			end)
		end
	end)
end

-- ---------------------------------------------------------------------------- cinematic
function HUD.fade(toBlack: boolean, seconds: number)
	UIKit.tween(fadeFrame, seconds, { BackgroundTransparency = if toBlack then 0 else 1 })
end

-- Black screen right now, then fade back in over `seconds` (used on every zone arrival).
function HUD.arrive(seconds: number)
	fadeFrame.BackgroundTransparency = 0
	UIKit.tween(fadeFrame, seconds, { BackgroundTransparency = 1 })
end

function HUD.letterbox(on: boolean)
	letterboxUsers = math.max(0, letterboxUsers + (if on then 1 else -1))
	local show = letterboxUsers > 0
	if UIKit.reduceMotion then
		topBar.Position = UDim2.fromScale(0, if show then 0 else -0.12)
		bottomBar.Position = UDim2.fromScale(0, if show then 0.88 else 1)
		return
	end
	UIKit.tween(topBar, 0.6, { Position = UDim2.fromScale(0, if show then 0 else -0.12) }, Enum.EasingStyle.Quart)
	UIKit.tween(bottomBar, 0.6, { Position = UDim2.fromScale(0, if show then 0.88 else 1) }, Enum.EasingStyle.Quart)
end

local function hideCard(card: CanvasGroup, my: number)
	UIKit.tween(card, 0.8, { GroupTransparency = 1 })
	task.delay(0.85, function()
		if cardToken == my then
			card.Visible = false
		end
	end)
end

-- Zone intro: letterbox bars slide in, the name and one-line theme fade in, then out.
function HUD.zoneCard(zone: string)
	local z = Progression.zone(zone)
	if not z then
		return
	end
	cardToken += 1
	local my = cardToken
	insightCard.Visible = false
	cardNumeral.Text = z.numeral
	cardName.Text = z.name
	cardTheme.Text = z.theme
	cardLine.BackgroundColor3 = Progression.color(zone)
	cardNumeral.TextColor3 = Progression.color(zone)
	zoneCard.GroupTransparency = 1
	zoneCard.Visible = true
	HUD.letterbox(true)
	task.delay(0.35, function()
		if cardToken ~= my then
			HUD.letterbox(false)
			return
		end
		UIKit.tween(zoneCard, 0.9, { GroupTransparency = 0 })
		task.delay(3.4, function()
			if cardToken ~= my then
				HUD.letterbox(false)
				return
			end
			hideCard(zoneCard, my)
			task.delay(0.5, function()
				HUD.letterbox(false)
			end)
		end)
	end)
end

function HUD.insightCard(zone: string, text: string)
	cardToken += 1
	local my = cardToken
	zoneCard.Visible = false
	insightText.Text = "\u{201C}" .. text .. "\u{201D}"
	insightZone.Text = Progression.name(zone)
	insightHint.Text = "Added to your Journal"
	insightCard.GroupTransparency = 1
	insightCard.Visible = true
	HUD.letterbox(true)
	UIKit.tween(insightCard, 0.8, { GroupTransparency = 0 })
	task.delay(6.5, function()
		if cardToken == my then
			hideCard(insightCard, my)
		end
		HUD.letterbox(false)
	end)
end

function HUD.hideCredits()
	creditsFrame.Visible = false
	for _, c in creditsFrame:GetChildren() do
		c:Destroy()
	end
end

-- Rolls the credits over `seconds` (yields until finished).
function HUD.credits(seconds: number)
	for _, c in creditsFrame:GetChildren() do
		c:Destroy()
	end
	creditsFrame.Visible = true
	local roll = Instance.new("Frame")
	roll.Name = "Roll"
	roll.BackgroundTransparency = 1
	roll.Size = UDim2.new(1, 0, 0, 0)
	roll.AutomaticSize = Enum.AutomaticSize.Y
	roll.Position = UDim2.fromScale(0, 1)
	roll.Parent = creditsFrame
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 18)
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = roll
	local labels: { TextLabel } = {}
	for i, credit in Content.Story.credits do
		if credit.heading ~= "" then
			local h = UIKit.label(roll, "Heading", string.upper(credit.heading), UDim2.new(0.8, 0, 0, 22), UDim2.new(),
				Theme.ui(Enum.FontWeight.Bold), Theme.Cyan, 20)
			h.LayoutOrder = i * 2 - 1
			table.insert(labels, h)
		end
		local big = i <= 2
		local l = UIKit.label(roll, "Line", credit.text, UDim2.new(0.86, 0, 0, if big then 64 else 44), UDim2.new(),
			Theme.title(nil, i == 2), if i == 1 then Theme.Gold else Theme.White, if big then 60 else 40)
		l.LayoutOrder = i * 2
		table.insert(labels, l)
	end
	if UIKit.reduceMotion then
		-- no scrolling: show the credits one after another
		roll.Position = UDim2.fromScale(0, 0.3)
		for _, l in labels do
			l.TextTransparency = 1
		end
		local per = seconds / math.max(#labels, 1)
		for _, l in labels do
			UIKit.tween(l, 0.6, { TextTransparency = 0 })
			task.wait(per)
		end
		task.wait(1)
	else
		task.wait()
		local height = roll.AbsoluteSize.Y
		roll.Position = UDim2.new(0, 0, 0, creditsFrame.AbsoluteSize.Y)
		UIKit.tween(roll, seconds, { Position = UDim2.new(0, 0, 0, -height) }, Enum.EasingStyle.Linear)
		task.wait(seconds)
	end
	creditsFrame.Visible = false
	roll:Destroy()
end

return HUD
