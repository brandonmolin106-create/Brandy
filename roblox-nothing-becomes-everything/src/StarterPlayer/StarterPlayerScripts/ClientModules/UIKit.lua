--!strict
-- StarterPlayerScripts > ClientModules > UIKit  (ModuleScript)
-- Small helpers for building touch-friendly UI in code, plus the "reduce motion"
-- switch that every animation respects.

local TweenService = game:GetService("TweenService")

local Theme = require(script.Parent:WaitForChild("Theme"))

local UIKit = {}

UIKit.reduceMotion = false

function UIKit.frame(parent: Instance, name: string, size: UDim2, position: UDim2, color: Color3?, transparency: number?): Frame
	local f = Instance.new("Frame")
	f.Name = name
	f.Size = size
	f.Position = position
	f.BackgroundColor3 = color or Theme.Navy
	f.BackgroundTransparency = transparency or 0
	f.BorderSizePixel = 0
	f.Parent = parent
	return f
end

function UIKit.label(parent: Instance, name: string, text: string, size: UDim2, position: UDim2, font: Font,
	color: Color3?, maxTextSize: number?): TextLabel
	local l = Instance.new("TextLabel")
	l.Name = name
	l.Size = size
	l.Position = position
	l.BackgroundTransparency = 1
	l.Text = text
	l.FontFace = font
	l.TextColor3 = color or Theme.White
	l.TextScaled = true
	l.TextWrapped = true
	l.Parent = parent
	local c = Instance.new("UITextSizeConstraint")
	c.MaxTextSize = maxTextSize or 32
	c.MinTextSize = 9
	c.Parent = l
	return l
end

function UIKit.button(parent: Instance, name: string, text: string, size: UDim2, position: UDim2,
	color: Color3?, textColor: Color3?): TextButton
	local b = Instance.new("TextButton")
	b.Name = name
	b.Size = size
	b.Position = position
	b.BackgroundColor3 = color or Theme.NavySoft
	b.BackgroundTransparency = 0.12
	b.BorderSizePixel = 0
	b.AutoButtonColor = true
	b.Text = text
	b.FontFace = Theme.ui(Enum.FontWeight.Bold)
	b.TextColor3 = textColor or Theme.White
	b.TextScaled = true
	b.Parent = parent
	local c = Instance.new("UITextSizeConstraint")
	c.MaxTextSize = 20
	c.MinTextSize = 10
	c.Parent = b
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 8)
	pad.PaddingRight = UDim.new(0, 8)
	pad.PaddingTop = UDim.new(0, 6)
	pad.PaddingBottom = UDim.new(0, 6)
	pad.Parent = b
	UIKit.corner(b, 10)
	UIKit.stroke(b, Theme.Cyan, 1.5, 0.45)
	return b
end

function UIKit.corner(parent: Instance, radius: number, scale: number?)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(scale or 0, radius)
	c.Parent = parent
end

function UIKit.stroke(parent: Instance, color: Color3, thickness: number, transparency: number?): UIStroke
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness
	s.Transparency = transparency or 0
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = parent
	return s
end

function UIKit.padding(parent: Instance, px: number)
	local p = Instance.new("UIPadding")
	p.PaddingLeft = UDim.new(0, px)
	p.PaddingRight = UDim.new(0, px)
	p.PaddingTop = UDim.new(0, px)
	p.PaddingBottom = UDim.new(0, px)
	p.Parent = parent
end

function UIKit.sizeLimit(parent: Instance, maxX: number, maxY: number)
	local c = Instance.new("UISizeConstraint")
	c.MaxSize = Vector2.new(maxX, maxY)
	c.Parent = parent
end

-- Tween helper. With reduce motion on, movement tweens (Position/Size/Rotation)
-- snap instantly and fades are shortened.
function UIKit.tween(object: Instance, seconds: number, props: { [string]: any }, style: Enum.EasingStyle?,
	direction: Enum.EasingDirection?): Tween
	local moving = props.Position ~= nil or props.Size ~= nil or props.Rotation ~= nil
	local duration = seconds
	if UIKit.reduceMotion then
		duration = if moving then 0 else seconds * 0.6
	end
	local tween = TweenService:Create(object, TweenInfo.new(duration, style or Enum.EasingStyle.Quad,
		direction or Enum.EasingDirection.Out), props)
	tween:Play()
	return tween
end

return UIKit
