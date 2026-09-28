--!strict
-- StarterPlayerScripts > ClientModules > Theme  (ModuleScript)
-- Colours and fonts for all UI, matching the loading screen (deep navy, cyan glow,
-- white classical serif).

local Theme = {}

Theme.Navy = Color3.fromRGB(10, 12, 30)
Theme.NavySoft = Color3.fromRGB(22, 24, 52)
Theme.Ink = Color3.fromRGB(6, 7, 18)
Theme.Cyan = Color3.fromRGB(120, 225, 240)
Theme.Violet = Color3.fromRGB(170, 140, 255)
Theme.Gold = Color3.fromRGB(255, 214, 140)
Theme.White = Color3.fromRGB(245, 245, 245)
Theme.Soft = Color3.fromRGB(200, 208, 232)
Theme.Dim = Color3.fromRGB(120, 128, 156)
Theme.Paper = Color3.fromRGB(244, 236, 216)
Theme.PaperInk = Color3.fromRGB(52, 40, 34)

-- Balthazar (Enum.Font.Fantasy): a classical serif for titles, insights and captions' speaker.
Theme.TitleFamily = Font.fromEnum(Enum.Font.Fantasy).Family
Theme.UIFamily = Font.fromEnum(Enum.Font.BuilderSans).Family

function Theme.title(weight: Enum.FontWeight?, italic: boolean?): Font
	return Font.new(Theme.TitleFamily, weight or Enum.FontWeight.Regular,
		if italic then Enum.FontStyle.Italic else Enum.FontStyle.Normal)
end

function Theme.ui(weight: Enum.FontWeight?): Font
	return Font.new(Theme.UIFamily, weight or Enum.FontWeight.Medium, Enum.FontStyle.Normal)
end

return Theme
