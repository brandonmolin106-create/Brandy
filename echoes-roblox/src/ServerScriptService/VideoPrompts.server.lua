-- ServerScriptService > VideoPrompts  (Script)
-- When a player presses a video ProximityPrompt (named "VideoPrompt"), tell
-- ONLY that player's game to (re)start that screen's video. Each player watches
-- at their own pace, so one person pressing Restart never interrupts anyone else.
-- Each prompt has a StringValue child "Screen" = "Cinema" or "Billboard".

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local promptEvent = ReplicatedStorage:WaitForChild("Remotes"):WaitForChild("VideoPromptTriggered") :: RemoteEvent

local lastPress: { [Player]: number } = {}

local function hook(prompt: ProximityPrompt)
	local screen = prompt:FindFirstChild("Screen")
	if not (screen and screen:IsA("StringValue")) then
		warn(`[VideoPrompts] {prompt:GetFullName()} needs a StringValue named "Screen"`)
		return
	end
	prompt.Triggered:Connect(function(player: Player)
		if os.clock() - (lastPress[player] or 0) < 0.5 then
			return
		end
		lastPress[player] = os.clock()
		promptEvent:FireClient(player, screen.Value)
	end)
end

for _, descendant in Workspace:GetDescendants() do
	if descendant:IsA("ProximityPrompt") and descendant.Name == "VideoPrompt" then
		hook(descendant)
	end
end

game:GetService("Players").PlayerRemoving:Connect(function(player)
	lastPress[player] = nil
end)
