-- ReplicatedStorage > Config  (ModuleScript)
-- ============================================================================
--  ECHOES IN THE DARK - the ONE place to edit.
--
--  Brandon: after you upload each file from the "upload" folder, paste its
--  asset ID number here (just the number, e.g. 123456789).
--  0 means "not uploaded yet". The game still runs with 0 - it just shows
--  "coming soon" on the screens, a plain loading screen, and no music.
-- ============================================================================

local Config = {
	-- ===== ASSET IDS =========================================================
	LoadingImageId = 0, -- Image : upload/loading_screen.png
	Video1Id = 0, -- Video : upload/video1.mp4  (big screen in the cinema)
	Video2Id = 0, -- Video : upload/video2.mp4  (giant billboard at the end of the obby)
	MusicId = 0, -- Audio : upload/music_calm_pad.ogg

	-- ===== TEXT ==============================================================
	CreatorName = "Brandon",
	StudioName = "Echoes in the Dark",
	CreditLine = "Brandon · Echoes in the Dark",
	Tagline = "you. the one reading this. You are amazing.",
	LoadingMessages = {
		"Lighting up the stars...",
		"Take a slow breath in...",
		"...and let it out.",
		"Almost there. Keep going.",
	},
	Video1Title = "Before you sleep: a calming breath",
	Video2Title = "You were made to move",
	ComingSoonText = "Brandon's video is coming soon",
	ObbyHint = "Obstacle course: to your right  >",
	FinishTitle = "You made it.",
	FinishMessage = "You made it. Keep going — Echoes in the Dark",

	-- ===== SOCIAL HANDLE (policy-gated - see README) =========================
	-- Only shown to a player if Roblox's PolicyService lists this platform in
	-- AllowedExternalLinkReferences for them. Roblox documents that field as
	-- legacy and always empty, so with today's rules this NEVER shows.
	-- Roblox only allows social links on the game's page, not inside games.
	SocialPlatform = "TikTok",
	SocialHandleText = "@brandonmolina651 on TikTok",
	ShowSocialHandleIfAllowed = true,

	-- ===== SOUND =============================================================
	MusicVolume = 0.35,
	-- The included music file is 5:20 long: a 64 s fade-in intro, then a
	-- seamless section from 64 s to 256 s that loops forever. If you swap in a
	-- different song, set both of these to 0 to loop the whole file instead.
	MusicLoopStart = 64,
	MusicLoopEnd = 256,
	Video1Volume = 2, -- 0-100 (sound comes from the screen, fades with distance)
	Video2Volume = 3,

	-- Roblox's PolicyService tells us if a player may see media that starts by
	-- itself and loops forever (IsEndlessContentAutoplayAllowed). If not - or
	-- if the check fails - videos wait for the player to press Play, and music
	-- waits for the Music button. Studio test sessions always autoplay:
	AlwaysAutoplayInStudio = true,

	-- ===== GAMEPLAY ==========================================================
	MinLoadingSeconds = 4, -- keep the loading screen up at least this long
	JumpPadPower = 110, -- upward launch speed for jump pads (studs/second)
}

return Config
