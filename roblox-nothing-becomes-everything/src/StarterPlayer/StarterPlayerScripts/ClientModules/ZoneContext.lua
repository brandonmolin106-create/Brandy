--!strict
-- StarterPlayerScripts > ClientModules > ZoneContext  (ModuleScript)
-- The shape every zone module (ClientModules/Zones/*) receives and implements.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Types = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Types"))

export type Context = {
	zone: string,
	kit: Instance?, -- this player's own copy of ReplicatedStorage.ZoneKits[zone]
	state: Types.ZoneState, -- puzzle state from the server
	action: (name: string, arg: number?) -> (), -- ask the server to do something
	travel: (zone: string) -> (),
	root: () -> BasePart?, -- the local character's HumanoidRootPart
}

export type Module = {
	start: (ctx: Context) -> (),
	stop: () -> (),
	onEvent: (name: string, data: { [string]: any }) -> (),
}

-- Collects connections and threads so a zone can clean up after itself.
export type Bin = {
	add: (self: Bin, item: RBXScriptConnection | thread | Instance | () -> ()) -> (),
	clean: (self: Bin) -> (),
}

local ZoneContext = {}

function ZoneContext.bin(): Bin
	local items: { RBXScriptConnection | thread | Instance | () -> () } = {}
	local bin: Bin = {
		add = function(_self: Bin, item: RBXScriptConnection | thread | Instance | () -> ())
			table.insert(items, item)
		end,
		clean = function(_self: Bin)
			for _, item in items do
				if typeof(item) == "RBXScriptConnection" then
					item:Disconnect()
				elseif typeof(item) == "thread" then
					pcall(task.cancel, item)
				elseif typeof(item) == "Instance" then
					item:Destroy()
				elseif type(item) == "function" then
					item()
				end
			end
			table.clear(items)
		end,
	}
	return bin
end

return ZoneContext
