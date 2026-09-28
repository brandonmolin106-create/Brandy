--!strict
-- StarterPlayerScripts > ClientModules > Voice  (ModuleScript)
-- Brandon narrates: plays a line with its caption, lowers the music, queues story
-- lines so they never talk over each other, and remembers what has been heard.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Content = require(ReplicatedStorage:WaitForChild("Content"))
local Signal = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Signal"))
local Audio = require(script.Parent:WaitForChild("Audio"))
local Captions = require(script.Parent:WaitForChild("Captions"))

local Voice = {}
Voice.Started = Signal.new() :: Signal.Signal<string>
Voice.Finished = Signal.new() :: Signal.Signal<string>

local queue: { string } = {}
local speaking: string? = nil
local token = 0
local lastPlayed: { [string]: number } = {}
local heard: { [string]: boolean } = {}

local function finish(lineId: string)
	if speaking == lineId then
		speaking = nil
		Audio.setDuck(false)
		Voice.Finished:Fire(lineId)
	end
end

local function start(lineId: string)
	local line = Content.Lines[lineId]
	if not line then
		warn("[Voice] unknown line " .. lineId)
		return
	end
	token += 1
	local my = token
	local previous = speaking
	if previous then
		finish(previous)
	end
	speaking = lineId
	lastPlayed[lineId] = os.clock()
	heard[lineId] = true
	local duration = Audio.playLine(lineId)
	Captions.show(line.text, duration)
	Audio.setDuck(true)
	Voice.Started:Fire(lineId)
	task.delay(duration + 0.35, function()
		if my ~= token then
			return
		end
		finish(lineId)
		local nextLine = table.remove(queue, 1)
		if nextLine then
			start(nextLine)
		end
	end)
end

-- Plays a line now if nothing is playing (or if interrupt), otherwise queues it.
function Voice.say(lineId: string, interrupt: boolean?)
	if interrupt or speaking == nil then
		if interrupt then
			table.clear(queue)
		end
		start(lineId)
	elseif speaking ~= lineId and not table.find(queue, lineId) and #queue < 3 then
		table.insert(queue, lineId)
	end
end

-- Story beats: each line auto-plays only once per session.
function Voice.sayOnce(lineId: string)
	if heard[lineId] or table.find(queue, lineId) or speaking == lineId then
		return
	end
	heard[lineId] = true
	Voice.say(lineId)
end

function Voice.heard(lineId: string): boolean
	return heard[lineId] == true
end

function Voice.playedWithin(lineId: string, seconds: number): boolean
	local t = lastPlayed[lineId]
	return t ~= nil and os.clock() - t < seconds
end

function Voice.current(): string?
	return speaking
end

function Voice.stop()
	token += 1
	table.clear(queue)
	Audio.stopLine()
	Captions.hide()
	local previous = speaking
	if previous then
		finish(previous)
	end
end

return Voice
