--!strict
-- StarterPlayerScripts > ClientModules > Zones > Glass  (ModuleScript)
-- The Glass Box. Word blocks drop in (server timeline) and the water rises with each.
-- The water is only a see-through part: nobody can drown, nothing does damage and
-- the player can always walk. Under the surface the screen tints blue and the music
-- is muffled (the "swimming" effect). "Let it go" dissolves a block and drains water.
-- The door was unlocked the whole time; it glows once the water is low. Walking out
-- shatters the box outward.

local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))
local LightingFX = require(Modules:WaitForChild("LightingFX"))
local HUD = require(Modules:WaitForChild("HUD"))
local UIKit = require(Modules:WaitForChild("UIKit"))

type Block = { part: BasePart, rest: CFrame, prompt: ProximityPrompt?, landed: boolean, gone: boolean }

local Glass = {}

local bin = ZoneContext.bin()
local ctxRef: ZoneContext.Context? = nil
local blocks: { [number]: Block } = {}
local total = 0
local present: { number } = {}
local dropped = 0
local doorOpen = false
local exited = false
local lettingGo = false
local glowing = false
local water: BasePart? = nil
local waterStep = 2.8
local boxMin = Vector3.zero
local boxMax = Vector3.zero
local doorwayZ = -math.huge
local door: Model? = nil
local exitSent = 0

local function setBlockVisible(b: Block, visible: boolean)
	b.part.Transparency = if visible then 0 else 1
	b.part.CanCollide = false
	b.part.CanQuery = visible
	for _, d in b.part:GetChildren() do
		if d:IsA("SurfaceGui") then
			d.Enabled = visible
		end
	end
	local p = b.prompt
	if p then
		p.Enabled = false
	end
end

local function waterTop(): number
	local w = water
	return if w then w.Position.Y + w.Size.Y / 2 else boxMin.Y
end

local function setWater(level: number, seconds: number)
	local w = water
	if not w then
		return
	end
	local h = math.max(level, 0.01)
	local size = Vector3.new(w.Size.X, h, w.Size.Z)
	local cf = CFrame.new(w.Position.X, boxMin.Y + h / 2, w.Position.Z)
	if seconds <= 0 then
		w.Size = size
		w.CFrame = cf
	else
		TweenService:Create(w, TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut),
			{ Size = size, CFrame = cf }):Play()
	end
end

local function doorParts(): { BasePart }
	local out = {}
	local d = door
	if d then
		for _, p in d:GetChildren() do
			if p:IsA("BasePart") then
				table.insert(out, p)
			end
		end
	end
	return out
end

local function setDoorGlow(on: boolean)
	glowing = on
	for _, p in doorParts() do
		if string.sub(p.Name, 1, 8) == "DoorGlow" then
			UIKit.tween(p, 1.2, { Transparency = if on then 0.1 else 1 })
			local light = p:FindFirstChildOfClass("PointLight")
			if light then
				light.Enabled = on
			end
		end
	end
end

local function openDoor(instant: boolean)
	doorOpen = true
	local d = door
	if not d then
		return
	end
	local hingeAttr = d:GetAttribute("Hinge")
	local leaf = d:FindFirstChild("DoorLeaf")
	if typeof(hingeAttr) ~= "Vector3" or not leaf or not leaf:IsA("BasePart") then
		return
	end
	local hinge = CFrame.new(hingeAttr.X, leaf.Position.Y, hingeAttr.Z)
	local target = hinge * CFrame.Angles(0, math.rad(100), 0) * hinge:Inverse() * leaf.CFrame
	leaf.CanCollide = false
	local prompt = leaf:FindFirstChildOfClass("ProximityPrompt")
	if prompt then
		prompt.Enabled = false
	end
	if instant then
		leaf.CFrame = target
	else
		TweenService:Create(leaf, TweenInfo.new(1.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = target }):Play()
		Audio.playSfx("whoosh", 0.7)
	end
end

local function boxPieces(): { BasePart }
	local out = {}
	local c = ctxRef
	local kit = if c then c.kit else nil
	local box = if kit then kit:FindFirstChild("Box") else nil
	if box then
		for _, p in box:GetChildren() do
			if p:IsA("BasePart") then
				table.insert(out, p)
			end
		end
	end
	for _, p in doorParts() do
		table.insert(out, p)
	end
	return out
end

