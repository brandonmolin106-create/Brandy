-- ReplicatedFirst > LoadingScreen  (LocalScript)
-- Custom loading screen: Brandon's loading image + studio branding + an animated
-- progress bar. Preloads the key assets, waits for the game to load, stays up
-- for at least Config.MinLoadingSeconds, then fades out.
-- The TikTok handle is NOT in the image. It is a separate label that only
-- appears if Roblox's PolicyService allows that reference for this player
-- (with today's rules it never does - see README).

local ReplicatedFirst = game:GetService("ReplicatedFirst")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ContentProvider = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

ReplicatedFirst:RemoveDefaultLoadingScreen()

local startedAt = os.clock()
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local DEEP = Color3.fromRGB(7, 6, 18)
local PURPLE = Color3.fromRGB(170, 90, 255)
local TEAL = Color3.fromRGB(40, 230, 220)
local WHITE = Color3.fromRGB(242, 238, 255)
local SOFT = Color3.fromRGB(196, 186, 232)

-- Safe defaults in case Config can't be read (the screen must never break).
local Config = {
	LoadingImageId = 0,
	MusicId = 0,
	CreatorName = "Brandon",
	StudioName = "Echoes in the Dark",
	CreditLine = "Brandon · Echoes in the Dark",
	Tagline = "",
	LoadingMessages = { "Loading..." },
	SocialPlatform = "TikTok",
	SocialHandleText = "",
	ShowSocialHandleIfAllowed = false,
	MinLoadingSeconds = 4,
}

------------------------------------------------------------------------------
-- Build the GUI first so the player sees it immediately
------------------------------------------------------------------------------
local gui = Instance.new("ScreenGui")
gui.Name = "EchoesLoadingScreen"
gui.IgnoreGuiInset = true
gui.ResetOnSpawn = false
gui.DisplayOrder = 1000
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

local background = Instance.new("Frame")
background.Name = "Background"
background.Size = UDim2.fromScale(1, 1)
background.BackgroundColor3 = DEEP
background.BorderSizePixel = 0
background.ZIndex = 1
background.Parent = gui

local backgroundGradient = Instance.new("UIGradient")
backgroundGradient.Color = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(12, 9, 34)),
	ColorSequenceKeypoint.new(0.55, Color3.fromRGB(30, 12, 56)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(4, 22, 34)),
})
backgroundGradient.Rotation = 90
backgroundGradient.Parent = background

local image = Instance.new("ImageLabel")
image.Name = "LoadingImage"
image.Size = UDim2.fromScale(1, 1)
image.BackgroundTransparency = 1
image.ScaleType = Enum.ScaleType.Crop
image.ImageTransparency = 1
image.ZIndex = 2
image.Parent = gui

-- Twinkling stars (cheap little frames) drawn over everything behind the text.
local starLayer = Instance.new("Frame")
starLayer.Name = "Stars"
starLayer.Size = UDim2.fromScale(1, 1)
starLayer.BackgroundTransparency = 1
starLayer.ZIndex = 3
starLayer.Parent = gui

for _ = 1, 60 do
	local star = Instance.new("Frame")
	local size = math.random(2, 4)
	star.Size = UDim2.fromOffset(size, size)
	star.Position = UDim2.fromScale(math.random(), math.random())
	star.BackgroundColor3 = WHITE
	star.BackgroundTransparency = 0.3 + math.random() * 0.5
	star.BorderSizePixel = 0
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(1, 0)
	corner.Parent = star
	star.Parent = starLayer
	local twinkle = TweenInfo.new(
		1 + math.random() * 2.5,
		Enum.EasingStyle.Sine,
		Enum.EasingDirection.InOut,
		-1,
		true,
		math.random() * 2
	)
	TweenService:Create(star, twinkle, { BackgroundTransparency = 0.95 }):Play()
end

-- Fallback emblem + title, only used when there is no loading image yet.
local fallback = Instance.new("Frame")
fallback.Name = "FallbackTitle"
fallback.AnchorPoint = Vector2.new(0.5, 0.5)
fallback.Position = UDim2.fromScale(0.5, 0.4)
fallback.Size = UDim2.fromScale(0.9, 0.5)
fallback.BackgroundTransparency = 1
fallback.ZIndex = 4
fallback.Parent = gui

