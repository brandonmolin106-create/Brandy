--!strict
-- StarterPlayerScripts > ClientModules > Captions  (ModuleScript)
-- Captions for every voice line, at the bottom of the screen, timed to the line's
-- region length. Players can switch them off in Settings.

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local Theme = require(script.Parent:WaitForChild("Theme"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

local Captions = {}

local enabled = true
local token = 0
local box: Frame
local speaker: TextLabel
local body: TextLabel

local function textSize(): number
	local camera = Workspace.CurrentCamera
	local h = if camera then camera.ViewportSize.Y else 720
	return math.clamp(math.floor(h * 0.03), 15, 26)
end

function Captions.init()
	local gui = Instance.new("ScreenGui")
	gui.Name = "Captions"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 30
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = (Players.LocalPlayer :: Player):WaitForChild("PlayerGui")

	box = Instance.new("Frame")
	box.Name = "Box"
	box.AnchorPoint = Vector2.new(0.5, 1)
	box.Position = UDim2.new(0.5, 0, 1, -18)
	box.Size = UDim2.new(0.56, 0, 0, 0)
	box.AutomaticSize = Enum.AutomaticSize.Y
	box.BackgroundColor3 = Theme.Ink
	box.BackgroundTransparency = 1
	box.BorderSizePixel = 0
	box.Visible = false
	box.Parent = gui
	UIKit.corner(box, 12)
	UIKit.sizeLimit(box, 820, 400)
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 16)
	pad.PaddingRight = UDim.new(0, 16)
	pad.PaddingTop = UDim.new(0, 8)
	pad.PaddingBottom = UDim.new(0, 10)
	pad.Parent = box
	local layout = Instance.new("UIListLayout")
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Padding = UDim.new(0, 2)
	layout.Parent = box

	speaker = Instance.new("TextLabel")
	speaker.Name = "Speaker"
	speaker.LayoutOrder = 1
	speaker.Size = UDim2.new(1, 0, 0, 16)
	speaker.BackgroundTransparency = 1
	speaker.Text = "BRANDON"
	speaker.FontFace = Theme.ui(Enum.FontWeight.Bold)
	speaker.TextColor3 = Theme.Cyan
	speaker.TextSize = 13
	speaker.TextXAlignment = Enum.TextXAlignment.Left
	speaker.Parent = box

	body = Instance.new("TextLabel")
	body.Name = "Text"
	body.LayoutOrder = 2
	body.Size = UDim2.new(1, 0, 0, 0)
	body.AutomaticSize = Enum.AutomaticSize.Y
	body.BackgroundTransparency = 1
	body.Text = ""
	body.FontFace = Theme.ui(Enum.FontWeight.Medium)
	body.TextColor3 = Theme.White
	body.TextSize = textSize()
	body.TextWrapped = true
	body.TextXAlignment = Enum.TextXAlignment.Left
	body.Parent = box

	local camera = Workspace.CurrentCamera
	if camera then
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(function()
			body.TextSize = textSize()
		end)
	end
end

function Captions.setEnabled(on: boolean)
	enabled = on
	if not on and box then
		box.Visible = false
	end
end

function Captions.isEnabled(): boolean
	return enabled
end

-- Shows text for duration seconds (plus a short tail so it can be read to the end).
function Captions.show(text: string, duration: number)
	token += 1
	local my = token
	if not enabled or not box then
		return
	end
	body.Text = text
	box.Visible = true
	box.BackgroundTransparency = 1
	body.TextTransparency = 1
	speaker.TextTransparency = 1
	UIKit.tween(box, 0.25, { BackgroundTransparency = 0.28 })
	UIKit.tween(body, 0.25, { TextTransparency = 0 })
	UIKit.tween(speaker, 0.25, { TextTransparency = 0 })
	task.delay(duration + 0.6, function()
		if my ~= token then
			return
		end
		UIKit.tween(box, 0.35, { BackgroundTransparency = 1 })
		UIKit.tween(body, 0.35, { TextTransparency = 1 })
		UIKit.tween(speaker, 0.35, { TextTransparency = 1 })
		task.delay(0.4, function()
			if my == token then
				box.Visible = false
			end
		end)
	end)
end

function Captions.hide()
	token += 1
	if box then
		box.Visible = false
	end
end

return Captions
