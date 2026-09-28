--!strict
-- StarterPlayerScripts > ClientModules > Zones > Hole  (ModuleScript)
-- The Hole. The steps start hidden in the wall. A glowing Better Thought orb waits;
-- touching it asks the server, and when the server confirms, the next flight of
-- stone steps slides out of the wall, one step at a time (step_rise), and the next
-- orb appears one flight higher. The sky opens as you climb.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))
local LightingFX = require(Modules:WaitForChild("LightingFX"))
local UIKit = require(Modules:WaitForChild("UIKit"))

type Step = { part: BasePart, final: CFrame, hidden: CFrame }

local Hole = {}

local bin = ZoneContext.bin()
local flights: { [number]: { Step } } = {}
local glows: { [number]: { BasePart } } = {}
local orbs: { [number]: Model } = {}
local collected = 0
local waiting = false
local shaft: BasePart? = nil
local spot: SpotLight? = nil
local dust: ParticleEmitter? = nil

local LINES_AT: { [number]: string } = { [1] = "hole_step", [3] = "hole_2", [5] = "hole_3", [7] = "hole_4" }

local function setOrbVisible(model: Model, visible: boolean, fade: boolean)
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then
			local target = if visible then (if d.Name == "Halo" then 0.78 else 0) else 1
			if fade then
				UIKit.tween(d, 0.8, { Transparency = target })
			else
				d.Transparency = target
			end
		elseif d:IsA("PointLight") then
			d.Enabled = visible
		elseif d:IsA("ParticleEmitter") then
			d.Enabled = visible
		elseif d:IsA("BillboardGui") then
			d.Enabled = visible
		end
	end
end

local function setFlight(index: number, risen: boolean)
	local steps = flights[index]
	if steps then
		for _, step in steps do
			step.part.CFrame = if risen then step.final else step.hidden
			step.part.CanCollide = risen
		end
	end
	local g = glows[index]
	if g then
		for _, part in g do
			part.Transparency = if risen then 0.4 else 1
		end
	end
end

local function raiseFlight(index: number)
	local steps: { Step } = flights[index] or {}
	for i, step in steps do
		task.delay((i - 1) * 0.28, function()
			step.part.CanCollide = true
			local tween = TweenService:Create(step.part, TweenInfo.new(if UIKit.reduceMotion then 0.25 else 0.55,
				Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = step.final })
			tween:Play()
			Audio.playSfx("step_rise", 0.75, 0.9 + i * 0.04)
		end)
	end
	task.delay(#steps * 0.28 + 0.4, function()
		local g = glows[index]
		if g then
			for _, part in g do
				UIKit.tween(part, 0.6, { Transparency = 0.4 })
			end
		end
	end)
end

-- More light from above as more Better Thoughts are collected.
local function applyProgress(count: number, seconds: number)
	local t = count / 7
	local s = shaft
	if s then
		UIKit.tween(s, seconds, { Transparency = 1 - 0.13 * t })
	end
	local sp = spot
	if sp then
		TweenService:Create(sp, TweenInfo.new(seconds), { Brightness = 3.5 * t }):Play()
	end
	local d = dust
	if d then
		d.Rate = 18 * t
	end
	LightingFX.shift("hole", {
		brightness = 0.7 + 1.1 * t,
		ambient = Color3.fromRGB(22, 20, 34):Lerp(Color3.fromRGB(70, 76, 110), t),
		outdoor = Color3.fromRGB(34, 34, 56):Lerp(Color3.fromRGB(96, 104, 150), t),
		exposure = 0.25 + 0.35 * t,
		saturation = -0.15 + 0.2 * t,
	}, seconds)
end

-- Carved words below the player fade: they're behind you now.
local function dimCarvings(rootY: number)
	local zones = Workspace:FindFirstChild("Zones")
	local model = if zones then zones:FindFirstChild("hole") else nil
	if not model then
		return
	end
	for _, d in model:GetDescendants() do
		if d:IsA("TextLabel") and string.sub(d.Name, 1, 7) == "Carving" then
			local h = d:GetAttribute("Height")
			if type(h) == "number" then
				d.TextTransparency = if h < rootY - 10 then 0.7 else 0
			end
		end
	end
end

