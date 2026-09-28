--!strict
-- ServerScriptService > Modules > Chains  (ModuleScript)
-- Zone 5. Walking into the chained area attaches glowing chains to the player's legs
-- (cuffs, beams and a weight, visible to everyone) and slows them down. Each I CAN
-- bell cracks the chains; the third breaks them and gives a sprint boost.
-- Leaving the zone always restores normal movement. A respawn gives a fresh character
-- with normal movement; walking back into the chained area re-attaches the chains
-- if fewer than three bells have been rung.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")
local CollectionService = game:GetService("CollectionService")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local Types = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Types"))

type Sender = (player: Player, name: string, data: { [string]: any }) -> ()

local Chains = {}

local send: Sender = function() end
local areaCFrame: CFrame? = nil
local areaSize: Vector3? = nil
local bellParts: { [number]: BasePart } = {}

local CHAIN_COLOR = Color3.fromRGB(176, 146, 255)
local CRACK_COLOR = Color3.fromRGB(255, 196, 140)

function Chains.init(sender: Sender)
	send = sender
	local kit = ReplicatedStorage:WaitForChild("ZoneKits"):WaitForChild("chains")
	local area = kit:FindFirstChild("ChainArea")
	if area and area:IsA("BasePart") then
		areaCFrame = area.CFrame
		areaSize = area.Size
	end
	for _, inst in CollectionService:GetTagged("Bell") do
		local index = inst:GetAttribute("Index")
		if inst:IsA("BasePart") and type(index) == "number" and inst:IsDescendantOf(Workspace) then
			bellParts[index] = inst
		end
	end
end

local function humanoidOf(player: Player): Humanoid?
	local character = player.Character
	return if character then character:FindFirstChildOfClass("Humanoid") else nil
end

local function rootOf(player: Player): BasePart?
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	return if root and root:IsA("BasePart") then root else nil
end

local function setMovement(player: Player, walk: number, jump: number)
	local humanoid = humanoidOf(player)
	if humanoid then
		humanoid.UseJumpPower = true
		humanoid.WalkSpeed = walk
		humanoid.JumpPower = jump
	end
end

local function removeVisuals(player: Player)
	local character = player.Character
	local model = if character then character:FindFirstChild("Chains") else nil
	if model then
		model:Destroy()
	end
end

local function weld(a: BasePart, b: BasePart)
	local w = Instance.new("WeldConstraint")
	w.Part0 = a
	w.Part1 = b
	w.Parent = a
end

local function cosmeticPart(name: string, shape: Enum.PartType, size: Vector3, color: Color3, material: Enum.Material): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Shape = shape
	p.Size = size
	p.Color = color
	p.Material = material
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Massless = true
	p.CastShadow = false
	p.Anchored = false
	return p
end

local function legs(character: Model): { BasePart }
	local out = {}
	for _, name in { "LeftLowerLeg", "RightLowerLeg", "Left Leg", "Right Leg" } do
		local leg = character:FindFirstChild(name)
		if leg and leg:IsA("BasePart") then
			table.insert(out, leg)
		end
	end
	return out
end

local function attachVisuals(player: Player)
	local character = player.Character
	local root = rootOf(player)
	if not character or not root or character:FindFirstChild("Chains") then
		return
	end
	local model = Instance.new("Model")
	model.Name = "Chains"
	local weight = cosmeticPart("Weight", Enum.PartType.Ball, Vector3.new(2.2, 2.2, 2.2), Color3.fromRGB(44, 40, 56),
		Enum.Material.Metal)
	weight.CFrame = root.CFrame * CFrame.new(0, -2.3, 2.6)
	weight.Parent = model
	weld(root, weight)
	local glow = Instance.new("PointLight")
	glow.Color = CHAIN_COLOR
	glow.Range = 8
	glow.Brightness = 1.2
	glow.Parent = weight
	local weightAttachment = Instance.new("Attachment")
	weightAttachment.Name = "ChainEnd"
	weightAttachment.Parent = weight
	local sparks = Instance.new("ParticleEmitter")
	sparks.Name = "Sparks"
	sparks.Color = ColorSequence.new(CHAIN_COLOR)
	sparks.LightEmission = 1
	sparks.Rate = 6
	sparks.Lifetime = NumberRange.new(0.6, 1.2)
	sparks.Speed = NumberRange.new(1, 2)
	sparks.Size = NumberSequence.new(0.15, 0)
	sparks.Parent = weight
	for i, leg in legs(character) do
		local cuff = cosmeticPart("Cuff", Enum.PartType.Cylinder, Vector3.new(0.5, leg.Size.X + 0.5, leg.Size.X + 0.5),
			CHAIN_COLOR, Enum.Material.Neon)
		cuff.CFrame = leg.CFrame * CFrame.new(0, -leg.Size.Y / 2 + 0.3, 0) * CFrame.Angles(0, 0, math.rad(90))
		cuff.Parent = model
		weld(leg, cuff)
		local a0 = Instance.new("Attachment")
		a0.Name = "ChainStart"
		a0.Parent = cuff
		local beam = Instance.new("Beam")
		beam.Name = "Chain" .. i
		beam.Attachment0 = a0
		beam.Attachment1 = weightAttachment
		beam.Color = ColorSequence.new(CHAIN_COLOR)
		beam.LightEmission = 0.7
		beam.Width0 = 0.32
		beam.Width1 = 0.4
		beam.Segments = 12
		beam.CurveSize0 = 0.6
		beam.CurveSize1 = -0.6
		beam.FaceCamera = true
		beam.Transparency = NumberSequence.new(0.1)
		beam.Parent = model
	end
	model.Parent = character
