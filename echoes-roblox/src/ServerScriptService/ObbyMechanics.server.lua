-- ServerScriptService > ObbyMechanics  (Script)
-- Makes the obstacle parts in Workspace.Obby do their thing. Parts are found
-- by NAME, so you can copy/paste obstacles in Studio and they just work:
--   "KillBrick"       - touching it resets the player to their checkpoint
--   "Spinner"         - spins around its centre (NumberValue "Speed" = degrees/second)
--                       and is deadly to touch
--   "MovingPlatform"  - slides back and forth (Vector3Value "Offset" = how far,
--                       NumberValue "Period" = seconds for a full trip,
--                       NumberValue "Phase" = 0..1 start offset). Carries players.
--   "FadingPlatform"  - fades away shortly after you step on it, then comes back
--                       (NumberValue "FadeTime", NumberValue "ReturnTime" optional)
-- Jump pads are handled on the client (StarterPlayerScripts.JumpPads).

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local obby = Workspace:WaitForChild("Obby")

local function numberChild(part: Instance, name: string, default: number): number
	local value = part:FindFirstChild(name)
	if value and value:IsA("NumberValue") then
		return value.Value
	end
	return default
end

local function humanoidFromHit(hit: BasePart): Humanoid?
	local model = hit:FindFirstAncestorOfClass("Model")
	if not model or not Players:GetPlayerFromCharacter(model) then
		return nil
	end
	return model:FindFirstChildOfClass("Humanoid")
end

------------------------------------------------------------------------------
-- Deadly parts
------------------------------------------------------------------------------
local function makeDeadly(part: BasePart)
	part.Touched:Connect(function(hit: BasePart)
		local humanoid = humanoidFromHit(hit)
		if humanoid and humanoid.Health > 0 then
			humanoid.Health = 0
		end
	end)
end

------------------------------------------------------------------------------
-- Moving platforms and spinners (updated every frame on the server)
------------------------------------------------------------------------------
type Mover = { part: BasePart, origin: CFrame, offset: Vector3, period: number, phase: number }
type Spinner = { part: BasePart, pivot: Vector3, rotation: CFrame, speed: number }

local movers: { Mover } = {}
local spinners: { Spinner } = {}

local function addMover(part: BasePart)
	local offsetValue = part:FindFirstChild("Offset")
	local offset = if offsetValue and offsetValue:IsA("Vector3Value") then offsetValue.Value else Vector3.new(0, 0, 10)
	part.Anchored = true
	table.insert(movers, {
		part = part,
		origin = part.CFrame,
		offset = offset,
		period = math.max(numberChild(part, "Period", 4), 0.5),
		phase = numberChild(part, "Phase", 0),
	})
end

local function addSpinner(part: BasePart)
	part.Anchored = true
	table.insert(spinners, {
		part = part,
		pivot = part.Position,
		rotation = part.CFrame - part.Position,
		speed = math.rad(numberChild(part, "Speed", 90)),
	})
	makeDeadly(part)
end

------------------------------------------------------------------------------
-- Fading platforms
------------------------------------------------------------------------------
local function addFader(part: BasePart)
	local originalTransparency = part.Transparency
	local originalColor = part.Color
	local fadeTime = numberChild(part, "FadeTime", 0.6)
	local returnTime = numberChild(part, "ReturnTime", 2.5)
	local busy = false
	part.Touched:Connect(function(hit: BasePart)
		if busy or not humanoidFromHit(hit) then
			return
		end
		busy = true
		part.Color = Color3.fromRGB(255, 255, 255)
		TweenService:Create(part, TweenInfo.new(fadeTime), {
			Transparency = 0.9,
			Color = originalColor,
		}):Play()
		task.wait(fadeTime)
		part.CanCollide = false
		task.wait(returnTime)
		part.CanCollide = true
		TweenService:Create(part, TweenInfo.new(0.3), { Transparency = originalTransparency }):Play()
		task.wait(0.3)
		busy = false
	end)
end

------------------------------------------------------------------------------
-- Hook everything up
------------------------------------------------------------------------------
for _, descendant in obby:GetDescendants() do
	if descendant:IsA("BasePart") then
		if descendant.Name == "KillBrick" then
			makeDeadly(descendant)
		elseif descendant.Name == "Spinner" then
			addSpinner(descendant)
		elseif descendant.Name == "MovingPlatform" then
			addMover(descendant)
		elseif descendant.Name == "FadingPlatform" then
			addFader(descendant)
		end
	end
end

RunService.Heartbeat:Connect(function()
	-- Shared server clock, so every platform moves in a smooth, predictable rhythm.
	local now = Workspace:GetServerTimeNow()
	for _, mover in movers do
		local omega = 2 * math.pi / mover.period
		local theta = omega * now + mover.phase * 2 * math.pi
		local alpha = (1 - math.cos(theta)) / 2 -- eases in and out at each end
		mover.part.CFrame = mover.origin + mover.offset * alpha
		-- Tell physics how fast it is moving so players standing on it ride along.
		mover.part.AssemblyLinearVelocity = mover.offset * (0.5 * omega * math.sin(theta))
	end
	for _, spinner in spinners do
		local angle = (spinner.speed * now) % (2 * math.pi)
		spinner.part.CFrame = CFrame.new(spinner.pivot) * CFrame.Angles(0, angle, 0) * spinner.rotation
	end
end)