local orb = Instance.new("Frame")
orb.Name = "Orb"
orb.AnchorPoint = Vector2.new(0.5, 0)
orb.Position = UDim2.fromScale(0.5, 0)
orb.Size = UDim2.fromScale(0.34, 0.34)
orb.SizeConstraint = Enum.SizeConstraint.RelativeYY
orb.BackgroundColor3 = Color3.fromRGB(20, 12, 44)
orb.ZIndex = 4
orb.Parent = fallback
local orbCorner = Instance.new("UICorner")
orbCorner.CornerRadius = UDim.new(1, 0)
orbCorner.Parent = orb
local orbStroke = Instance.new("UIStroke")
orbStroke.Thickness = 4
orbStroke.Color = WHITE
orbStroke.Parent = orb
local orbStrokeGradient = Instance.new("UIGradient")
orbStrokeGradient.Color = ColorSequence.new(PURPLE, TEAL)
orbStrokeGradient.Parent = orbStroke
TweenService:Create(orbStrokeGradient, TweenInfo.new(6, Enum.EasingStyle.Linear, Enum.EasingDirection.In, -1), {
	Rotation = 360,
}):Play()

local initial = Instance.new("TextLabel")
initial.Name = "Initial"
initial.Size = UDim2.fromScale(1, 1)
initial.BackgroundTransparency = 1
initial.Text = string.sub(Config.CreatorName, 1, 1)
initial.TextColor3 = WHITE
initial.TextScaled = true
initial.Font = Enum.Font.Merriweather
initial.ZIndex = 5
initial.Parent = orb

local fallbackTitle = Instance.new("TextLabel")
fallbackTitle.Name = "Title"
fallbackTitle.AnchorPoint = Vector2.new(0.5, 0)
fallbackTitle.Position = UDim2.fromScale(0.5, 0.44)
fallbackTitle.Size = UDim2.fromScale(1, 0.26)
fallbackTitle.BackgroundTransparency = 1
fallbackTitle.Text = string.upper(Config.StudioName)
fallbackTitle.TextColor3 = WHITE
fallbackTitle.TextScaled = true
fallbackTitle.Font = Enum.Font.Michroma
fallbackTitle.ZIndex = 4
fallbackTitle.Parent = fallback
local titleStroke = Instance.new("UIStroke")
titleStroke.Color = PURPLE
titleStroke.Thickness = 2
titleStroke.Transparency = 0.35
titleStroke.Parent = fallbackTitle

-- Bottom shade so text stays readable over any image.
local shade = Instance.new("Frame")
shade.Name = "BottomShade"
shade.AnchorPoint = Vector2.new(0, 1)
shade.Position = UDim2.fromScale(0, 1)
shade.Size = UDim2.fromScale(1, 0.36)
shade.BackgroundColor3 = Color3.new(0, 0, 0)
shade.BorderSizePixel = 0
shade.ZIndex = 4
shade.Parent = gui
local shadeGradient = Instance.new("UIGradient")
shadeGradient.Rotation = 90
shadeGradient.Transparency = NumberSequence.new({
	NumberSequenceKeypoint.new(0, 1),
	NumberSequenceKeypoint.new(1, 0.25),
})
shadeGradient.Parent = shade

local function makeLabel(name: string, y: number, height: number, maxTextSize: number): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Position = UDim2.fromScale(0.5, y)
	label.Size = UDim2.fromScale(0.86, height)
	label.BackgroundTransparency = 1
	label.TextColor3 = WHITE
	label.TextScaled = true
	label.Font = Enum.Font.GothamMedium
	label.ZIndex = 5
	label.Parent = gui
	local limit = Instance.new("UITextSizeConstraint")
	limit.MaxTextSize = maxTextSize
	limit.MinTextSize = 10
	limit.Parent = label
	return label
end

