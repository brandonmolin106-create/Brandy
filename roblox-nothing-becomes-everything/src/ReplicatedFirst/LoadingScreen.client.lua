--!strict
-- ReplicatedFirst > LoadingScreen  (LocalScript)
-- Custom loading screen: Brandon's loading image (Config.LoadingImageId) or, until it
-- is uploaded, a matching built-in title card; a glowing progress bar; then a fade.
-- Stays at least Config.MinLoadingSeconds and never more than 15 seconds.

local ReplicatedFirst = game:GetService("ReplicatedFirst")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ContentProvider = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

ReplicatedFirst:RemoveDefaultLoadingScreen()

local startedAt = os.clock()
local playerGui = (Players.LocalPlayer :: Player):WaitForChild("PlayerGui")

local DEEP = Color3.fromRGB(6, 7, 20)
local CYAN = Color3.fromRGB(120, 225, 240)
local VIOLET = Color3.fromRGB(150, 110, 255)
local WHITE = Color3.fromRGB(245, 245, 245)
local SOFT = Color3.fromRGB(200, 208, 232)
local TITLE = Font.fromEnum(Enum.Font.Fantasy)
local UI = Font.new(Font.fromEnum(Enum.Font.BuilderSans).Family, Enum.FontWeight.Bold, Enum.FontStyle.Normal)

local gui = Instance.new("ScreenGui")
gui.Name = "LoadingScreen"
gui.IgnoreGuiInset = true
gui.ScreenInsets = Enum.ScreenInsets.None
gui.ResetOnSpawn = false
gui.DisplayOrder = 1000
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

local background = Instance.new("Frame")
background.Name = "Background"
background.Size = UDim2.fromScale(1, 1)
background.BackgroundColor3 = DEEP
background.BorderSizePixel = 0
background.Parent = gui
local grad = Instance.new("UIGradient")
grad.Color = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(8, 8, 26)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(26, 14, 52)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(6, 20, 34)),
})
grad.Rotation = 90
grad.Parent = background

-- twinkling stars
for _ = 1, 50 do
	local star = Instance.new("Frame")
	local size = math.random(2, 3)
	star.Size = UDim2.fromOffset(size, size)
	star.Position = UDim2.fromScale(math.random(), math.random())
	star.BackgroundColor3 = WHITE
	star.BackgroundTransparency = 0.3 + math.random() * 0.5
	star.BorderSizePixel = 0
	star.Parent = background
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = star
	TweenService:Create(star, TweenInfo.new(1 + math.random() * 2.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut,
		-1, true, math.random() * 2), { BackgroundTransparency = 0.95 }):Play()
end

-- built-in title card (shown until the uploaded loading image has loaded)
local card = Instance.new("Frame")
card.Name = "TitleCard"
card.AnchorPoint = Vector2.new(0.5, 0.5)
card.Position = UDim2.fromScale(0.5, 0.45)
card.Size = UDim2.fromScale(0.9, 0.6)
card.BackgroundTransparency = 1
card.Parent = gui

local ring = Instance.new("Frame")
ring.Name = "Emblem"
ring.AnchorPoint = Vector2.new(0.5, 0)
ring.Position = UDim2.fromScale(0.5, 0)
ring.Size = UDim2.fromScale(0.3, 0.3)
ring.SizeConstraint = Enum.SizeConstraint.RelativeYY
ring.BackgroundColor3 = Color3.fromRGB(12, 12, 34)
ring.Parent = card
local ringCorner = Instance.new("UICorner")
ringCorner.CornerRadius = UDim.new(1, 0)
ringCorner.Parent = ring
local ringStroke = Instance.new("UIStroke")
ringStroke.Color = CYAN
ringStroke.Thickness = 4
ringStroke.Parent = ring
local initial = Instance.new("TextLabel")
initial.Size = UDim2.fromScale(0.6, 0.6)
initial.Position = UDim2.fromScale(0.2, 0.2)
initial.BackgroundTransparency = 1
initial.Text = "B"
initial.FontFace = TITLE
initial.TextColor3 = WHITE
initial.TextScaled = true
initial.Parent = ring

local function label(name: string, text: string, y: number, h: number, font: Font, color: Color3, max: number): TextLabel
	local l = Instance.new("TextLabel")
	l.Name = name
	l.AnchorPoint = Vector2.new(0.5, 0)
	l.Position = UDim2.fromScale(0.5, y)
	l.Size = UDim2.fromScale(1, h)
	l.BackgroundTransparency = 1
	l.Text = text
	l.FontFace = font
	l.TextColor3 = color
	l.TextScaled = true
	l.Parent = card
	local c = Instance.new("UITextSizeConstraint")
	c.MaxTextSize = max
	c.MinTextSize = 10
	c.Parent = l
	return l
end
label("Title1", "NOTHING BECOMES", 0.4, 0.2, TITLE, WHITE, 96)
label("Title2", "EVERYTHING", 0.6, 0.2, TITLE, CYAN, 96)
local byline = label("Byline", "A  GAME  BY  BRANDON", 0.86, 0.07, UI, SOFT, 26)

local image = Instance.new("ImageLabel")
image.Name = "LoadingImage"
image.Size = UDim2.fromScale(1, 1)
image.BackgroundTransparency = 1
image.ScaleType = Enum.ScaleType.Crop
image.ImageTransparency = 1
image.Parent = gui

