-- StarterPlayer > StarterPlayerScripts > HUD  (LocalScript)
-- Stage counter at the top of the screen, a little "checkpoint saved" toast,
-- and the celebration message when the player reaches the finish.
-- The stage number itself is saved by the server (ServerScriptService.Checkpoints)
-- in player.leaderstats.Stage - this script only displays it.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage:WaitForChild("Config"))

local player = Players.LocalPlayer
local PURPLE = Color3.fromRGB(170, 90, 255)
local TEAL = Color3.fromRGB(40, 230, 220)
local WHITE = Color3.fromRGB(242, 238, 255)

-- Count the checkpoints so the "/ 15" is always right, even if stages are added.
local obby = Workspace:WaitForChild("Obby")
local totalStages = 0
for _, descendant in obby:GetDescendants() do
	if descendant:IsA("BasePart") and descendant.Name == "Checkpoint" then
		local stage = descendant:FindFirstChild("Stage")
		if stage and stage:IsA("IntValue") then
			totalStages = math.max(totalStages, stage.Value)
		end
	end
end

-- Finish sign text comes from Config too.
local finish = Workspace:WaitForChild("Finish", 30)
local finishSign = finish and finish:FindFirstChild("FinishSign", true)
if finishSign then
	local title = finishSign:FindFirstChild("Title", true)
	local message = finishSign:FindFirstChild("Message", true)
	if title and title:IsA("TextLabel") then
		title.Text = Config.FinishTitle
	end
	if message and message:IsA("TextLabel") then
		message.Text = Config.FinishMessage
	end
end

------------------------------------------------------------------------------
-- GUI
------------------------------------------------------------------------------
local gui = Instance.new("ScreenGui")
gui.Name = "HUD"
gui.ResetOnSpawn = false
gui.DisplayOrder = 5
gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets

local counter = Instance.new("Frame")
counter.Name = "StageCounter"
counter.AnchorPoint = Vector2.new(0.5, 0)
counter.Position = UDim2.new(0.5, 0, 0, 10)
counter.Size = UDim2.fromOffset(250, 44)
counter.BackgroundColor3 = Color3.fromRGB(16, 12, 34)
counter.BackgroundTransparency = 0.2
counter.Parent = gui
local counterCorner = Instance.new("UICorner")
counterCorner.CornerRadius = UDim.new(0, 22)
counterCorner.Parent = counter
local counterStroke = Instance.new("UIStroke")
counterStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
counterStroke.Color = PURPLE
counterStroke.Thickness = 2
counterStroke.Parent = counter

local counterText = Instance.new("TextLabel")
counterText.Name = "Text"
counterText.Size = UDim2.fromScale(1, 1)
counterText.BackgroundTransparency = 1
counterText.Font = Enum.Font.Michroma
counterText.TextSize = 18
counterText.TextColor3 = WHITE
counterText.Text = ""
counterText.Parent = counter

local hint = Instance.new("TextLabel")
hint.Name = "Hint"
hint.AnchorPoint = Vector2.new(0.5, 0)
hint.Position = UDim2.new(0.5, 0, 0, 58)
hint.Size = UDim2.fromOffset(420, 24)
hint.BackgroundTransparency = 1
hint.Font = Enum.Font.GothamMedium
hint.TextSize = 15
hint.TextColor3 = TEAL
hint.TextStrokeTransparency = 0.6
hint.Text = Config.ObbyHint
hint.Parent = gui

local toast = Instance.new("TextLabel")
toast.Name = "Toast"
toast.AnchorPoint = Vector2.new(0.5, 0.5)
toast.Position = UDim2.fromScale(0.5, 0.26)
toast.Size = UDim2.fromOffset(360, 48)
toast.BackgroundColor3 = Color3.fromRGB(16, 12, 34)
toast.BackgroundTransparency = 1
toast.Font = Enum.Font.GothamBold
toast.TextSize = 22
toast.TextColor3 = TEAL
toast.TextTransparency = 1
toast.Text = ""
toast.Parent = gui
local toastCorner = Instance.new("UICorner")
toastCorner.CornerRadius = UDim.new(0, 24)
toastCorner.Parent = toast

