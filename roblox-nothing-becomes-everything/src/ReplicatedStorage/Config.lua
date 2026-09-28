--!strict
-- ReplicatedStorage > Config  (ModuleScript)
-- ============================================================================
--  NOTHING BECOMES EVERYTHING - the ONE place Brandon edits.
--
--  After you upload a file from the "upload" folder, paste its asset ID number
--  here (just the number, like 123456789). 0 means "not uploaded yet".
--  The game works with every ID at 0: captions still show, the screens show a
--  "Brandon's video goes here" panel, and the shop items stay hidden.
-- ============================================================================

local Config = {
	-- ===== AUDIO (free uploads) ==============================================
	VoicePackId = 0, -- Audio : upload/voice_pack.ogg  (all 24 of Brandon's lines)
	SfxPackId = 0, -- Audio : upload/sfx_pack.ogg    (all 14 sound effects)
	MusicPackId = 0, -- Audio : upload/music_pack.ogg  (all 8 music tracks)

	-- ===== LOADING SCREEN (free upload) ======================================
	LoadingImageId = 0, -- Image : upload/loading_screen.png  (or loading_screen_no_photo.png)

	-- ===== VIDEOS (optional, 2,000 Robux EACH, see README) ===================
	-- One screen per zone. Leave 0 to keep the "Brandon's video goes here" panel.
	Videos = {
		hub = 0, -- upload/videos/video_hub.mp4        (The Clearing)
		time = 0, -- upload/videos/video_time.mp4       (The Clock Tower)
		hole = 0, -- upload/videos/video_hole.mp4       (The Hole)
		glass = 0, -- upload/videos/video_glass.mp4      (The Glass Box)
		road = 0, -- upload/videos/video_road.mp4       (The Road)
		chains = 0, -- upload/videos/video_chains.mp4     (Chains)
		everything = 0, -- upload/videos/video_everything.mp4 (The Summit)
	} :: { [string]: number },

	-- ===== OPTIONAL SHOP (hidden while 0) ====================================
	GamePassId = 0, -- Game pass "Echo Aura" (a soft particle trail)
	DevProductIds = {
		TipBrandon = 0, -- Developer product "Tip Brandon" (the lantern by the campfire)
	} :: { [string]: number },

	-- ===== OPTIONAL BADGES (skipped while 0) =================================
	BadgeIds = {
		time = 0, -- collected the Insight in The Clock Tower
		hole = 0, -- ... The Hole
		glass = 0, -- ... The Glass Box
		road = 0, -- ... The Road
		chains = 0, -- ... Chains
		everything = 0, -- ... The Summit
		finale = 0, -- watched the finale
	} :: { [string]: number },

	-- ===== SOUND =============================================================
	DefaultMusicVolume = 0.6, -- 0 to 1 (players can change these in Settings)
	DefaultVoiceVolume = 1.0,
	DefaultSfxVolume = 0.8,
	VideoVolume = 2, -- VideoFrame.Volume (sound comes from the screen and fades with distance)
	MusicCrossfadeSeconds = 2.5,
	MusicDuckWhileTalking = 0.35, -- music plays at this fraction while Brandon talks
	-- Roblox's PolicyService says whether media may start by itself and loop
	-- (IsEndlessContentAutoplayAllowed). If not, music waits for a tap and videos
	-- wait for "Play video" and play once. Studio test sessions always autoplay:
	AlwaysAutoplayInStudio = true,

	-- ===== GAMEPLAY ==========================================================
	MinLoadingSeconds = 3,
	NormalWalkSpeed = 16,
	NormalJumpPower = 50,
	ChainedWalkSpeed = { 7, 10, 13 } :: { number }, -- before the 1st, 2nd and 3rd bell
	ChainedJumpPower = { 25, 32, 40 } :: { number },
	UnchainedWalkSpeed = 26, -- the sprint after the chains break
	UnchainedJumpPower = 60,
	GlassFirstDropSeconds = 3, -- first word block falls this long after you arrive
	GlassDropIntervalSeconds = 3.5,

	-- ===== SAVING ============================================================
	DataStoreName = "NothingBecomesEverything_v1", -- change the name to start everyone fresh
}

return Config
