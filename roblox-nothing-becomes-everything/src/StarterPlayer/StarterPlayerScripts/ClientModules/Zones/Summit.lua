--!strict
-- StarterPlayerScripts > ClientModules > Zones > Summit  (ModuleScript)
-- The Summit and the finale: after the Insight, the finale music plays once,
-- confetti bursts, the sunrise lifts, Brandon's last line plays, the credits roll
-- ("a game by Brandon"), and a portal home opens.

local Modules = script.Parent.Parent
local ZoneContext = require(Modules:WaitForChild("ZoneContext"))
local State = require(Modules:WaitForChild("State"))
local Voice = require(Modules:WaitForChild("Voice"))
local Audio = require(Modules:WaitForChild("Audio"))
local LightingFX = require(Modules:WaitForChild("LightingFX"))
local HUD = require(Modules:WaitForChild("HUD"))
local UIKit = require(Modules:WaitForChild("UIKit"))

local Summit = {}

local bin = ZoneContext.bin()
local ctxRef: ZoneContext.Context? = nil
local running = false

local function portalModel(): Instance?
	local ctx = ctxRef
	local kit = if ctx then ctx.kit else nil
	return if kit then kit:FindFirstChild("HomePortal") else nil
end

local function revealPortal(instant: boolean)
	local portal = portalModel()
	if not portal then
		return
	end
	for _, d in portal:GetDescendants() do
		if d:IsA("BasePart") then
			local target = if d.Name == "Gate" then 0.5 else 0
			if instant then
				d.Transparency = target
			else
				UIKit.tween(d, 1.6, { Transparency = target })
			end
			if d.Name ~= "Gate" then
				d.CanCollide = true
			end
		elseif d:IsA("ParticleEmitter") then
			d.Enabled = true
		elseif d:IsA("PointLight") then
			d.Enabled = true
		elseif d:IsA("ProximityPrompt") then
			d.Enabled = true
		end
	end
end

local function confetti(amount: number)
	local ctx = ctxRef
	local kit = if ctx then ctx.kit else nil
	if not kit then
		return
	end
	for _, d in kit:GetDescendants() do
		if d:IsA("ParticleEmitter") and d.Name == "Burst" then
			d:Emit(amount)
		end
	end
end

local function finale()
	if running then
		return
	end
	running = true
	HUD.setHudVisible(false)
	HUD.letterbox(true)
	Audio.setMusic("finale", "everything")
	task.wait(1)
	Audio.playSfx("finale_boom", 1)
	local amount = if UIKit.reduceMotion then 20 else 70
	confetti(amount)
	LightingFX.shift("everything", {
		clock = 7.4,
		brightness = 3.4,
		exposure = 0.35,
		bloom = 1.3,
		rays = 0.35,
		glare = 1.6,
		atmoColor = Color3.fromRGB(255, 214, 180),
		tint = Color3.fromRGB(255, 244, 232),
	}, 14)
	task.delay(1.6, confetti, amount)
	task.delay(3.4, confetti, amount)
	task.wait(6.5)
	Voice.say("everything_3", true)
	HUD.credits(24)
	revealPortal(false)
	HUD.letterbox(false)
	HUD.setHudVisible(true)
	HUD.toast("A portal home has opened.")
	running = false
end

function Summit.start(ctx: ZoneContext.Context)
	ctxRef = ctx
	running = false
	if ctx.state.finale or State.get().finaleSeen then
		revealPortal(true)
	end
end

function Summit.stop()
	bin:clean()
	if running then
		running = false
		HUD.hideCredits()
		HUD.letterbox(false)
		HUD.setHudVisible(true)
	end
	ctxRef = nil
end

function Summit.onEvent(name: string, _data: { [string]: any })
	if name == "finale" then
		bin:add(task.spawn(finale))
	end
end

return Summit
