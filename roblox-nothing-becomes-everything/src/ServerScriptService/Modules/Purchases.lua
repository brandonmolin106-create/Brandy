--!strict
-- ServerScriptService > Modules > Purchases  (ModuleScript)
-- Optional monetisation. Everything here is hidden while its id in Config is 0.
--
--  * "Echo Aura" game pass: a soft particle trail. Ownership is checked on join and
--    granted straight after a purchase (PromptGamePassPurchaseFinished).
--  * "Tip Brandon" developer product: a thank-you message and sparkles at the campfire.
--    Receipts go through MarketplaceService.ProcessReceipt, idempotently:
--      - the PurchaseId is recorded in the player's saved profile; a receipt that is
--        already recorded is never granted twice,
--      - PurchaseGranted is only returned once that record is safely saved
--        (UpdateAsync merge in ProgressStore); otherwise NotProcessedYet, and Roblox
--        delivers the receipt again later,
--      - two servers handling the same receipt at once still count it once, because
--        the saved receipts are merged by PurchaseId.

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage:WaitForChild("Config"))
local ProgressStore = require(script.Parent:WaitForChild("ProgressStore"))

type Hooks = {
	notify: (player: Player, text: string) -> (),
	event: (player: Player, name: string, data: { [string]: any }) -> (),
	pushState: (player: Player) -> (),
}

local Purchases = {}

local hooks: Hooks? = nil
local handlers: { [number]: (player: Player, receipt: { [string]: any }) -> () } = {}

local function passId(): number
	return if type(Config.GamePassId) == "number" then Config.GamePassId else 0
end

local function tipId(): number
	local id = Config.DevProductIds.TipBrandon
	return if type(id) == "number" then id else 0
end

-- ---------------------------------------------------------------------------- Echo Aura
local AURA_NAMES = { "EchoAuraTop", "EchoAuraBottom", "EchoAuraTrail", "EchoAuraSparkles" }

local function auraWanted(player: Player): boolean
	if player:GetAttribute("AuraOwned") ~= true then
		return false
	end
	local session = ProgressStore.get(player)
	return session == nil or session.profile.settings.aura
end

function Purchases.applyAura(player: Player)
	local character = player.Character
	local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
	if not root or not root:IsA("BasePart") then
		return
	end
	local has = root:FindFirstChild("EchoAuraTrail") ~= nil
	local want = auraWanted(player)
	if has and not want then
		for _, name in AURA_NAMES do
			local d = root:FindFirstChild(name)
			if d then
				d:Destroy()
			end
		end
	elseif want and not has then
		local top = Instance.new("Attachment")
		top.Name = "EchoAuraTop"
		top.Position = Vector3.new(0, 1.2, 0.3)
		top.Parent = root
		local bottom = Instance.new("Attachment")
		bottom.Name = "EchoAuraBottom"
		bottom.Position = Vector3.new(0, -1.6, 0.3)
		bottom.Parent = root
		local trail = Instance.new("Trail")
		trail.Name = "EchoAuraTrail"
		trail.Attachment0 = top
		trail.Attachment1 = bottom
		trail.Lifetime = 0.7
		trail.LightEmission = 0.8
		trail.FaceCamera = true
		trail.Color = ColorSequence.new(Color3.fromRGB(120, 225, 240), Color3.fromRGB(190, 150, 255))
		trail.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.55),
			NumberSequenceKeypoint.new(1, 1),
		})
		trail.Parent = root
		local sparkles = Instance.new("ParticleEmitter")
		sparkles.Name = "EchoAuraSparkles"
		sparkles.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		sparkles.Color = ColorSequence.new(Color3.fromRGB(150, 230, 255), Color3.fromRGB(210, 170, 255))
		sparkles.LightEmission = 1
		sparkles.Rate = 5
		sparkles.Lifetime = NumberRange.new(1, 2)
		sparkles.Speed = NumberRange.new(0.3, 1)
		sparkles.SpreadAngle = Vector2.new(180, 180)
		sparkles.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.25),
			NumberSequenceKeypoint.new(1, 0),
		})
		sparkles.Parent = root
	end