local function shatter(instant: boolean)
	exited = true
	for _, p in boxPieces() do
		p.CanCollide = false
		p.CanQuery = false
		if instant then
			p.Transparency = 1
		else
			local outward = p:GetAttribute("Outward")
			local dir = if typeof(outward) == "Vector3" and outward.Magnitude > 0 then outward.Unit else Vector3.yAxis
			local fly = if UIKit.reduceMotion then Vector3.zero else dir * math.random(10, 18) + Vector3.new(0, math.random(3, 8), 0)
			local spin = if UIKit.reduceMotion
				then CFrame.identity
				else CFrame.Angles(math.rad(math.random(-60, 60)), math.rad(math.random(-60, 60)), math.rad(math.random(-60, 60)))
			TweenService:Create(p, TweenInfo.new(1.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
				CFrame = (p.CFrame + fly) * spin,
				Transparency = 1,
			}):Play()
		end
	end
	setWater(0, if instant then 0 else 1.2)
end

local function refreshDoorGlow()
	if not glowing and not exited and dropped >= total and total > 0 and #present <= 1 then
		setDoorGlow(true)
		Voice.sayOnce("glass_2")
	end
end

local function dropBlock(index: number)
	local b = blocks[index]
	if not b or b.gone then
		return
	end
	b.part.CFrame = b.rest + Vector3.new(0, 17, 0)
	setBlockVisible(b, true)
	local fall = TweenService:Create(b.part, TweenInfo.new(if UIKit.reduceMotion then 0.5 else 1.0, Enum.EasingStyle.Bounce,
		Enum.EasingDirection.Out), { CFrame = b.rest })
	fall:Play()
	task.delay(0.45, function()
		Audio.playSfx("heartbeat", 0.9, 0.7)
		local dust = Instance.new("ParticleEmitter")
		dust.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		dust.Color = ColorSequence.new(Color3.fromRGB(200, 214, 230))
		dust.Size = NumberSequence.new(0.5, 0)
		dust.Speed = NumberRange.new(4, 9)
		dust.SpreadAngle = Vector2.new(80, 10)
		dust.Lifetime = NumberRange.new(0.5, 1)
		dust.Rate = 0
		dust.Parent = b.part
		dust:Emit(if UIKit.reduceMotion then 8 else 24)
		task.delay(1.5, function()
			dust:Destroy()
		end)
	end)
	task.delay(1.05, function()
		b.landed = true
		local p = b.prompt
		if p and not b.gone then
			p.Enabled = true
		end
	end)
end

local function dissolve(index: number)
	local b = blocks[index]
	if not b or b.gone then
		return
	end
	b.gone = true
	b.part.CanCollide = false
	local p = b.prompt
	if p then
		p.Enabled = false
	end
	for _, d in b.part:GetChildren() do
		if d:IsA("SurfaceGui") then
			d.Enabled = false
		end
	end
	local sparks = Instance.new("ParticleEmitter")
	sparks.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	sparks.Color = ColorSequence.new(Color3.fromRGB(170, 230, 255), Color3.fromRGB(255, 255, 255))
	sparks.LightEmission = 1
	sparks.Size = NumberSequence.new(0.4, 0)
	sparks.Speed = NumberRange.new(2, 6)
	sparks.Lifetime = NumberRange.new(0.8, 1.6)
	sparks.Acceleration = Vector3.new(0, 6, 0)
	sparks.SpreadAngle = Vector2.new(180, 180)
	sparks.Rate = 0
	sparks.Parent = b.part
	sparks:Emit(if UIKit.reduceMotion then 15 else 45)
	TweenService:Create(b.part, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
		Transparency = 1,
		Size = b.part.Size * 0.6,
	}):Play()
end