local creditLabel = makeLabel("Credit", 0.79, 0.055, 38)
creditLabel.Font = Enum.Font.Michroma
creditLabel.Text = Config.CreditLine

local taglineLabel = makeLabel("Tagline", 0.838, 0.034, 22)
taglineLabel.FontFace = Font.new(Font.fromEnum(Enum.Font.Merriweather).Family, Enum.FontWeight.Regular, Enum.FontStyle.Italic)
taglineLabel.TextColor3 = SOFT
taglineLabel.Text = Config.Tagline

local statusLabel = makeLabel("Status", 0.922, 0.03, 18)
statusLabel.TextColor3 = SOFT
statusLabel.Text = "Loading..."

-- Policy-gated handle label: hidden unless PolicyService allows the platform.
local handleLabel = makeLabel("SocialHandle", 0.962, 0.028, 18)
handleLabel.TextColor3 = TEAL
handleLabel.Text = ""
handleLabel.Visible = false

local track = Instance.new("Frame")
track.Name = "ProgressTrack"
track.AnchorPoint = Vector2.new(0.5, 0.5)
track.Position = UDim2.fromScale(0.5, 0.885)
track.Size = UDim2.new(0.42, 0, 0, 8)
track.BackgroundColor3 = Color3.fromRGB(40, 32, 70)
track.BorderSizePixel = 0
track.ZIndex = 5
track.Parent = gui
local trackCorner = Instance.new("UICorner")
trackCorner.CornerRadius = UDim.new(1, 0)
trackCorner.Parent = track
local trackSize = Instance.new("UISizeConstraint")
trackSize.MinSize = Vector2.new(240, 6)
trackSize.Parent = track

local fill = Instance.new("Frame")
fill.Name = "Fill"
fill.Size = UDim2.fromScale(0, 1)
fill.BackgroundColor3 = WHITE
fill.BorderSizePixel = 0
fill.ZIndex = 6
fill.Parent = track
local fillCorner = Instance.new("UICorner")
fillCorner.CornerRadius = UDim.new(1, 0)
fillCorner.Parent = fill
local fillGradient = Instance.new("UIGradient")
fillGradient.Color = ColorSequence.new({
	ColorSequenceKeypoint.new(0, PURPLE),
	ColorSequenceKeypoint.new(0.5, TEAL),
	ColorSequenceKeypoint.new(1, PURPLE),
})
fillGradient.Offset = Vector2.new(-0.5, 0)
fillGradient.Parent = fill
TweenService:Create(fillGradient, TweenInfo.new(2.2, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), {
	Offset = Vector2.new(0.5, 0),
}):Play()

gui.Parent = playerGui

------------------------------------------------------------------------------
-- Read Config (it lives in ReplicatedStorage, which arrives a moment later)
------------------------------------------------------------------------------
local configModule = ReplicatedStorage:WaitForChild("Config", 10)
if configModule and configModule:IsA("ModuleScript") then
	local ok, result = pcall(require, configModule)
	if ok and type(result) == "table" then
		Config = result
	else
		warn("[LoadingScreen] Could not read Config:", result)
	end
end

creditLabel.Text = Config.CreditLine
taglineLabel.Text = Config.Tagline
fallbackTitle.Text = string.upper(Config.StudioName)
initial.Text = string.sub(Config.CreatorName, 1, 1)

local minSeconds = math.max(tonumber(Config.MinLoadingSeconds) or 4, 1)
local imageId = tonumber(Config.LoadingImageId) or 0
local musicId = tonumber(Config.MusicId) or 0
local hasImage = imageId > 0
-- The fallback title stays until the image has actually loaded (a brand-new
-- upload may still be waiting for moderation).
local function showImage()
	fallback.Visible = false
	TweenService:Create(image, TweenInfo.new(0.8), { ImageTransparency = 0 }):Play()
end

