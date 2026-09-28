--!strict
-- StarterPlayerScripts > ClientModules > Kinetics  (ModuleScript)
-- Animates the moving pieces of the local zone kit: models with a "Kinetic"
-- attribute ("rotate" = clock hands, gears; "swing" = the pendulum).
-- Angles come from the server clock, so every player sees the same positions.
-- Each part also gets matching AssemblyLinearVelocity / AssemblyAngularVelocity,
-- so a character standing on a clock hand is carried around with it.

local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

type PartEntry = { part: BasePart, rel: CFrame }
type Item = {
	kind: string,
	pivot: Vector3,
	axis: Vector3,
	speed: number, -- degrees per second (rotate)
	phase: number, -- degrees
	amplitude: number, -- degrees (swing)
	period: number, -- seconds (swing)
	parts: { PartEntry },
}

local Kinetics = {}

local items: { Item } = {}
local connection: RBXScriptConnection? = nil

local function number(inst: Instance, name: string, default: number): number
	local v = inst:GetAttribute(name)
	return if type(v) == "number" then v else default
end

local function vector(inst: Instance, name: string, default: Vector3): Vector3
	local v = inst:GetAttribute(name)
	return if typeof(v) == "Vector3" then v else default
end

-- Angle (radians) and angular speed (radians/second) of an item at time t.
function Kinetics.angle(kind: string, t: number, speed: number, phase: number, amplitude: number, period: number): (number, number)
	if kind == "swing" then
		local w = 2 * math.pi / period
		local a = math.rad(amplitude)
		return a * math.sin(w * t + math.rad(phase)), a * w * math.cos(w * t + math.rad(phase))
	end
	local deg = (phase + speed * t) % 360
	return math.rad(deg), math.rad(speed)
end

local function step()
	local t = Workspace:GetServerTimeNow()
	for _, item in items do
		local angle, omega = Kinetics.angle(item.kind, t, item.speed, item.phase, item.amplitude, item.period)
		local base = CFrame.new(item.pivot) * CFrame.fromAxisAngle(item.axis, angle)
		local w = item.axis * omega
		for _, entry in item.parts do
			local p = entry.part
			if p.Parent then
				local cf = base * entry.rel
				p.CFrame = cf
				p.AssemblyAngularVelocity = w
				p.AssemblyLinearVelocity = w:Cross(cf.Position - item.pivot)
			end
		end
	end
end

-- Starts animating every Kinetic model under root. Returns a function that stops it.
function Kinetics.bind(root: Instance): () -> ()
	local mine: { Item } = {}
	for _, model in root:GetDescendants() do
		local kind = model:GetAttribute("Kinetic")
		if model:IsA("Model") and (kind == "rotate" or kind == "swing") then
			local pivot = vector(model, "Pivot", model:GetPivot().Position)
			local axis = vector(model, "Axis", Vector3.yAxis)
			if axis.Magnitude < 1e-3 then
				axis = Vector3.yAxis
			end
			local item: Item = {
				kind = kind,
				pivot = pivot,
				axis = axis.Unit,
				speed = number(model, "Speed", 0),
				phase = number(model, "Phase", 0),
				amplitude = number(model, "Amplitude", 0),
				period = math.max(number(model, "Period", 1), 0.1),
				parts = {},
			}
			local inverse = CFrame.new(pivot):Inverse()
			for _, d in model:GetDescendants() do
				if d:IsA("BasePart") then
					table.insert(item.parts, { part = d, rel = inverse * d.CFrame })
				end
			end
			table.insert(mine, item)
			table.insert(items, item)
		end
	end
	if not connection and #items > 0 then
		connection = RunService.PreSimulation:Connect(step)
	end
	return function()
		for _, item in mine do
			local i = table.find(items, item)
			if i then
				table.remove(items, i)
			end
		end
		if #items == 0 and connection then
			connection:Disconnect()
			connection = nil
		end
	end
end

return Kinetics