-- Celebration panel
local panel = Instance.new("Frame")
panel.Name = "Celebration"
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.Position = UDim2.fromScale(0.5, 0.42)
panel.Size = UDim2.fromScale(0.62, 0.3)
panel.BackgroundColor3 = Color3.fromRGB(14, 10, 32)
panel.BackgroundTransparency = 0.12
panel.Visible = false
panel.Parent = gui
local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 24)
panelCorner.Parent = panel
local panelStroke = Instance.new("UIStroke")
panelStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
panelStroke.Color = WHITE
panelStroke.Thickness = 3
panelStroke.Parent = panel
local panelStrokeGradient = Instance.new("UIGradient")
panelStrokeGradient.Color = ColorSequence.new(PURPLE, TEAL)
panelStrokeGradient.Parent = panelStroke
local panelSize = Instance.new("UISizeConstraint")
panelSize.MinSize = Vector2.new(300, 150)
panelSize.MaxSize = Vector2.new(820, 330)
panelSize.Parent = panel

local panelTitle = Instance.new("TextLabel")
panelTitle.Name = "Title"
panelTitle.AnchorPoint = Vector2.new(0.5, 0)
panelTitle.Position = UDim2.fromScale(0.5, 0.1)
panelTitle.Size = UDim2.fromScale(0.9, 0.36)
panelTitle.BackgroundTransparency = 1
panelTitle.Font = Enum.Font.Michroma
panelTitle.TextScaled = true
panelTitle.TextColor3 = WHITE
panelTitle.Text = Config.FinishTitle
panelTitle.Parent = panel

local panelMessage = Instance.new("TextLabel")
panelMessage.Name = "Message"
panelMessage.AnchorPoint = Vector2.new(0.5, 0)
panelMessage.Position = UDim2.fromScale(0.5, 0.52)
panelMessage.Size = UDim2.fromScale(0.9, 0.3)
panelMessage.BackgroundTransparency = 1
panelMessage.Font = Enum.Font.GothamMedium
panelMessage.TextScaled = true
panelMessage.TextWrapped = true
panelMessage.TextColor3 = TEAL
panelMessage.Text = Config.FinishMessage
panelMessage.Parent = panel

gui.Parent = player:WaitForChild("PlayerGui")

------------------------------------------------------------------------------
-- Behaviour
------------------------------------------------------------------------------
local function showToast(text: string)
	toast.Text = text
	toast.TextTransparency = 0
	toast.BackgroundTransparency = 0.2
	toast.Size = UDim2.fromOffset(300, 40)
	TweenService:Create(toast, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Size = UDim2.fromOffset(360, 48) }):Play()
	task.delay(1.8, function()
		if toast.Text == text then
			local fade = TweenInfo.new(0.6)
			TweenService:Create(toast, fade, { TextTransparency = 1, BackgroundTransparency = 1 }):Play()
		end
	end)
end

local function celebrate()
	panel.Visible = true
	panel.Size = UDim2.fromScale(0.4, 0.2)
	TweenService:Create(panel, TweenInfo.new(0.6, Enum.EasingStyle.Back), { Size = UDim2.fromScale(0.62, 0.3) }):Play()
	TweenService:Create(
		panelStrokeGradient,
		TweenInfo.new(4, Enum.EasingStyle.Linear, Enum.EasingDirection.In, -1),
		{ Rotation = 360 }
	):Play()
	-- Simple confetti
	for _ = 1, 40 do
		local bit = Instance.new("Frame")
		bit.Size = UDim2.fromOffset(math.random(6, 12), math.random(6, 12))
		bit.Position = UDim2.fromScale(math.random(), -0.05)
		bit.BackgroundColor3 = if math.random() < 0.5 then PURPLE else TEAL
		bit.BorderSizePixel = 0
		bit.Rotation = math.random(0, 360)
		bit.Parent = gui
		local fall = TweenInfo.new(2 + math.random() * 2, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		TweenService:Create(bit, fall, {
			Position = UDim2.fromScale(math.random(), 1.1),
			Rotation = bit.Rotation + math.random(-360, 360),
		}):Play()
		task.delay(4.5, function()
			bit:Destroy()
		end)
	end
	task.delay(9, function()
		panel.Visible = false
	end)
end

local lastStage = -1
local function render(stage: number)
	if stage > totalStages and totalStages > 0 then
		counterText.Text = "FINISHED  *  KEEP GOING"
		hint.Visible = false
	elseif stage <= 0 then
		counterText.Text = `STAGE 0 / {totalStages}`
		hint.Visible = true
	else
		counterText.Text = `STAGE {stage} / {totalStages}`
		hint.Visible = false
	end
	if lastStage >= 0 and stage > lastStage then
		if stage > totalStages then
			celebrate()
		else
			showToast(`Checkpoint saved - Stage {stage}`)
		end
	end
	lastStage = stage
end

local leaderstats = player:WaitForChild("leaderstats")
local stageValue = leaderstats:WaitForChild("Stage") :: IntValue
render(stageValue.Value)
stageValue.Changed:Connect(function()
	render(stageValue.Value)
end)
