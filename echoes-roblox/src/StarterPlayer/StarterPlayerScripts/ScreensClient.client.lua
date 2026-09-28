-- StarterPlayer > StarterPlayerScripts > ScreensClient  (LocalScript)
-- Runs Brandon's two videos for THIS player:
--   Video 1 -> Workspace.Cinema.Screen      (big screen in the cinema)
--   Video 2 -> Workspace.Billboard.Screen   (giant billboard at the end of the obby)
-- * An ID of 0 in Config shows a "coming soon" message instead (no errors).
-- * If Roblox's PolicyService allows autoplay for this player, videos start by
--   themselves and loop. Otherwise they wait for the player to press Play
--   (ProximityPrompt) and play once each time.
-- * The sound comes out of the screen itself (3D), so it fades with distance.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local PlayerPolicy = require(ReplicatedStorage:WaitForChild("PlayerPolicy"))
local promptEvent = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("VideoPromptTriggered") :: RemoteEvent

type Screen = {
	key: string,
	video: VideoFrame,
	overlay: TextLabel,
	caption: TextLabel?,
	assetId: number,
	volume: number,
	title: string,
	prompts: { ProximityPrompt },
	ready: boolean,
}

local screens: { [string]: Screen } = {}

local function findScreen(key: string, modelName: string, assetId: any, volume: any, title: string): Screen?
	local model = Workspace:WaitForChild(modelName, 30)
	if not model then
		warn(`[ScreensClient] Workspace.{modelName} not found`)
		return nil
	end
	local part = model:WaitForChild("Screen", 10)
	local display = part and part:WaitForChild("Display", 10)
	local video = display and display:WaitForChild("Video", 10)
	local overlay = display and display:WaitForChild("Overlay", 10)
	if not (video and video:IsA("VideoFrame") and overlay and overlay:IsA("TextLabel")) then
		warn(`[ScreensClient] {modelName}.Screen is missing Display/Video/Overlay`)
		return nil
	end
	local caption: TextLabel? = nil
	local captionPart = model:FindFirstChild("Caption")
	local captionLabel = captionPart and captionPart:FindFirstChild("Title", true)
	if captionLabel and captionLabel:IsA("TextLabel") then
		caption = captionLabel
	end
	return {
		key = key,
		video = video,
		overlay = overlay,
		caption = caption,
		assetId = math.floor(tonumber(assetId) or 0),
		volume = tonumber(volume) or 1,
		title = title,
		prompts = {},
		ready = false,
	}
end

local function showOverlay(screen: Screen, text: string)
	screen.overlay.Text = text
	screen.overlay.Visible = true
end

local function hideOverlay(screen: Screen)
	screen.overlay.Visible = false
end

local function setPromptText(screen: Screen, text: string, enabled: boolean)
	for _, prompt in screen.prompts do
		prompt.ActionText = text
		prompt.Enabled = enabled
	end
end

local function waitUntilLoaded(video: VideoFrame, timeout: number): boolean
	local started = os.clock()
	while not video.IsLoaded and os.clock() - started < timeout do
		task.wait(0.25)
	end
	return video.IsLoaded
end

local autoplay = PlayerPolicy.autoplayAllowed(Config.AlwaysAutoplayInStudio)

local function playFromStart(screen: Screen)
	if not screen.ready then
		return
	end
	screen.video.TimePosition = 0
	screen.video:Play()
	hideOverlay(screen)
end

local function setUp(screen: Screen)
	local video = screen.video
	if screen.caption then
		screen.caption.Text = screen.title
	end

	if screen.assetId <= 0 then
		-- Placeholder mode: no video uploaded yet.
		video.Visible = false
		video.Video = ""
		showOverlay(screen, Config.ComingSoonText)
		setPromptText(screen, "Coming soon", false)
		return
	end

	video.Visible = true
	video.Video = "rbxassetid://" .. tostring(screen.assetId)
	video.Volume = screen.volume
	video.Looped = autoplay
	showOverlay(screen, "Loading Brandon's video...")
	setPromptText(screen, "Loading...", false)

	-- Wait (up to 2 minutes) - a brand-new upload can take a while to pass moderation.
	if not waitUntilLoaded(video, 120) then
		showOverlay(screen, Config.ComingSoonText)
		setPromptText(screen, "Coming soon", false)
		warn(`[ScreensClient] {screen.key} video {screen.assetId} did not load (still in moderation, or wrong ID?)`)
		return
	end

	screen.ready = true
	if autoplay then
		setPromptText(screen, "Restart video", true)
		playFromStart(screen)
	else
		setPromptText(screen, "Play video", true)
		showOverlay(screen, "Walk up to a glowing console and press Play to watch Brandon")
		video.Ended:Connect(function()
			showOverlay(screen, "Press Play on a glowing console to watch again")
		end)
	end
end

local cinema = findScreen("Cinema", "Cinema", Config.Video1Id, Config.Video1Volume, Config.Video1Title)
local billboard = findScreen("Billboard", "Billboard", Config.Video2Id, Config.Video2Volume, Config.Video2Title)
if cinema then
	screens.Cinema = cinema
end
if billboard then
	screens.Billboard = billboard
end

-- Each ProximityPrompt named "VideoPrompt" has a StringValue "Screen" saying
-- which screen it controls ("Cinema" or "Billboard").
for _, descendant in Workspace:GetDescendants() do
	if descendant:IsA("ProximityPrompt") and descendant.Name == "VideoPrompt" then
		local target = descendant:FindFirstChild("Screen")
		if target and target:IsA("StringValue") and screens[target.Value] then
			table.insert(screens[target.Value].prompts, descendant)
		end
	end
end

-- The server tells us when *we* pressed a prompt (see ServerScriptService.VideoPrompts).
promptEvent.OnClientEvent:Connect(function(screenKey: any)
	local screen = if type(screenKey) == "string" then screens[screenKey] else nil
	if screen then
		playFromStart(screen)
	end
end)

for _, screen in screens do
	task.spawn(setUp, screen)
end
