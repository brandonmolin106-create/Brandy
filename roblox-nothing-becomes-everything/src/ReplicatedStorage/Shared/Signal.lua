--!strict
-- ReplicatedStorage > Shared > Signal  (ModuleScript)
-- A tiny typed event: signal:Connect(fn) -> disconnect function, signal:Fire(...).

export type Signal<T...> = {
	Connect: (self: Signal<T...>, fn: (T...) -> ()) -> () -> (),
	Fire: (self: Signal<T...>, T...) -> (),
}

local Signal = {}

function Signal.new<T...>(): Signal<T...>
	local handlers: { (T...) -> () } = {}
	local signal: Signal<T...> = {
		Connect = function(_self: Signal<T...>, fn: (T...) -> ()): () -> ()
			table.insert(handlers, fn)
			return function()
				local i = table.find(handlers, fn)
				if i then
					table.remove(handlers, i)
				end
			end
		end,
		Fire = function(_self: Signal<T...>, ...: T...)
			for _, fn in table.clone(handlers) do
				task.spawn(fn, ...)
			end
		end,
	}
	return signal
end

return Signal
