--!strict
-- StarterPlayerScripts > ClientModules > Journal  (ModuleScript)
-- The Insight Journal: a book with one card per zone. Collected cards show the
-- Insight, its zone and the date it was collected (and can be heard again);
-- locked cards say where to go next.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Content = require(ReplicatedStorage:WaitForChild("Content"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Types = require(Shared:WaitForChild("Types"))
local Progression = require(Shared:WaitForChild("Progression"))
local Theme = require(script.Parent:WaitForChild("Theme"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

local Journal = {}

local gui: ScreenGui
local book: Frame
local counter: TextLabel
local pages: ScrollingFrame
local grid: UIGridLayout
local onListen: (lineId: string) -> () = function() end
local onClick: () -> () = function() end
local latest: Types.Snapshot? = nil

local CARD_BG = Color3.fromRGB(236, 226, 204)

local function build()
	gui = Instance.new("ScreenGui")
	gui.Name = "Journal"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 60
	gui.Enabled = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = (Players.LocalPlayer :: Player):WaitForChild("PlayerGui")

	local shade = Instance.new("TextButton")
	shade.Name = "Shade"
	shade.Size = UDim2.fromScale(1, 1)
	shade.BackgroundColor3 = Color3.new(0, 0, 0)
	shade.BackgroundTransparency = 0.45
	shade.AutoButtonColor = false
	shade.Text = ""
	shade.Parent = gui
	shade.Activated:Connect(function()
		Journal.close()
	end)

	book = UIKit.frame(gui, "Book", UDim2.fromScale(0.92, 0.86), UDim2.fromScale(0.5, 0.5), Theme.Paper, 0)
	book.AnchorPoint = Vector2.new(0.5, 0.5)
	UIKit.sizeLimit(book, 980, 640)
	UIKit.corner(book, 16)
	UIKit.stroke(book, Theme.Gold, 3, 0.2)
	local grad = Instance.new("UIGradient")
	grad.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(250, 244, 228)),
		ColorSequenceKeypoint.new(0.5, Color3.fromRGB(236, 226, 204)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(250, 244, 228)),
	})
	grad.Parent = book

	UIKit.label(book, "Title", "Insight Journal", UDim2.new(0.6, 0, 0, 40), UDim2.fromOffset(20, 12), Theme.title(),
		Theme.PaperInk, 40).TextXAlignment = Enum.TextXAlignment.Left
	counter = UIKit.label(book, "Counter", "", UDim2.new(0.5, 0, 0, 20), UDim2.fromOffset(22, 52), Theme.ui(),
		Color3.fromRGB(120, 100, 86), 18)
	counter.TextXAlignment = Enum.TextXAlignment.Left
	local close = UIKit.button(book, "Close", "Close", UDim2.fromOffset(96, 44), UDim2.new(1, -108, 0, 12))
	close.Activated:Connect(function()
		Journal.close()
	end)

	pages = Instance.new("ScrollingFrame")
	pages.Name = "Pages"
	pages.Position = UDim2.fromOffset(16, 82)
	pages.Size = UDim2.new(1, -32, 1, -96)
	pages.BackgroundTransparency = 1
	pages.BorderSizePixel = 0
	pages.ScrollBarThickness = 6
	pages.ScrollBarImageColor3 = Color3.fromRGB(160, 130, 100)
	pages.AutomaticCanvasSize = Enum.AutomaticSize.Y
	pages.CanvasSize = UDim2.new()
	pages.Parent = book
	grid = Instance.new("UIGridLayout")
	grid.CellPadding = UDim2.fromOffset(10, 10)
	grid.SortOrder = Enum.SortOrder.LayoutOrder
	grid.Parent = pages

	local function relayout()
		local w = book.AbsoluteSize.X
		if w < 640 then
			grid.CellSize = UDim2.new(1, -8, 0, 150)
		else
			grid.CellSize = UDim2.new(0.5, -10, 0, 164)
		end
	end
	book:GetPropertyChangedSignal("AbsoluteSize"):Connect(relayout)
	relayout()
	local camera = Workspace.CurrentCamera
	if camera then
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(relayout)
	end
end

local function card(order: number, zone: Content.Zone, snapshot: Types.Snapshot)
	local collectedAt = snapshot.insights[zone.id]
	local unlocked = Progression.isUnlocked(snapshot.insights, zone.id)
	local color = Progression.color(zone.id)
	local c = UIKit.frame(pages, "Card_" .. zone.id, UDim2.new(), UDim2.new(), CARD_BG, 0)
	c.LayoutOrder = order
	UIKit.corner(c, 12)
	UIKit.stroke(c, if collectedAt then color else Color3.fromRGB(190, 176, 156), if collectedAt then 2 else 1, 0)
	UIKit.padding(c, 10)
	local head = UIKit.label(c, "Zone", `{zone.numeral}  {zone.name}`, UDim2.new(1, 0, 0, 24), UDim2.new(),
		Theme.title(), Theme.PaperInk, 24)
	head.TextXAlignment = Enum.TextXAlignment.Left
	local body: TextLabel
	if collectedAt then
		body = UIKit.label(c, "Insight", "\u{201C}" .. (zone.insight or "") .. "\u{201D}", UDim2.new(1, 0, 1, -64),
			UDim2.fromOffset(0, 28), Theme.title(nil, true), Color3.fromRGB(40, 32, 30), 22)
		local date = UIKit.label(c, "Date", "Collected " .. os.date("%d %b %Y", collectedAt), UDim2.new(0.6, 0, 0, 18),
			UDim2.new(0, 0, 1, -22), Theme.ui(), Color3.fromRGB(130, 110, 94), 15)
		date.TextXAlignment = Enum.TextXAlignment.Left
		local lineId = zone.insightLine
		if lineId then
			local listen = UIKit.button(c, "Listen", "Listen", UDim2.fromOffset(84, 36), UDim2.new(1, -84, 1, -36),
				Color3.fromRGB(60, 46, 40), Theme.Paper)
			listen.Activated:Connect(function()
				onClick()
				onListen(lineId)
			end)
		end
	else
		local previous = Progression.Journey[Progression.index(zone.id) - 1]
		local hint = if unlocked
			then `Waiting for you. Enter the {zone.name} portal in the Clearing.`
			else `Locked. Collect the Insight in {Progression.name(previous or "hub")} first.`
		body = UIKit.label(c, "Locked", hint, UDim2.new(1, 0, 1, -40), UDim2.fromOffset(0, 30), Theme.ui(),
			Color3.fromRGB(130, 110, 94), 18)
	end
	body.TextXAlignment = Enum.TextXAlignment.Left
	body.TextYAlignment = Enum.TextYAlignment.Top
end

function Journal.refresh(snapshot: Types.Snapshot)
	latest = snapshot
	if not gui or not gui.Enabled then
		return
	end
	for _, child in pages:GetChildren() do
		if child:IsA("Frame") then
			child:Destroy()
		end
	end
	local n = 0
	for _, zone in Content.Zones do
		if zone.id ~= "hub" then
			n += 1
			card(n, zone, snapshot)
		end
	end
	counter.Text = `{Progression.collectedCount(snapshot.insights)} of {#Progression.Journey} Insights collected`
end

function Journal.init(listen: (lineId: string) -> (), click: () -> ())
	onListen = listen
	onClick = click
	build()
end

function Journal.open()
	gui.Enabled = true
	local s = latest
	if s then
		Journal.refresh(s)
	end
	book.Position = UDim2.fromScale(0.5, 0.54)
	UIKit.tween(book, 0.35, { Position = UDim2.fromScale(0.5, 0.5) }, Enum.EasingStyle.Back)
end

function Journal.close()
	gui.Enabled = false
end

return Journal