-- Social handle: only if PolicyService says this platform may be referenced.
task.spawn(function()
	if not Config.ShowSocialHandleIfAllowed or Config.SocialHandleText == "" then
		return
	end
	local policyModule = ReplicatedStorage:WaitForChild("PlayerPolicy", 10)
	if not (policyModule and policyModule:IsA("ModuleScript")) then
		return
	end
	local ok, allowed = pcall(function()
		return require(policyModule).isLinkAllowed(Config.SocialPlatform)
	end)
	if ok and allowed == true and handleLabel.Parent then
		handleLabel.Text = Config.SocialHandleText
		handleLabel.Visible = true
	end
end)

------------------------------------------------------------------------------
-- Preload key assets (loading image first so it can fade in, then music)
------------------------------------------------------------------------------
local assets: { Instance | string } = {} -- PreloadAsync takes instances and/or content IDs
local imageContent = ""
if hasImage then
	imageContent = "rbxassetid://" .. tostring(imageId)
	image.Image = imageContent
	table.insert(assets, image)
end
if musicId > 0 then
	table.insert(assets, "rbxassetid://" .. tostring(musicId))
end

local assetsTotal = #assets
local assetsDone = 0
local preloadFinished = assetsTotal == 0

if assetsTotal > 0 then
	task.spawn(function()
		local ok, err = pcall(function()
			ContentProvider:PreloadAsync(assets, function(contentId: string, status: Enum.AssetFetchStatus)
				assetsDone += 1
				if contentId == imageContent and status == Enum.AssetFetchStatus.Success then
					showImage()
				end
			end)
		end)
		if not ok then
			warn("[LoadingScreen] Preload problem:", err)
		end
		preloadFinished = true
		-- In case the callback's content ID didn't match exactly.
		if hasImage and image.IsLoaded and fallback.Visible then
			showImage()
		end
	end)
end

local gameLoaded = game:IsLoaded()
if not gameLoaded then
	task.spawn(function()
		game.Loaded:Wait()
		gameLoaded = true
	end)
end

------------------------------------------------------------------------------
-- Animate progress until everything is ready
------------------------------------------------------------------------------
local messages = Config.LoadingMessages
if type(messages) ~= "table" or #messages == 0 then
	messages = { "Loading..." }
end

local shown = 0
local MAX_WAIT = 20 -- never trap a player on the loading screen

while true do
	local dt = RunService.RenderStepped:Wait()
	local elapsed = os.clock() - startedAt
	local assetPart = if assetsTotal > 0 then math.min(assetsDone / assetsTotal, 1) else 1
	if preloadFinished then
		assetPart = 1
	end
	local timePart = math.clamp(elapsed / minSeconds, 0, 1)
	local target = assetPart * 0.4 + (if gameLoaded then 0.35 else 0) + timePart * 0.25
	local ready = (preloadFinished and gameLoaded and elapsed >= minSeconds) or elapsed >= MAX_WAIT
	if ready then
		target = 1
	end
	shown += (target - shown) * (1 - math.exp(-dt * 5))
	fill.Size = UDim2.fromScale(math.clamp(shown, 0, 1), 1)
	local message = messages[(math.floor(elapsed / 1.8) % #messages) + 1]
	statusLabel.Text = `{message}   {math.floor(shown * 100 + 0.5)}%`
	if ready and shown > 0.995 then
		break
	end
end

statusLabel.Text = "Welcome."
task.wait(0.35)

------------------------------------------------------------------------------
-- Fade everything out, then remove the GUI
------------------------------------------------------------------------------
local FADE = TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
for _, object in gui:GetDescendants() do
	if object:IsA("TextLabel") then
		TweenService:Create(object, FADE, { TextTransparency = 1, BackgroundTransparency = 1 }):Play()
	elseif object:IsA("ImageLabel") then
		TweenService:Create(object, FADE, { ImageTransparency = 1, BackgroundTransparency = 1 }):Play()
	elseif object:IsA("Frame") then
		TweenService:Create(object, FADE, { BackgroundTransparency = 1 }):Play()
	elseif object:IsA("UIStroke") then
		TweenService:Create(object, FADE, { Transparency = 1 }):Play()
	end
end
TweenService:Create(background, FADE, { BackgroundTransparency = 1 }):Play()
TweenService:Create(image, FADE, { ImageTransparency = 1 }):Play()
task.wait(1)
gui:Destroy()