local status = Instance.new("TextLabel")
status.Name = "Status"
status.AnchorPoint = Vector2.new(0.5, 0.5)
status.Position = UDim2.fromScale(0.5, 0.93)
status.Size = UDim2.fromScale(0.6, 0.03)
status.BackgroundTransparency = 1
status.Text = "Loading..."
status.FontFace = UI
status.TextColor3 = SOFT
status.TextScaled = true
status.Parent = gui
local statusLimit = Instance.new("UITextSizeConstraint")
statusLimit.MaxTextSize = 18
statusLimit.Parent = status

local track = Instance.new("Frame")
track.Name = "Track"
track.AnchorPoint = Vector2.new(0.5, 0.5)
track.Position = UDim2.fromScale(0.5, 0.965)
track.Size = UDim2.new(0.4, 0, 0, 6)
track.BackgroundColor3 = Color3.fromRGB(34, 30, 64)
track.BorderSizePixel = 0
track.Parent = gui
local trackCorner = Instance.new("UICorner")
trackCorner.CornerRadius = UDim.new(1, 0)
trackCorner.Parent = track
local fill = Instance.new("Frame")
fill.Name = "Fill"
fill.Size = UDim2.fromScale(0, 1)
fill.BackgroundColor3 = WHITE
fill.BorderSizePixel = 0
fill.Parent = track
local fillCorner = Instance.new("UICorner")
fillCorner.CornerRadius = UDim.new(1, 0)
fillCorner.Parent = fill
local fillGrad = Instance.new("UIGradient")
fillGrad.Color = ColorSequence.new({
	ColorSequenceKeypoint.new(0, VIOLET),
	ColorSequenceKeypoint.new(0.5, CYAN),
	ColorSequenceKeypoint.new(1, VIOLET),
})
fillGrad.Parent = fill

gui.Parent = playerGui

-- ---------------------------------------------------------------------------- settings
local imageId = 0
local minSeconds = 3
local messages = { "Loading..." }
local config = ReplicatedStorage:WaitForChild("Config", 10)
if config and config:IsA("ModuleScript") then
	local ok, result = pcall(require, config)
	if ok and type(result) == "table" then
		imageId = tonumber(result.LoadingImageId) or 0
		minSeconds = math.max(tonumber(result.MinLoadingSeconds) or 3, 1)
	end
end
local content = ReplicatedStorage:WaitForChild("Content", 10)
if content and content:IsA("ModuleScript") then
	local ok, result = pcall(require, content)
	if ok and type(result) == "table" and type(result.Story) == "table" then
		local list = result.Story.loadingMessages
		if type(list) == "table" and #list > 0 then
			messages = list
		end
		if type(result.Subtitle) == "string" then
			byline.Text = (string.gsub(string.upper(result.Subtitle), " ", "  "))
		end
	end
end

-- ---------------------------------------------------------------------------- preload
local imageReady = imageId <= 0
local preloadDone = imageId <= 0
if imageId > 0 then
	image.Image = "rbxassetid://" .. tostring(math.floor(imageId))
	task.spawn(function()
		local ok = pcall(function()
			ContentProvider:PreloadAsync({ image })
		end)
		preloadDone = true
		if ok and image.IsLoaded then
			imageReady = true
			card.Visible = false
			TweenService:Create(image, TweenInfo.new(0.8), { ImageTransparency = 0 }):Play()
		end
	end)
end
local loaded = game:IsLoaded()
if not loaded then
	task.spawn(function()
		game.Loaded:Wait()
		loaded = true
	end)
end

local shown = 0
local MAX_WAIT = 15
while true do
	local dt = RunService.RenderStepped:Wait()
	local elapsed = os.clock() - startedAt
	local ready = (loaded and preloadDone and elapsed >= minSeconds) or elapsed >= MAX_WAIT
	local target = (if loaded then 0.5 else 0.2) + (if preloadDone then 0.25 else 0) + math.clamp(elapsed / minSeconds, 0, 1) * 0.25
	if ready then
		target = 1
	end
	shown += (target - shown) * (1 - math.exp(-dt * 5))
	fill.Size = UDim2.fromScale(math.clamp(shown, 0, 1), 1)
	fillGrad.Offset = Vector2.new(math.sin(elapsed * 1.5) * 0.4, 0)
	status.Text = messages[(math.floor(elapsed / 1.8) % #messages) + 1]
	if ready and shown > 0.99 then
		break
	end
end
if not imageReady then
	card.Visible = true
end

-- ---------------------------------------------------------------------------- fade out
local FADE = TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
for _, object in gui:GetDescendants() do
	if object:IsA("TextLabel") then
		TweenService:Create(object, FADE, { TextTransparency = 1 }):Play()
	elseif object:IsA("ImageLabel") then
		TweenService:Create(object, FADE, { ImageTransparency = 1 }):Play()
	elseif object:IsA("Frame") then
		TweenService:Create(object, FADE, { BackgroundTransparency = 1 }):Play()
	elseif object:IsA("UIStroke") then
		TweenService:Create(object, FADE, { Transparency = 1 }):Play()
	end
end
task.wait(1)
gui:Destroy()
