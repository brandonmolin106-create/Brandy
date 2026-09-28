--!strict
-- StarterPlayerScripts > ClientModules > LightingFX  (ModuleScript)
-- Per-zone lighting and atmosphere (Lighting, Atmosphere, ColorCorrection, Bloom,
-- SunRays, Sky), tweened on the client when the player changes zone. Changes made on
-- the client stay on this client.

local Lighting = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")

local LightingFX = {}

type Preset = {
	clock: number,
	brightness: number,
	ambient: Color3,
	outdoor: Color3,
	exposure: number,
	density: number,
	offset: number,
	atmoColor: Color3,
	decay: Color3,
	glare: number,
	haze: number,
	tint: Color3,
	saturation: number,
	contrast: number,
	gradeBrightness: number,
	bloom: number,
	bloomSize: number,
	bloomThreshold: number,
	rays: number,
	stars: number,
}

local rgb = Color3.fromRGB

local PRESETS: { [string]: Preset } = {
	hub = { -- calm night meadow
		clock = 0.2, brightness = 1.6, ambient = rgb(40, 44, 72), outdoor = rgb(70, 80, 124), exposure = 0.35,
		density = 0.32, offset = 0.1, atmoColor = rgb(110, 120, 170), decay = rgb(40, 50, 100), glare = 0, haze = 1.4,
		tint = rgb(226, 230, 255), saturation = 0.08, contrast = 0.12, gradeBrightness = 0.02,
		bloom = 0.8, bloomSize = 30, bloomThreshold = 0.88, rays = 0.02, stars = 3000,
	},
	time = { -- golden, dusty, sand in the air
		clock = 16.6, brightness = 2.6, ambient = rgb(120, 96, 70), outdoor = rgb(150, 120, 90), exposure = 0.1,
		density = 0.38, offset = 0.2, atmoColor = rgb(214, 176, 120), decay = rgb(170, 110, 70), glare = 0.4, haze = 2.2,
		tint = rgb(255, 238, 210), saturation = 0.12, contrast = 0.1, gradeBrightness = 0.01,
		bloom = 0.6, bloomSize = 28, bloomThreshold = 0.92, rays = 0.12, stars = 0,
	},
	hole = { -- dark pit under a starry sliver of sky
		clock = 23.5, brightness = 0.7, ambient = rgb(22, 20, 34), outdoor = rgb(34, 34, 56), exposure = 0.25,
		density = 0.42, offset = 0, atmoColor = rgb(60, 60, 110), decay = rgb(20, 16, 40), glare = 0, haze = 1.6,
		tint = rgb(200, 206, 255), saturation = -0.15, contrast = 0.22, gradeBrightness = -0.02,
		bloom = 1.0, bloomSize = 32, bloomThreshold = 0.8, rays = 0, stars = 4000,
	},
	glass = { -- bright, cool morning by the lake
		clock = 8.6, brightness = 2.8, ambient = rgb(100, 130, 150), outdoor = rgb(140, 170, 190), exposure = 0.05,
		density = 0.28, offset = 0.1, atmoColor = rgb(170, 210, 230), decay = rgb(110, 150, 180), glare = 0.3, haze = 1.2,
		tint = rgb(226, 244, 255), saturation = 0.05, contrast = 0.06, gradeBrightness = 0.02,
		bloom = 0.9, bloomSize = 30, bloomThreshold = 0.86, rays = 0.1, stars = 0,
	},
	road = { -- long dusk
		clock = 17.9, brightness = 2.2, ambient = rgb(110, 80, 80), outdoor = rgb(150, 110, 110), exposure = 0.15,
		density = 0.4, offset = 0.25, atmoColor = rgb(255, 160, 120), decay = rgb(120, 60, 100), glare = 0.8, haze = 2.4,
		tint = rgb(255, 226, 212), saturation = 0.18, contrast = 0.12, gradeBrightness = 0.0,
		bloom = 0.8, bloomSize = 34, bloomThreshold = 0.88, rays = 0.16, stars = 500,
	},
	chains = { -- stormy and heavy
		clock = 15.2, brightness = 1.2, ambient = rgb(70, 70, 90), outdoor = rgb(90, 90, 110), exposure = -0.05,
		density = 0.48, offset = 0.05, atmoColor = rgb(130, 130, 160), decay = rgb(70, 66, 96), glare = 0, haze = 2.6,
		tint = rgb(220, 222, 240), saturation = -0.2, contrast = 0.2, gradeBrightness = -0.03,
		bloom = 0.5, bloomSize = 24, bloomThreshold = 0.95, rays = 0, stars = 0,
	},
	everything = { -- sunrise above the clouds
		clock = 6.15, brightness = 2.6, ambient = rgb(140, 110, 100), outdoor = rgb(180, 140, 130), exposure = 0.2,
		density = 0.34, offset = 0.3, atmoColor = rgb(255, 196, 160), decay = rgb(255, 130, 110), glare = 1.2, haze = 1.8,
		tint = rgb(255, 240, 226), saturation = 0.2, contrast = 0.1, gradeBrightness = 0.03,
		bloom = 1.0, bloomSize = 36, bloomThreshold = 0.82, rays = 0.25, stars = 0,
	},
}

