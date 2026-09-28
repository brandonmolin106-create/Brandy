--!strict
-- StarterPlayerScripts > ClientModules > Zones > Time  (ModuleScript)
-- The Clock Tower: the gears, dial hands and pendulum are animated by Kinetics;
-- this adds the ticking soundscape (a tick every time the pendulum passes the middle)
-- and Brandon's first line at the foot of the tower. time_2 plays from a beat marker
-- halfway up, and time_3 is the Insight on the roof.

local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))

local Time = {}

local bin = ZoneContext.bin()

function Time.start(ctx: ZoneContext.Context)
	local period = 4
	local kit = ctx.kit
	if kit then
		for _, d in kit:GetDescendants() do
			local p = d:GetAttribute("Period")
			if d:IsA("Model") and d:GetAttribute("Kinetic") == "swing" and type(p) == "number" then
				period = p
			end
		end
	end
	local half = period / 2
	local lastBeat = math.floor(Workspace:GetServerTimeNow() / half)
	bin:add(RunService.Heartbeat:Connect(function()
		local beat = math.floor(Workspace:GetServerTimeNow() / half)
		if beat ~= lastBeat then
			lastBeat = beat
			Audio.playSfx("clock_tick", 0.35)
		end
	end))
	bin:add(task.delay(4.5, function()
		Voice.sayOnce("time_1")
	end))
end

function Time.stop()
	bin:clean()
end

function Time.onEvent(_name: string, _data: { [string]: any }) end

return Time
