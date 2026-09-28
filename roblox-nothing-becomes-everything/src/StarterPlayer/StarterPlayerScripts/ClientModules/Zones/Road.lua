--!strict
-- StarterPlayerScripts > ClientModules > Zones > Road  (ModuleScript)
-- The Road. A colossal wall blocks the horizon. It is scaled every frame by how far
-- the player is from it (smoothed, so it glides): it barely changes for most of the
-- walk, then shrinks fast until it is a small rock you can step over. road_3 lands
-- right as the big shrink begins (wall_shrink plays with it).

local RunService = game:GetService("RunService")

local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))

type Piece = { part: BasePart, offset: Vector3, rotation: CFrame, size: Vector3 }

local Road = {}

local bin = ZoneContext.bin()
local MIN_SCALE = 0.004
local ROCK_AT = 0.02

local function smoothstep(x: number): number
	local t = math.clamp(x, 0, 1)
	return t * t * (3 - 2 * t)
end

-- Wall scale for a given distance (studs) between the player and the wall.
function Road.targetScale(d: number, shrinkStart: number, shrinkEnd: number): number
	if d >= 600 then
		return 1
	elseif d >= shrinkStart then
		return 1 - 0.15 * (600 - d) / (600 - shrinkStart)
	elseif d <= shrinkEnd then
		return MIN_SCALE
	end
	return MIN_SCALE + (0.85 - MIN_SCALE) * smoothstep((d - shrinkEnd) / (shrinkStart - shrinkEnd))
end

function Road.start(ctx: ZoneContext.Context)
	local kit = ctx.kit
	if not kit then
		return
	end
	local wall = kit:FindFirstChild("Wall")
	local rockInst = kit:FindFirstChild("Rock")
	local wallZAttr = kit:GetAttribute("WallZ")
	local startAttr = kit:GetAttribute("ShrinkStart")
	local endAttr = kit:GetAttribute("ShrinkEnd")
	if not wall or type(wallZAttr) ~= "number" then
		return
	end
	local wallZ: number = wallZAttr
	local shrinkStart: number = if type(startAttr) == "number" then startAttr else 260
	local shrinkEnd: number = if type(endAttr) == "number" then endAttr else 36
	local pivotAttr = wall:GetAttribute("Pivot")
	local pivot: Vector3 = if typeof(pivotAttr) == "Vector3" then pivotAttr else Vector3.new(0, 0, wallZ)
	local pieces: { Piece } = {}
	for _, d in wall:GetDescendants() do
		if d:IsA("BasePart") then
			table.insert(pieces, {
				part = d,
				offset = d.Position - pivot,
				rotation = d.CFrame.Rotation,
				size = d.Size,
			})
		end
	end
	local rock: BasePart? = if rockInst and rockInst:IsA("BasePart") then rockInst else nil
	local visible = true
	local function apply(s: number)
		local showWall = s > ROCK_AT
		for _, p in pieces do
			p.part.Size = p.size * s
			p.part.CFrame = CFrame.new(pivot + p.offset * s) * p.rotation
			if showWall ~= visible then
				p.part.Transparency = if showWall then 0 else 1
			end
		end
		if showWall ~= visible then
			visible = showWall
			local r = rock
			if r then
				r.Transparency = if showWall then 1 else 0
				r.CanCollide = not showWall
			end
		end
	end
	local function distance(): number?
		local root = ctx.root()
		return if root then root.Position.Z - wallZ else nil
	end
	local current = Road.targetScale(distance() or 600, shrinkStart, shrinkEnd)
	apply(current)
	local shrinking = false
	bin:add(RunService.RenderStepped:Connect(function(dt: number)
		local d = distance()
		if not d then
			return
		end
		if not shrinking and d < shrinkStart then
			shrinking = true
			Audio.playSfx("wall_shrink", 1)
			Voice.sayOnce("road_3")
		end
		local target = Road.targetScale(d, shrinkStart, shrinkEnd)
		current += (target - current) * (1 - math.exp(-dt * 4))
		if math.abs(target - current) < 1e-4 then
			current = target
		end
		apply(current)
	end))
end

function Road.stop()
	bin:clean()
end

function Road.onEvent(_name: string, _data: { [string]: any }) end

return Road