end

-- Crack the chains a little more for each bell rung.
local function crackVisuals(player: Player, count: number)
	local character = player.Character
	local model = if character then character:FindFirstChild("Chains") else nil
	if not model then
		return
	end
	local t = count / 3
	for _, d in model:GetDescendants() do
		if d:IsA("Beam") then
			d.Color = ColorSequence.new(CHAIN_COLOR:Lerp(CRACK_COLOR, t))
			d.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 0.1 + t * 0.4),
				NumberSequenceKeypoint.new(0.5, 0.4 + t * 0.5),
				NumberSequenceKeypoint.new(1, 0.1 + t * 0.4),
			})
			d.Width0 = 0.32 * (1 - t * 0.5)
			d.Width1 = 0.4 * (1 - t * 0.5)
		elseif d:IsA("BasePart") and d.Name == "Weight" then
			local s = 2.2 * (1 - t * 0.35)
			d.Size = Vector3.new(s, s, s)
		end
	end
end

local function applyChainedMovement(player: Player, state: Types.ZoneState)
	local step = math.clamp(#state.bells + 1, 1, 3)
	setMovement(player, Config.ChainedWalkSpeed[step], Config.ChainedJumpPower[step])
end

-- Called when a player enters or leaves the zone: everything back to normal.
function Chains.reset(player: Player)
	removeVisuals(player)
	setMovement(player, Config.NormalWalkSpeed, Config.NormalJumpPower)
end

-- New character (respawn): it already has normal movement and no chains.
function Chains.onCharacter(_player: Player, state: Types.ZoneState)
	state.chained = false
end

local function insideArea(position: Vector3): boolean
	local cf, size = areaCFrame, areaSize
	if not cf or not size then
		return false
	end
	local p = cf:PointToObjectSpace(position)
	return math.abs(p.X) <= size.X / 2 and math.abs(p.Y) <= size.Y / 2 and math.abs(p.Z) <= size.Z / 2
end

-- Polled by ZoneService while the player is in the chains zone.
function Chains.poll(player: Player, state: Types.ZoneState)
	if state.chained or state.broken or #state.bells >= 3 then
		return
	end
	local root = rootOf(player)
	if not root or not insideArea(root.Position) then
		return
	end
	state.chained = true
	attachVisuals(player)
	crackVisuals(player, #state.bells)
	applyChainedMovement(player, state)
	send(player, "chains_chained", { bells = table.clone(state.bells) })
end

function Chains.ring(player: Player, state: Types.ZoneState, index: number)
	if state.broken or table.find(state.bells, index) then
		return
	end
	local bell = bellParts[index]
	local root = rootOf(player)
	if not bell or not root or (root.Position - bell.Position).Magnitude > 16 then
		return
	end
	table.insert(state.bells, index)
	local count = #state.bells
	send(player, "chains_bell", { index = index, count = count })
	if count >= 3 then
		state.broken = true
		state.chained = false
		removeVisuals(player)
		setMovement(player, Config.UnchainedWalkSpeed, Config.UnchainedJumpPower)
		send(player, "chains_break", {})
	elseif state.chained then
		crackVisuals(player, count)
		applyChainedMovement(player, state)
	end
end

return Chains
