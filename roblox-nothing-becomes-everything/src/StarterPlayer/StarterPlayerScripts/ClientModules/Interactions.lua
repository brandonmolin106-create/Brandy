--!strict
-- StarterPlayerScripts > ClientModules > Interactions  (ModuleScript)
-- Client side of the proximity prompts (each prompt has an "Action" attribute):
-- Listen (speech stones), Journal, Play video, and the kit prompts (Let it go, Door,
-- the finale portal). Server prompts (portals, Insights, bells, shop) just get a click
-- sound and a fade here; the server does the work. Speech stones glow while their
-- line is playing, whether it was asked for or auto-played.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local CollectionService = game:GetService("CollectionService")

local State = require(script.Parent:WaitForChild("State"))
local Audio = require(script.Parent:WaitForChild("Audio"))
local Voice = require(script.Parent:WaitForChild("Voice"))
local Journal = require(script.Parent:WaitForChild("Journal"))
local Videos = require(script.Parent:WaitForChild("Videos"))
local ZoneController = require(script.Parent:WaitForChild("ZoneController"))
local UIKit = require(script.Parent:WaitForChild("UIKit"))

local Interactions = {}

local function setGlow(model: Instance, on: boolean)
	local glow = model:FindFirstChild("Glow")
	if not glow or not glow:IsA("BasePart") then
		return
	end
	local light = glow:FindFirstChildOfClass("PointLight")
	if light then
		light.Enabled = on
	end
	UIKit.tween(glow, 0.4, { Transparency = if on then 0 else 0.35 })
end

local function stonesFor(lineId: string): { Instance }
	local out = {}
	for _, model in CollectionService:GetTagged("SpeechStone") do
		if model:GetAttribute("LineId") == lineId then
			table.insert(out, model)
		end
	end
	return out
end

function Interactions.init()
	Voice.Started:Connect(function(lineId: string)
		for _, model in stonesFor(lineId) do
			setGlow(model, true)
		end
	end)
	Voice.Finished:Connect(function(lineId: string)
		for _, model in stonesFor(lineId) do
			setGlow(model, false)
		end
	end)

	ProximityPromptService.PromptTriggered:Connect(function(prompt: ProximityPrompt, player: Player)
		if player ~= Players.LocalPlayer then
			return
		end
		local action = prompt:GetAttribute("Action")
		local zone = prompt:GetAttribute("Zone")
		local index = prompt:GetAttribute("Index")
		local isKitPrompt = prompt:IsDescendantOf(ZoneController.folder())
		if action == "listen" then
			local lineId = prompt:GetAttribute("LineId")
			if type(lineId) == "string" then
				Voice.say(lineId, true)
			end
		elseif action == "journal" then
			Audio.playSfx("ui_click")
			Journal.open()
		elseif action == "video" and type(zone) == "string" then
			Audio.playSfx("ui_click")
			Videos.playRequested(zone)
		elseif action == "letgo" or action == "door" then
			ZoneController.forward("prompt", { action = action, index = index })
		elseif action == "return" then
			if isKitPrompt then
				ZoneController.travel("hub")
			else
				ZoneController.expectTravel()
			end
		elseif action == "portal" and type(zone) == "string" then
			if State.isUnlocked(zone) then
				ZoneController.expectTravel()
			else
				Audio.playSfx("ui_click", 0.5)
			end
		elseif action == "insight" or action == "bell" or action == "tip" or action == "aura" then
			Audio.playSfx("ui_click", 0.7)
		end
	end)
end

return Interactions
