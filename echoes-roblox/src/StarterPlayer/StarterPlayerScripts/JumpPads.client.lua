-- StarterPlayer > StarterPlayerScripts > JumpPads  (LocalScript)
-- Launches the local player upward when they step on a part named "JumpPad".
-- (Done on the client because each player's own character physics runs on
-- their device - this makes the launch instant and smooth.)
-- A JumpPad can have a NumberValue child "Power" to override Config.JumpPadPower.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage:WaitForChild("Config"))

local player = Players.LocalPlayer
local lastLaunch = 0

local function launch(pad: BasePart, hit: BasePart)
	local character = player.Character
	if not character or not hit:IsDescendantOf(character) then
		return
	end
	local root = character:FindFirstChild("HumanoidRootPart")
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not (root and root:IsA("BasePart") and humanoid) or humanoid.Health <= 0 then
		return
	end
	if os.clock() - lastLaunch < 0.6 then
		return
	end
	lastLaunch = os.clock()

	local powerValue = pad:FindFirstChild("Power")
	local power = if powerValue and powerValue:IsA("NumberValue") then powerValue.Value else Config.JumpPadPower
	humanoid:ChangeState(Enum.HumanoidStateType.Jumping)
	local velocity = root.AssemblyLinearVelocity
	root.AssemblyLinearVelocity = Vector3.new(velocity.X, power, velocity.Z)

	-- Little flash so the pad feels alive.
	local original = pad.Color
	pad.Color = Color3.new(1, 1, 1)
	task.delay(0.15, function()
		pad.Color = original
	end)
end

local obby = Workspace:WaitForChild("Obby")
for _, descendant in obby:GetDescendants() do
	if descendant:IsA("BasePart") and descendant.Name == "JumpPad" then
		local pad = descendant
		pad.Touched:Connect(function(hit: BasePart)
			launch(pad, hit)
		end)
	end
end