local atmosphere: Atmosphere
local grade: ColorCorrectionEffect
local bloom: BloomEffect
local rays: SunRaysEffect
local sky: Sky?
local tweens: { Tween } = {}

local function find<T>(className: string, name: string, make: () -> T): T
	local existing = Lighting:FindFirstChild(name)
	if existing and existing:IsA(className) then
		return (existing :: any) :: T
	end
	return make()
end

function LightingFX.init()
	atmosphere = find("Atmosphere", "Atmosphere", function(): Atmosphere
		local a = Instance.new("Atmosphere")
		a.Parent = Lighting
		return a
	end)
	grade = find("ColorCorrectionEffect", "Grade", function(): ColorCorrectionEffect
		local g = Instance.new("ColorCorrectionEffect")
		g.Name = "Grade"
		g.Parent = Lighting
		return g
	end)
	bloom = find("BloomEffect", "Bloom", function(): BloomEffect
		local b = Instance.new("BloomEffect")
		b.Name = "Bloom"
		b.Parent = Lighting
		return b
	end)
	rays = find("SunRaysEffect", "SunRays", function(): SunRaysEffect
		local r = Instance.new("SunRaysEffect")
		r.Name = "SunRays"
		r.Parent = Lighting
		return r
	end)
	local s = Lighting:FindFirstChildOfClass("Sky")
	sky = s
end

local function play(object: Instance, info: TweenInfo, props: { [string]: any })
	local t = TweenService:Create(object, info, props)
	table.insert(tweens, t)
	t:Play()
end

local function applyPreset(p: Preset, seconds: number, setClock: boolean)
	for _, t in tweens do
		t:Cancel()
	end
	table.clear(tweens)
	local info = TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
	local lightingProps: { [string]: any } = {
		Brightness = p.brightness,
		Ambient = p.ambient,
		OutdoorAmbient = p.outdoor,
		ExposureCompensation = p.exposure,
	}
	if setClock then
		Lighting.ClockTime = p.clock
	else
		lightingProps.ClockTime = p.clock
	end
	play(Lighting, info, lightingProps)
	play(atmosphere, info, {
		Density = p.density,
		Offset = p.offset,
		Color = p.atmoColor,
		Decay = p.decay,
		Glare = p.glare,
		Haze = p.haze,
	})
	play(grade, info, {
		TintColor = p.tint,
		Saturation = p.saturation,
		Contrast = p.contrast,
		Brightness = p.gradeBrightness,
	})
	play(bloom, info, { Intensity = p.bloom, Size = p.bloomSize, Threshold = p.bloomThreshold })
	play(rays, info, { Intensity = p.rays })
	local s = sky
	if s then
		s.StarCount = p.stars
	end
end

-- Zone change: the clock jumps (the screen is faded), everything else tweens.
function LightingFX.apply(zone: string, seconds: number?)
	local p = PRESETS[zone] or PRESETS.hub
	applyPreset(p, seconds or 1.4, true)
end

-- Story moments inside a zone: a copy of the zone preset with some values changed.
function LightingFX.shift(zone: string, changes: { [string]: any }, seconds: number)
	local base = PRESETS[zone] or PRESETS.hub
	local p = table.clone(base) :: any
	for k, v in changes do
		p[k] = v
	end
	applyPreset(p :: Preset, seconds, false)
end

return LightingFX
