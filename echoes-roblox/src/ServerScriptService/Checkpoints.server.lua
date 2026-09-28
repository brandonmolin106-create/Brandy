-- ServerScriptService > Checkpoints  (Script)
-- Server-side checkpoint saving for the obby.
-- * Every stage has a part named "Checkpoint" with an IntValue "Stage".
-- * Workspace.Finish.FinishPad is the last "checkpoint" (stage 16).
-- * Touching a higher checkpoint saves it for that player (leaderstats.Stage).
-- * When a player respawns, they are moved to their last checkpoint.
-- * Workspace.Finish.BackToCinema sends a player back to the cinema (progress kept).
-- Progress is kept for the whole visit (it resets when they leave the server).

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local obby = Workspace:WaitForChild("Obby")
local finish = Workspace:WaitForChild("Finish")
local cinema = Workspace:WaitForChild("Cinema")

local checkpoints: { [number]: BasePart } = {}

local function register(part: Instance)
	if not part:IsA("BasePart") then
		return
	end
	local stage = part:FindFirstChild("Stage")
	if stage and stage:IsA("IntValue") then
		if checkpoints[stage.Value] then
			warn(`[Checkpoints] Two checkpoints use stage {stage.Value}: {part:GetFullName()}`)
		end
		checkpoints[stage.Value] = part
	end
end

for _, descendant in obby:GetDescendants() do
	if descendant.Name == "Checkpoint" then
		register(descendant)
	end
end
register(finish:WaitForChild("FinishPad"))

local stageOf: { [Player]: number } = {}

local function characterPlayer(hit: BasePart): Player?
	local model = hit:FindFirstAncestorOfClass("Model")
	if not model then
		return nil
	end
	local humanoid = model:FindFirstChildOfClass("Humanoid")
	if not humanoid or humanoid.Health <= 0 then
		return nil
	end
	return Players:GetPlayerFromCharacter(model)
end

local function setStage(player: Player, stage: number)
	stageOf[player] = stage
	local leaderstats = player:FindFirstChild("leaderstats")
	local value = leaderstats and leaderstats:FindFirstChild("Stage")
	if value and value:IsA("IntValue") then
		value.Value = stage
	end
end

for stage, part in checkpoints do
	part.Touched:Connect(function(hit: BasePart)
		local player = characterPlayer(hit)
		if player and stage > (stageOf[player] or 0) then
			setStage(player, stage)
		end
	end)
end

local function moveCharacterTo(character: Model, target: CFrame)
	if not character:IsDescendantOf(Workspace) then
		character.AncestryChanged:Wait()
	end
	if not character:WaitForChild("HumanoidRootPart", 10) then
		return
	end
	task.wait() -- let Roblox finish its own spawn placement first
	character:PivotTo(target)
end

local function onCharacterAdded(player: Player, character: Model)
	local checkpoint = checkpoints[stageOf[player] or 0]
	if checkpoint then
		moveCharacterTo(character, checkpoint.CFrame * CFrame.new(0, 4, 0))
	end
end

local function onPlayerAdded(player: Player)
	if stageOf[player] ~= nil then
		return -- already set up
	end
	stageOf[player] = 0
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"
	local stage = Instance.new("IntValue")
	stage.Name = "Stage"
	stage.Value = 0
	stage.Parent = leaderstats
	leaderstats.Parent = player

	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
	if player.Character then
		task.spawn(onCharacterAdded, player, player.Character)
	end
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end
Players.PlayerRemoving:Connect(function(player)
	stageOf[player] = nil
end)

-- Back-to-cinema pad on the finish platform.
local backPad = finish:FindFirstChild("BackToCinema")
local spawnPad = cinema:FindFirstChild("SpawnLocation")
if backPad and backPad:IsA("BasePart") and spawnPad and spawnPad:IsA("BasePart") then
	local cooldown: { [Player]: number } = {}
	backPad.Touched:Connect(function(hit: BasePart)
		local player = characterPlayer(hit)
		if not player or not player.Character then
			return
		end
		if os.clock() - (cooldown[player] or 0) < 2 then
			return
		end
		cooldown[player] = os.clock()
		player.Character:PivotTo(spawnPad.CFrame * CFrame.new(0, 4, 0))
	end)
	Players.PlayerRemoving:Connect(function(player)
		cooldown[player] = nil
	end)
end
