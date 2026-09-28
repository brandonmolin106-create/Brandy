-- ReplicatedStorage > PlayerPolicy  (ModuleScript, used by LocalScripts)
-- Asks Roblox's PolicyService what the local player is allowed to see.
-- If the check fails for any reason, it answers with the SAFE default
-- (no autoplay, no off-platform references), so the game is compliant by default.

local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local RunService = game:GetService("RunService")

export type Policy = {
	checked: boolean, -- true if Roblox actually answered
	autoplayAllowed: boolean, -- IsEndlessContentAutoplayAllowed
	allowedLinks: { string }, -- AllowedExternalLinkReferences (legacy; documented as always empty)
}

local SAFE_DEFAULT: Policy = {
	checked = false,
	autoplayAllowed = false,
	allowedLinks = {},
}

local PlayerPolicy = {}

local cached: Policy? = nil
local inFlight = false

local function fetch(): Policy
	local player = Players.LocalPlayer
	if not player then
		return SAFE_DEFAULT -- only meaningful on the client
	end
	for attempt = 1, 3 do
		local ok, result = pcall(function()
			return PolicyService:GetPolicyInfoForPlayerAsync(player)
		end)
		if ok and type(result) == "table" then
			local links = {}
			local raw = result.AllowedExternalLinkReferences
			if type(raw) == "table" then
				for _, name in raw do
					if type(name) == "string" then
						table.insert(links, name)
					end
				end
			end
			return {
				checked = true,
				autoplayAllowed = result.IsEndlessContentAutoplayAllowed == true,
				allowedLinks = links,
			}
		end
		warn(`[PlayerPolicy] policy check failed (attempt {attempt}): {result}`)
		task.wait(attempt)
	end
	return SAFE_DEFAULT
end

-- Returns the (cached) policy for the local player. Yields the first time.
function PlayerPolicy.get(): Policy
	if cached then
		return cached
	end
	if inFlight then
		while inFlight do
			task.wait(0.1)
		end
		return cached or SAFE_DEFAULT
	end
	inFlight = true
	local policy = fetch()
	cached = policy
	inFlight = false
	return policy
end

-- May media start by itself and loop forever for this player?
-- alwaysInStudio lets Brandon test autoplay in Studio; it never affects live servers.
function PlayerPolicy.autoplayAllowed(alwaysInStudio: boolean?): boolean
	if alwaysInStudio and RunService:IsStudio() then
		return true
	end
	return PlayerPolicy.get().autoplayAllowed
end

-- Is a reference to this off-platform service (e.g. "TikTok") allowed for this player?
function PlayerPolicy.isLinkAllowed(platform: string): boolean
	for _, name in PlayerPolicy.get().allowedLinks do
		if string.lower(name) == string.lower(platform) then
			return true
		end
	end
	return false
end

return PlayerPolicy
