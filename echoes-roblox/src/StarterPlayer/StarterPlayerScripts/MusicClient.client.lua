-- StarterPlayer > StarterPlayerScripts > MusicClient  (LocalScript)
-- Calm background music (SoundService.BackgroundMusic) + a small MUSIC ON/OFF
-- button in the top-right corner. The music gets quieter near a playing video
-- screen so Brandon's voice is easy to hear.
-- If PolicyService does not allow autoplay for this player, the music starts
-- OFF and only plays after the player presses the button.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local PlayerPolicy = require(ReplicatedStorage:WaitForChild("PlayerPolicy"))

local player = Players.LocalPlayer
local music = SoundService:WaitForChild("BackgroundMusic") :: Sound

local musicId = math.floor(tonumber(Config.MusicId) or 0)
if musicId <= 0 then
	warn("[MusicClient] Config.MusicId is 0 - no background music yet.")
	return
end

music.SoundId = "rbxassetid://" .. tostring(musicId)
music.Looped = true
music.Volume = 0
local loopStart = tonumber(Config.MusicLoopStart) or 0
local loopEnd = tonumber(Config.MusicLoopEnd) or 0
if loopEnd > loopStart and loopStart >= 0 then
	-- Plays the fade-in intro once, then loops the seamless middle section.
	music.PlaybackRegionsEnabled = true
	music.LoopRegion = NumberRange.new(loopStart, loopEnd)
end

------------------------------------------------------------------------------
-- The button
------------------------------------------------------------------------------
local gui = Instance.new("ScreenGui")
gui.Name = "MusicToggle"
gui.ResetOnSpawn = false
gui.DisplayOrder = 10
gui.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets

local button = Instance.new("TextButton")
button.Name = "Toggle"
button.AnchorPoint = Vector2.new(1, 0)
button.Position = UDim2.new(1, -12, 0, 12)
button.Size = UDim2.fromOffset(132, 36)
button.BackgroundColor3 = Color3.fromRGB(22, 16, 44)
button.BackgroundTransparency = 0.15
button.AutoButtonColor = true
button.Font = Enum.Font.GothamBold
button.TextSize = 15
button.TextColor3 = Color3.fromRGB(240, 236, 255)
button.Text = "MUSIC: ..."
button.Parent = gui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 18)
corner.Parent = button
local stroke = Instance.new("UIStroke")
stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
stroke.Color = Color3.fromRGB(40, 230, 220)
stroke.Thickness = 1.5
stroke.Transparency = 0.2
stroke.Parent = button

gui.Parent = player:WaitForChild("PlayerGui")

------------------------------------------------------------------------------
-- On/off state
------------------------------------------------------------------------------
local musicOn = false
local everStarted = false

local function refreshButton()
	button.Text = if musicOn then "MUSIC: ON" else "MUSIC: OFF"
	stroke.Color = if musicOn then Color3.fromRGB(40, 230, 220) else Color3.fromRGB(150, 140, 180)
end

local function setMusic(on: boolean)
	musicOn = on
	if on then
		if everStarted then
			music:Resume()
		else
			everStarted = true
			music:Play()
		end
	end
	refreshButton()
end

button.Activated:Connect(function()
	setMusic(not musicOn)
end)

------------------------------------------------------------------------------
-- Ducking: quieter near a screen that is playing a video
------------------------------------------------------------------------------
type DuckTarget = { part: BasePart, video: VideoFrame, near: number, far: number }
local duckTargets: { DuckTarget } = {}

local function addDuckTarget(modelName: string, near: number, far: number)
	local model = Workspace:WaitForChild(modelName, 30)
	local part = model and model:WaitForChild("Screen", 10)
	local display = part and part:WaitForChild("Display", 10)
	local video = display and display:WaitForChild("Video", 10)
	if part and part:IsA("BasePart") and video and video:IsA("VideoFrame") then
		table.insert(duckTargets, { part = part, video = video, near = near, far = far })
	end
end

task.spawn(addDuckTarget, "Cinema", 45, 100)
task.spawn(addDuckTarget, "Billboard", 110, 260)

local function duckFactor(): number
	local camera = Workspace.CurrentCamera
	if not camera then
		return 1
	end
	local listener = camera.CFrame.Position
	local factor = 1
	for _, target in duckTargets do
		if target.video.Playing then
			local distance = (target.part.Position - listener).Magnitude
			local t = math.clamp((distance - target.near) / (target.far - target.near), 0, 1)
			factor = math.min(factor, 0.35 + 0.65 * t)
		end
	end
	return factor
end

local current = 0
RunService.Heartbeat:Connect(function(dt: number)
	local target = if musicOn then Config.MusicVolume * duckFactor() else 0
	-- Smooth fades (about 1.5 s) for starting, stopping and ducking.
	current += (target - current) * (1 - math.exp(-dt / 1.5))
	if not musicOn and current < 0.003 then
		current = 0
		if music.Playing then
			music:Pause()
		end
	end
	music.Volume = current
end)

------------------------------------------------------------------------------
-- Start: autoplay only if PolicyService allows it for this player
------------------------------------------------------------------------------
refreshButton()
if PlayerPolicy.autoplayAllowed(Config.AlwaysAutoplayInStudio) then
	setMusic(true)
end
