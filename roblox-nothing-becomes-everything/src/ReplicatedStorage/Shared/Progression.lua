--!strict
-- ReplicatedStorage > Shared > Progression  (ModuleScript)
-- Zone order and unlock rules, shared by server and client.
-- The Clearing is always open; each journey zone opens when the previous zone's
-- Insight has been collected.

local Content = require(script.Parent.Parent:WaitForChild("Content"))

local Progression = {}

Progression.Journey = {} :: { string } -- journey zones in order (without the hub)
local byId: { [string]: Content.Zone } = {}
local indexOf: { [string]: number } = {}

for _, zone in Content.Zones do
	byId[zone.id] = zone
	if zone.id ~= "hub" then
		table.insert(Progression.Journey, zone.id)
		indexOf[zone.id] = #Progression.Journey
	else
		indexOf[zone.id] = 0
	end
end

function Progression.zone(id: string): Content.Zone?
	return byId[id]
end

function Progression.name(id: string): string
	local zone = byId[id]
	return if zone then zone.name else id
end

function Progression.index(id: string): number
	return indexOf[id] or -1
end

function Progression.isZone(id: any): boolean
	return type(id) == "string" and byId[id] ~= nil
end

function Progression.isJourneyZone(id: string): boolean
	local i = indexOf[id]
	return i ~= nil and i > 0
end

function Progression.isUnlocked(insights: { [string]: number }, id: string): boolean
	local i = indexOf[id]
	if i == nil then
		return false
	end
	if i <= 1 then
		return true -- the hub and the first zone
	end
	return insights[Progression.Journey[i - 1]] ~= nil
end

function Progression.collectedCount(insights: { [string]: number }): number
	local n = 0
	for _, id in Progression.Journey do
		if insights[id] ~= nil then
			n += 1
		end
	end
	return n
end

function Progression.nextZone(id: string): string?
	local i = indexOf[id]
	if i == nil then
		return nil
	end
	return Progression.Journey[i + 1]
end

function Progression.color(id: string): Color3
	local zone = byId[id]
	if not zone then
		return Color3.fromRGB(120, 225, 240)
	end
	local c = zone.color
	return Color3.fromRGB(c[1], c[2], c[3])
end

return Progression
