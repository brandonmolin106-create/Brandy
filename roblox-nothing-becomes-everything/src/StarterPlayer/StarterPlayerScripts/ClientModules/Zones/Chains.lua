--!strict
-- StarterPlayerScripts > ClientModules > Zones > Chains  (ModuleScript)
-- Chains (client side). The server attaches the chains and changes the movement;
-- here: Brandon's lines, the bell swing and halo, the shatter burst when the chains
-- break, a quick camera kick, the storm clearing, and the hints.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")

local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))
local LightingFX = require(Modules:WaitForChild("LightingFX"))
local HUD = require(Modules:WaitForChild("HUD"))
local UIKit = require(Modules:WaitForChild("UIKit"))

local Chains = {}

local bin = ZoneContext.bin()
local ctxRef: ZoneContext.Context? = nil
local rung: { number } = {}
local rain: ParticleEmitter? = nil

local function lightHalo(index: number)
	for _, halo in CollectionService:GetTagged("BellHalo") do
		if halo:GetAttribute("Index") == index and halo:IsA("BasePart") then
			UIKit.tween(halo, 0.6, { Transparency = 0.15 })
			local light = halo:FindFirstChildOfClass("PointLight")
			if light then
				light.Brightness = 2.5
			end
		end
	end
end

local function resetHalos()
	for _, halo in CollectionService:GetTagged("BellHalo") do
		if halo:IsA("BasePart") then
			local index = halo:GetAttribute("Index")
			local on = type(index) == "number" and table.find(rung, index) ~= nil
			halo.Transparency = if on then 0.15 else 0.75
			local light = halo:FindFirstChildOfClass("PointLight")
			if light then
				light.Brightness = if on then 2.5 else 0.8
			end
		end
	end
end

local function swingBell(index: number)
	for _, body in CollectionService:GetTagged("Bell") do
		local pivotAttr = body:GetAttribute("Pivot")
		if body:GetAttribute("Index") == index and body:IsA("BasePart") and typeof(pivotAttr) == "Vector3" then
			local start = body.CFrame
			local pivot = CFrame.new(pivotAttr) * start.Rotation
			local rel = pivot:Inverse() * start
			local t = 0
			local conn: RBXScriptConnection
			conn = RunService.RenderStepped:Connect(function(dt: number)
				t += dt
				if t > 2.6 or not body.Parent then
					conn:Disconnect()
					if body.Parent then
						body.CFrame = start
					end
					return
				end
				local amp = if UIKit.reduceMotion then 6 else 22
				local angle = math.rad(amp) * math.exp(-t * 1.4) * math.sin(t * 8)
				body.CFrame = pivot * CFrame.Angles(angle, 0, 0) * rel
			end)
			bin:add(conn)
		end
	end
end

local function breakBurst()
	local ctx = ctxRef
	local root = if ctx then ctx.root() else nil
	if not root then
		return
	end
	local a = Instance.new("Attachment")
	a.Position = Vector3.new(0, -2.2, 0)
	a.Parent = root
	local burst = Instance.new("ParticleEmitter")
	burst.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	burst.Color = ColorSequence.new(Color3.fromRGB(196, 146, 255), Color3.fromRGB(255, 214, 140))
	burst.LightEmission = 1
	burst.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 0) })
	burst.Speed = NumberRange.new(12, 26)
	burst.SpreadAngle = Vector2.new(180, 180)
	burst.Lifetime = NumberRange.new(0.6, 1.4)
	burst.Drag = 3
	burst.Rate = 0
	burst.Parent = a
	burst:Emit(if UIKit.reduceMotion then 30 else 110)
	task.delay(2, function()
		a:Destroy()
	end)
	local camera = Workspace.CurrentCamera
	if camera and not UIKit.reduceMotion then
		local fov = camera.FieldOfView
		local up = TweenService:Create(camera, TweenInfo.new(0.18, Enum.EasingStyle.Quad), { FieldOfView = fov + 14 })
		up:Play()
		up.Completed:Once(function()
			TweenService:Create(camera, TweenInfo.new(0.9, Enum.EasingStyle.Sine), { FieldOfView = fov }):Play()
		end)
	end
end

local function clearStorm(seconds: number)
	local r = rain
	if r then
		r.Enabled = false
	end
	LightingFX.shift("chains", {
		brightness = 2.4,
		ambient = Color3.fromRGB(120, 110, 130),
		outdoor = Color3.fromRGB(150, 140, 170),
		density = 0.3,
		haze = 1.4,
		saturation = 0.1,
		contrast = 0.12,
		exposure = 0.15,
		rays = 0.2,
		clock = 16.4,
	}, seconds)
end

function Chains.start(ctx: ZoneContext.Context)
	ctxRef = ctx
	rung = table.clone(ctx.state.bells)
	rain = nil
	local kit = ctx.kit
	local rainPart = if kit then kit:FindFirstChild("Rain") else nil
	if rainPart then
		rain = rainPart:FindFirstChildOfClass("ParticleEmitter")
	end
	resetHalos()
	bin:add(CollectionService:GetInstanceAddedSignal("BellHalo"):Connect(resetHalos))
	if ctx.state.broken then
		clearStorm(0.1)
	end
end

function Chains.stop()
	bin:clean()
	ctxRef = nil
	table.clear(rung)
end

function Chains.onEvent(name: string, data: { [string]: any })
	if name == "chains_chained" then
		Audio.playSfx("heartbeat", 0.9, 0.8)
		Voice.sayOnce("chains_1")
		HUD.toast("Ring the three I CAN bells.")
	elseif name == "chains_bell" then
		local index, count = data.index, data.count
		if type(index) ~= "number" or type(count) ~= "number" then
			return
		end
		table.insert(rung, index)
		Audio.playSfx("bell", 1)
		swingBell(index)
		lightHalo(index)
		if count < 3 then
			HUD.toast(`I CAN  ({count}/3)`)
		end
	elseif name == "chains_break" then
		Audio.playSfx("chains_break", 1)
		breakBurst()
		clearStorm(3)
		Voice.say("chains_3", true)
		HUD.toast("The chains are gone. Run up the mountain!")
	end
end

return Chains