function Hole.start(ctx: ZoneContext.Context)
	local kit = ctx.kit
	if not kit then
		return
	end
	table.clear(flights)
	table.clear(glows)
	table.clear(orbs)
	collected = ctx.state.orbs
	waiting = false
	local centerAttr = kit:GetAttribute("PitCenter")
	local center: Vector3 = if typeof(centerAttr) == "Vector3" then centerAttr else Vector3.zero
	local retractAttr = kit:GetAttribute("Retract")
	local retract: number = if type(retractAttr) == "number" then retractAttr else 8

	local flightFolder = kit:FindFirstChild("Flights")
	if flightFolder then
		for _, folder in flightFolder:GetChildren() do
			local index = folder:GetAttribute("Index")
			if type(index) == "number" then
				local steps: { Step } = {}
				local g: { BasePart } = {}
				for _, d in folder:GetChildren() do
					if d:IsA("BasePart") and d.Name == "LandingGlow" then
						table.insert(g, d)
					elseif d:IsA("BasePart") then
						local out = Vector3.new(d.Position.X - center.X, 0, d.Position.Z - center.Z)
						local dir = if out.Magnitude > 0.01 then out.Unit else Vector3.xAxis
						table.insert(steps, { part = d, final = d.CFrame, hidden = d.CFrame + dir * retract })
					end
				end
				table.sort(steps, function(a, b)
					return (a.part:GetAttribute("Index") :: number? or 0) < (b.part:GetAttribute("Index") :: number? or 0)
				end)
				flights[index] = steps
				glows[index] = g
			end
		end
	end
	for index in flights do
		setFlight(index, index <= collected)
	end

	local orbFolder = kit:FindFirstChild("Orbs")
	if orbFolder then
		for _, m in orbFolder:GetChildren() do
			local index = m:GetAttribute("Index")
			if m:IsA("Model") and type(index) == "number" then
				orbs[index] = m
				setOrbVisible(m, index == collected + 1, false)
			end
		end
	end

	local s = kit:FindFirstChild("LightShaft")
	shaft = if s and s:IsA("BasePart") then s else nil
	local lamp = kit:FindFirstChild("SkyLight")
	if lamp then
		local sp = lamp:FindFirstChildOfClass("SpotLight")
		spot = sp
		local pe = lamp:FindFirstChildOfClass("ParticleEmitter")
		dust = pe
	end
	applyProgress(collected, 0.1)

	-- touching the active orb
	local lastCheck = 0
	bin:add(RunService.Heartbeat:Connect(function()
		if os.clock() - lastCheck < 0.1 then
			return
		end
		lastCheck = os.clock()
		local root = ctx.root()
		if not root then
			return
		end
		local orb = orbs[collected + 1]
		local core = if orb then orb:FindFirstChild("Core") else nil
		if not waiting and core and core:IsA("BasePart") and (root.Position - core.Position).Magnitude < 6 then
			waiting = true
			ctx.action("orb", collected + 1)
			task.delay(2, function()
				waiting = false
			end)
		end
	end))
	-- gently bob the orbs (unless reduce motion)
	local t0 = os.clock()
	bin:add(RunService.RenderStepped:Connect(function()
		if UIKit.reduceMotion then
			return
		end
		local orb = orbs[collected + 1]
		if orb then
			local base = orb:GetAttribute("BaseY")
			local core = orb:FindFirstChild("Core")
			if core and core:IsA("BasePart") then
				if type(base) ~= "number" then
					orb:SetAttribute("BaseY", core.Position.Y)
					base = core.Position.Y
				end
				local y = (base :: number) + math.sin((os.clock() - t0) * 2) * 0.35
				for _, d in orb:GetChildren() do
					if d:IsA("BasePart") then
						d.CFrame = CFrame.new(d.Position.X, y, d.Position.Z)
					end
				end
			end
		end
	end))
	bin:add(task.spawn(function()
		while true do
			local root = ctx.root()
			if root then
				dimCarvings(root.Position.Y)
			end
			task.wait(1.5)
		end
	end))
	if collected == 0 then
		bin:add(task.delay(4.5, function()
			Audio.playSfx("heartbeat", 0.8)
			Voice.sayOnce("hole_1")
		end))
	end
end

function Hole.stop()
	bin:clean()
end

function Hole.onEvent(name: string, data: { [string]: any })
	if name ~= "hole_orb" then
		return
	end
	local count = data.count
	if type(count) ~= "number" or count <= collected then
		return
	end
	local orb = orbs[count]
	collected = count
	waiting = false
	if orb then
		local core = orb:FindFirstChild("Core")
		local sparkle = if core then core:FindFirstChildOfClass("ParticleEmitter") else nil
		if sparkle then
			sparkle:Emit(40)
		end
		setOrbVisible(orb, false, true)
	end
	Audio.playSfx("collect", 0.9)
	raiseFlight(count)
	applyProgress(count, 2.5)
	local nextOrb = orbs[count + 1]
	if nextOrb then
		task.delay(2.2, function()
			if collected == count then
				setOrbVisible(nextOrb, true, true)
			end
		end)
	end
	local line = LINES_AT[count]
	if line then
		Voice.sayOnce(line)
	end
end

return Hole