function Glass.start(ctx: ZoneContext.Context)
	ctxRef = ctx
	local kit = ctx.kit
	if not kit then
		return
	end
	table.clear(blocks)
	total = 0
	present = table.clone(ctx.state.present)
	dropped = ctx.state.dropped
	doorOpen = false
	exited = false
	glowing = false
	lettingGo = false
	exitSent = 0
	local step = kit:GetAttribute("WaterStep")
	waterStep = if type(step) == "number" then step else 2.8
	local mn, mx, dz = kit:GetAttribute("BoxMin"), kit:GetAttribute("BoxMax"), kit:GetAttribute("DoorwayZ")
	boxMin = if typeof(mn) == "Vector3" then mn else Vector3.zero
	boxMax = if typeof(mx) == "Vector3" then mx else Vector3.zero
	doorwayZ = if type(dz) == "number" then dz else -math.huge
	local w = kit:FindFirstChild("Water")
	water = if w and w:IsA("BasePart") then w else nil
	local d = kit:FindFirstChild("Door")
	door = if d and d:IsA("Model") then d else nil
	local blockFolder = kit:FindFirstChild("Blocks")
	if blockFolder then
		for _, part in blockFolder:GetChildren() do
			local index = part:GetAttribute("Index")
			if part:IsA("BasePart") and type(index) == "number" then
				local b: Block = { part = part, rest = part.CFrame, prompt = part:FindFirstChildOfClass("ProximityPrompt"),
					landed = false, gone = false }
				blocks[index] = b
				total = math.max(total, index)
				if table.find(present, index) then
					setBlockVisible(b, true)
					b.landed = true
					local p = b.prompt
					if p then
						p.Enabled = true
					end
				else
					setBlockVisible(b, false)
					b.gone = index <= dropped -- already let go earlier this visit
				end
			end
		end
	end
	setWater(#present * waterStep, 0)
	if ctx.state.door then
		openDoor(true)
	end
	if ctx.state.exited then
		shatter(true)
	else
		refreshDoorGlow()
	end

	-- underwater tint + muffled music while the camera is below the surface
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "GlassUnderwater"
	cc.TintColor = Color3.fromRGB(150, 205, 255)
	cc.Saturation = -0.1
	cc.Brightness = -0.03
	cc.Enabled = false
	cc.Parent = Lighting
	bin:add(cc)
	local bl = Instance.new("BlurEffect")
	bl.Name = "GlassUnderwaterBlur"
	bl.Size = 5
	bl.Enabled = false
	bl.Parent = Lighting
	bin:add(bl)
	bin:add(function()
		Audio.setUnderwater(false)
	end)
	local under = false
	bin:add(RunService.RenderStepped:Connect(function()
		local camera = Workspace.CurrentCamera
		if not camera then
			return
		end
		local p = camera.CFrame.Position
		local inside = p.X > boxMin.X and p.X < boxMax.X and p.Z > boxMin.Z and p.Z < boxMax.Z and not exited
		local now = inside and p.Y < waterTop() - 0.1
		if now ~= under then
			under = now
			cc.Enabled = now
			bl.Enabled = now
			Audio.setUnderwater(now)
		end
	end))
	-- walking out through the open door
	bin:add(RunService.Heartbeat:Connect(function()
		if not doorOpen or exited or os.clock() - exitSent < 2 then
			return
		end
		local root = ctx.root()
		if root and root.Position.Z < doorwayZ then
			exitSent = os.clock()
			ctx.action("exit")
		end
	end))
	-- blocks become solid once nobody is standing where they landed
	bin:add(task.spawn(function()
		while true do
			task.wait(0.5)
			local root = ctx.root()
			for _, b in blocks do
				if b.landed and not b.gone and not b.part.CanCollide then
					local rel = b.rest:PointToObjectSpace(if root then root.Position else Vector3.new(1e6, 0, 0))
					local clear = math.abs(rel.X) > b.part.Size.X / 2 + 2 or math.abs(rel.Z) > b.part.Size.Z / 2 + 2
					if clear then
						b.part.CanCollide = true
					end
				end
			end
		end
	end))
end

function Glass.stop()
	bin:clean()
	ctxRef = nil
end

function Glass.onEvent(name: string, data: { [string]: any })
	local ctx = ctxRef
	if not ctx then
		return
	end
	if name == "glass_drop" then
		local index = data.index
		if type(index) ~= "number" then
			return
		end
		dropped = math.max(dropped, index)
		if type(data.present) == "table" then
			present = data.present
		end
		dropBlock(index)
		setWater(#present * waterStep, 1.4)
		if index == 1 then
			Voice.sayOnce("glass_1")
			HUD.toast("Hold \"Let it go\" on a word to release it.")
		end
		refreshDoorGlow()
	elseif name == "glass_letgo" then
		local index = data.index
		if type(index) ~= "number" then
			return
		end
		if type(data.present) == "table" then
			present = data.present
		end
		lettingGo = false
		dissolve(index)
		Audio.playSfx("water_drain", 0.9)
		setWater(#present * waterStep, 1.8)
		Voice.sayOnce("glass_3")
		refreshDoorGlow()
	elseif name == "glass_door" then
		openDoor(false)
	elseif name == "glass_exit" then
		Audio.playSfx("glass_shatter", 1)
		shatter(false)
		LightingFX.shift("glass", { brightness = 3.2, exposure = 0.15, saturation = 0.15, bloom = 1.1 }, 2.5)
	elseif name == "prompt" then
		local action = data.action
		if action == "letgo" and type(data.index) == "number" and not lettingGo then
			lettingGo = true
			task.delay(1.5, function()
				lettingGo = false
			end)
			ctx.action("letgo", data.index)
		elseif action == "door" and not doorOpen then
			ctx.action("door")
		end
	end
end

return Glass
