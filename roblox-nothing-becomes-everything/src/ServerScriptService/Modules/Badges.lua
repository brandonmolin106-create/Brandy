--!strict
-- ServerScriptService > Modules > Badges  (ModuleScript)
-- Awards the optional badges from Config.BadgeIds (0 = no badge, skipped).

local BadgeService = game:GetService("BadgeService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Config"))

local Badges = {}

local awarded: { [Player]: { [number]: boolean } } = {}

function Badges.award(player: Player, key: string)
	local badgeId = Config.BadgeIds[key]
	if type(badgeId) ~= "number" or badgeId <= 0 then
		return
	end
	local mine = awarded[player]
	if not mine then
		mine = {}
		awarded[player] = mine
	end
	if mine[badgeId] then
		return
	end
	mine[badgeId] = true
	task.spawn(function()
		for attempt = 1, 3 do
			local ok, err = pcall(function()
				if not BadgeService:UserHasBadgeAsync(player.UserId, badgeId) then
					BadgeService:AwardBadgeAsync(player.UserId, badgeId)
				end
			end)
			if ok then
				return
			end
			warn(`[Badges] could not award {key} ({badgeId}) to {player.Name} (attempt {attempt}): {err}`)
			task.wait(attempt * 2)
		end
		if awarded[player] then
			awarded[player][badgeId] = nil -- allow another try later this session
		end
	end)
end

function Badges.forget(player: Player)
	awarded[player] = nil
end

return Badges
