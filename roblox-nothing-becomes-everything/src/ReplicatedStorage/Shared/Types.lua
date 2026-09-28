--!strict
-- ReplicatedStorage > Shared > Types  (ModuleScript)
-- Data shapes shared by the server and the client.

export type Settings = {
	music: number, -- 0..1
	voice: number, -- 0..1
	sfx: number, -- 0..1
	captions: boolean,
	reduceMotion: boolean,
	aura: boolean, -- show the Echo Aura (only matters if the player owns it)
}

-- Per-player puzzle state for the zone the player is in (owned by the server).
export type ZoneState = {
	zone: string,
	orbs: number, -- The Hole: Better Thoughts collected (0..7)
	present: { number }, -- The Glass Box: word blocks currently in the box
	dropped: number, -- The Glass Box: blocks dropped so far
	door: boolean, -- The Glass Box: door opened
	exited: boolean, -- The Glass Box: walked out (box shattered)
	bells: { number }, -- Chains: bells rung
	chained: boolean,
	broken: boolean,
	finale: boolean, -- The Summit: finale played this visit
}

export type Snapshot = {
	insights: { [string]: number }, -- zone id -> os.time() when collected
	settings: Settings,
	persistent: boolean, -- false when progress can't be saved (e.g. Studio without API access)
	auraOwned: boolean,
	auraOffered: boolean, -- a game pass id is configured
	tipOffered: boolean, -- a tip product id is configured
	tips: number,
	finaleSeen: boolean,
	zone: string,
	zoneState: ZoneState,
}

local Types = {}

function Types.defaultSettings(musicVolume: number, voiceVolume: number, sfxVolume: number): Settings
	return {
		music = musicVolume,
		voice = voiceVolume,
		sfx = sfxVolume,
		captions = true,
		reduceMotion = false,
		aura = true,
	}
end

function Types.newZoneState(zone: string): ZoneState
	return {
		zone = zone,
		orbs = 0,
		present = {},
		dropped = 0,
		door = false,
		exited = false,
		bells = {},
		chained = false,
		broken = false,
		finale = false,
	}
end

return Types
