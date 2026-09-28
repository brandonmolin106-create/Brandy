--!strict
-- ReplicatedStorage > Shared > PlayerPolicy  (ModuleScript, used by LocalScripts)
-- Asks Roblox's PolicyService whether media may start by itself and loop for the
-- local player (IsEndlessContentAutoplayAllowed). If the check fails for any
-- reason the SAFE answer is used: no autoplay.

local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local RunService = game:GetService("RunService")

local PlayerPolicy = {}

local cached: boolean? = nil
local inFlight = false

local function fetch(): boolean
	local player = Players.LocalPlayer
	if not player then
		return false
	end
	for attempt = 1, 3 do
		local ok, result = pcall(function()
			return PolicyService:GetPolicyInfoForPlayerAsync(player)
		end)
		if ok and type(result) == "table" then
			return result.IsEndlessContentAutoplayAllowed == true
		end
		warn(`[PlayerPolicy] policy check failed (attempt {attempt}): {result}`)
		task.wait(attempt)
	end
	return false
end

-- May media start by itself and loop for this player? Yields the first time.
-- alwaysInStudio lets Brandon test autoplay in Studio; it never affects live servers.
function PlayerPolicy.autoplayAllowed(alwaysInStudio: boolean?): boolean
	if alwaysInStudio and RunService:IsStudio() then
		return true
	end
	if cached ~= nil then
		return cached
	end
	if inFlight then
		while inFlight do
			task.wait(0.1)
		end
		return cached == true
	end
	inFlight = true
	local allowed = fetch()
	cached = allowed
	inFlight = false
	return allowed
end

return PlayerPolicy
