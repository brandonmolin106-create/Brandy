--!strict
-- StarterPlayerScripts > ClientModules > SettingsMenu  (ModuleScript)
-- Music, Voice and SFX volume sliders (through the SoundGroups), captions on/off,
-- reduce motion, and the Echo Aura switch for owners. Saved with the player's progress.

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Types = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Types"))
local Theme = require(script.Parent:WaitForChild("Theme"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

local SettingsMenu = {}

type Row = { set: (value: any) -> () }

local gui: ScreenGui
local panel: Frame
local rows: { [string]: Row } = {}
local auraRow: Frame
local savedNote: TextLabel
local onChange: (key: string, value: any) -> () = function() end
local onClick: () -> () = function() end

local function slider(parent: Instance, order: number, key: string, title: string)
	local row = UIKit.frame(parent, "Row_" .. key, UDim2.new(1, 0, 0, 56), UDim2.new(), Theme.Navy, 1)
	row.LayoutOrder = order
	local name = UIKit.label(row, "Name", title, UDim2.new(0.55, 0, 0, 22), UDim2.new(), Theme.ui(Enum.FontWeight.SemiBold),
		Theme.White, 20)
	name.TextXAlignment = Enum.TextXAlignment.Left
	local value = UIKit.label(row, "Value", "", UDim2.new(0.3, 0, 0, 22), UDim2.new(0.7, 0, 0, 0), Theme.ui(), Theme.Soft, 18)
	value.TextXAlignment = Enum.TextXAlignment.Right
	local track = UIKit.frame(row, "Track", UDim2.new(1, -16, 0, 10), UDim2.new(0, 8, 0, 36), Theme.NavySoft, 0)
	UIKit.corner(track, 1, 1)
	local fill = UIKit.frame(track, "Fill", UDim2.fromScale(0.5, 1), UDim2.new(), Theme.Cyan, 0)
	UIKit.corner(fill, 1, 1)
	local knob = UIKit.frame(track, "Knob", UDim2.fromOffset(26, 26), UDim2.new(0.5, 0, 0.5, 0), Theme.White, 0)
	knob.AnchorPoint = Vector2.new(0.5, 0.5)
	UIKit.corner(knob, 1, 1)
	UIKit.stroke(knob, Theme.Cyan, 2, 0)
	-- a taller invisible hit area makes the thin track easy to grab on a phone
	local hit = Instance.new("TextButton")
	hit.Name = "Hit"
	hit.Text = ""
	hit.BackgroundTransparency = 1
	hit.Size = UDim2.new(1, 16, 0, 40)
	hit.Position = UDim2.new(0, -8, 0.5, -20)
	hit.Parent = track

	local function show(v: number)
		fill.Size = UDim2.fromScale(v, 1)
		knob.Position = UDim2.new(v, 0, 0.5, 0)
		value.Text = tostring(math.floor(v * 100 + 0.5)) .. "%"
	end
	local dragging = false
	local function fromX(x: number)
		local v = math.clamp((x - track.AbsolutePosition.X) / math.max(track.AbsoluteSize.X, 1), 0, 1)
		v = math.floor(v * 20 + 0.5) / 20
		show(v)
		onChange(key, v)
	end
	hit.InputBegan:Connect(function(input: InputObject)
		if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
			dragging = true
			fromX(input.Position.X)
		end
	end)
	UserInputService.InputChanged:Connect(function(input: InputObject)
		if dragging and (input.UserInputType == Enum.UserInputType.MouseMovement
			or input.UserInputType == Enum.UserInputType.Touch) then
			fromX(input.Position.X)
		end
	end)
	UserInputService.InputEnded:Connect(function(input: InputObject)
		if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
			dragging = false
		end
	end)
	rows[key] = {
		set = function(v: any)
			if type(v) == "number" then
				show(v)
			end
		end,
	}
end

local function toggle(parent: Instance, order: number, key: string, title: string): Frame
	local row = UIKit.frame(parent, "Row_" .. key, UDim2.new(1, 0, 0, 48), UDim2.new(), Theme.Navy, 1)
	row.LayoutOrder = order
	local name = UIKit.label(row, "Name", title, UDim2.new(0.62, 0, 0, 24), UDim2.new(0, 0, 0.5, -12),
		Theme.ui(Enum.FontWeight.SemiBold), Theme.White, 20)
	name.TextXAlignment = Enum.TextXAlignment.Left
	local button = UIKit.button(row, "Switch", "ON", UDim2.fromOffset(84, 40), UDim2.new(1, -84, 0.5, -20))
	local state = false
	local function show(on: boolean)
		state = on
		button.Text = if on then "ON" else "OFF"
		button.BackgroundColor3 = if on then Color3.fromRGB(34, 92, 104) else Theme.NavySoft
	end
	button.Activated:Connect(function()
		onClick()
		show(not state)
		onChange(key, state)
	end)
	rows[key] = {
		set = function(v: any)
			if type(v) == "boolean" then
				show(v)
			end
		end,
	}
	return row
end

function SettingsMenu.init(change: (key: string, value: any) -> (), click: () -> ())
	onChange = change
	onClick = click
	gui = Instance.new("ScreenGui")
	gui.Name = "Settings"
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
	shade.BackgroundTransparency = 0.5
	shade.AutoButtonColor = false
	shade.Text = ""
	shade.Parent = gui
	shade.Activated:Connect(function()
		SettingsMenu.close()
	end)

	panel = UIKit.frame(gui, "Panel", UDim2.fromScale(0.8, 0.86), UDim2.fromScale(0.5, 0.5), Theme.Navy, 0.04)
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	UIKit.sizeLimit(panel, 460, 600)
	UIKit.corner(panel, 16)
	UIKit.stroke(panel, Theme.Cyan, 2, 0.35)
	local title = UIKit.label(panel, "Title", "Settings", UDim2.new(0.6, 0, 0, 36), UDim2.fromOffset(18, 12), Theme.title(),
		Theme.White, 34)
	title.TextXAlignment = Enum.TextXAlignment.Left
	local close = UIKit.button(panel, "Close", "Close", UDim2.fromOffset(92, 44), UDim2.new(1, -104, 0, 10))
	close.Activated:Connect(function()
		SettingsMenu.close()
	end)
	local list = Instance.new("ScrollingFrame")
	list.Name = "List"
	list.Position = UDim2.fromOffset(18, 66)
	list.Size = UDim2.new(1, -36, 1, -80)
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 5
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.Parent = panel
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	slider(list, 1, "music", "Music")
	slider(list, 2, "voice", "Voice")
	slider(list, 3, "sfx", "Sound effects")
	toggle(list, 4, "captions", "Captions")
	toggle(list, 5, "reduceMotion", "Reduce motion")
	auraRow = toggle(list, 6, "aura", "Echo Aura")
	auraRow.Visible = false
	savedNote = UIKit.label(list, "Note", "", UDim2.new(1, 0, 0, 40), UDim2.new(), Theme.ui(), Theme.Dim, 16)
	savedNote.LayoutOrder = 7
end

function SettingsMenu.refresh(snapshot: Types.Snapshot)
	local s = snapshot.settings :: any
	for key, row in rows do
		row.set(s[key])
	end
	auraRow.Visible = snapshot.auraOwned
	savedNote.Text = if snapshot.persistent
		then ""
		else "Progress isn't being saved in this session. (In Studio: turn on API access, see README.)"
end

function SettingsMenu.open()
	gui.Enabled = true
end

function SettingsMenu.close()
	gui.Enabled = false
end

return SettingsMenu