end

local function grantAura(player: Player)
	if player:GetAttribute("AuraOwned") == true then
		return
	end
	player:SetAttribute("AuraOwned", true)
	Purchases.applyAura(player)
	local h = hooks
	if h then
		h.pushState(player)
	end
end

function Purchases.checkOwnership(player: Player)
	local id = passId()
	if id <= 0 then
		return
	end
	task.spawn(function()
		for attempt = 1, 3 do
			local ok, owns = pcall(function()
				return MarketplaceService:UserOwnsGamePassAsync(player.UserId, id)
			end)
			if ok then
				if owns then
					grantAura(player)
				end
				return
			end
			task.wait(attempt * 2)
		end
	end)
end

function Purchases.promptAura(player: Player)
	local id = passId()
	if id <= 0 then
		return
	end
	if player:GetAttribute("AuraOwned") == true then
		local h = hooks
		if h then
			h.notify(player, "You have the Echo Aura. Turn it on or off in Settings.")
		end
		return
	end
	MarketplaceService:PromptGamePassPurchase(player, id)
end

-- ---------------------------------------------------------------------------- Tip Brandon
function Purchases.promptTip(player: Player)
	local id = tipId()
	if id > 0 then
		MarketplaceService:PromptProductPurchase(player, id)
	end
end

local function processReceipt(receipt: { [string]: any }): Enum.ProductPurchaseDecision
	local userId = receipt.PlayerId
	local productId = receipt.ProductId
	local purchaseId = tostring(receipt.PurchaseId)
	local player = if type(userId) == "number" then Players:GetPlayerByUserId(userId) else nil
	if not player then
		return Enum.ProductPurchaseDecision.NotProcessedYet -- delivered again when they rejoin
	end
	local handler = if type(productId) == "number" then handlers[productId] else nil
	if not handler then
		warn(`[Purchases] no handler for product {productId}`)
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	local session = ProgressStore.waitFor(player, 15)
	if not session then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	if ProgressStore.recordReceipt(player, purchaseId) == "new" then
		local ok, err = pcall(function()
			handler(player, receipt)
		end)
		if not ok then
			warn("[Purchases] thank-you effect failed:", err)
		end
	end
	if not session.persistent then
		-- Data stores are unavailable (Studio without API access): test purchases in
		-- Studio are free, so grant them; a live server waits for data stores instead.
		return if RunService:IsStudio()
			then Enum.ProductPurchaseDecision.PurchaseGranted
			else Enum.ProductPurchaseDecision.NotProcessedYet
	end
	if ProgressStore.receiptIsSaved(player, purchaseId) then
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	if ProgressStore.saveAsync(player, "receipt") and ProgressStore.receiptIsSaved(player, purchaseId) then
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	return Enum.ProductPurchaseDecision.NotProcessedYet
end

function Purchases.start(h: Hooks)
	hooks = h
	local hub = Workspace:WaitForChild("Zones"):WaitForChild("hub")
	if passId() <= 0 then
		local shrine = hub:FindFirstChild("AuraShrine")
		if shrine then
			shrine:Destroy()
		end
	end
	local tip = tipId()
	if tip <= 0 then
		local jar = hub:FindFirstChild("TipJar")
		if jar then
			jar:Destroy()
		end
	else
		handlers[tip] = function(player: Player, _receipt: { [string]: any })
			h.notify(player, "Thank you for supporting Brandon!")
			h.event(player, "tip_thanks", {})
			h.pushState(player)
		end
	end
	MarketplaceService.ProcessReceipt = processReceipt
	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player: Player, gamePassId: number, purchased: boolean)
		if purchased and gamePassId == passId() then
			grantAura(player)
			h.notify(player, "Echo Aura unlocked. Thank you!")
		end
	end)
end

return Purchases
