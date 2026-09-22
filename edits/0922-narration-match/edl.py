"""Edit decision list for "0922 narration-match" (Endless Destiny announcement).

Everything creative lives here: which narration phrases make up each line,
the voice effect on each line, how long the pause after it is, the music
plan, the sound-design cues, and which clip plays under which line.

Chunk ids refer to data/chunks.json (the narration split on silences).
Line indexes (L0, L1, ...) are positions in LINES.
"""

# Higgsfield generation ids for the source media (URLs are resolved locally,
# never committed -- see fetch_assets.py).
NARRATION_PARTS = {
    1: "bce0eea3-944a-4139-a59c-8bb57febcac9",
    2: "9a814d5e-3fee-413e-9718-d2629e78ddc8",
    3: "4350d5e0-26b3-4f78-a632-17799fdf5653",
    4: "1a833912-756c-4ad9-984b-4f0a602a9929",
    5: "b09ab272-e79a-4660-a6d8-76b16bacaf0a",
    6: "57961986-e164-486c-9fee-5fd0705e718b",
    7: "8fb7dee5-3d9c-4230-994b-439310057317",
}

CLIPS = {
    "C01": "0098aa66-5607-4c4f-8136-5bd22f844708",  # line-light traveler, galaxy, logo title card
    "C02": "8f309ab2-c5a2-48a5-b7cc-92015484cf5c",  # constellations walk, gold bloom, logo on water
    "C03": "8adb49d9-65db-4182-9fc4-b56b8c07a360",  # milky way, portal, ENDLESS DESTINY title
    "C04": "65ec8eee-7d81-417f-91b3-36ea2ea9816a",  # stairway, particle heads, hand, smile/tear/fall
    "C05": "27f099ff-bfd0-49b8-a318-efede9b2adcc",  # pier to the horizon light
    "C06": "64b10c30-adbe-4f30-a22a-7a1c93627e0c",  # river horizon, logo ripple, lone figure
    "C07": "35de02a6-f518-49b2-be46-15f904a5da5e",  # hooded figure, gold cracks underground
    "C08": "e9b1e446-cc5a-4c4b-b673-fd60619813dc",  # river shore, logo reflection rising
    "C09": "0357d876-9136-45cd-94cc-69ab7f386b85",  # glowing platform, winding path, gold planet
    "C10": "f2f9964b-e4b1-4bcc-8cfe-91f23a61242b",  # feet on wet road, fog, sea of clouds
    "C11": "e3cd855e-d234-46f7-9500-93cefd96200e",  # gold point -> logo -> nebula
    "C12": "b1e66d90-4996-4750-a438-86bb33b8ec91",  # valley becomes the logo, dawn lake
    "C13": "3f97b8b0-fa92-4c8b-ba2a-d0be6de0e504",  # boots in snow, gold paths, gold network planet
    "C14": "8dc36547-f2c8-48fa-8139-c9926ce738ed",  # traveler in a maze of light roads
    "C15": "e8ebf0ed-ff78-4e2c-91de-f28d11895ee8",  # lantern walkers, logo in sky
    "C16": "0c60a902-2ce8-458a-a664-cb7ddb151c8f",  # man in fog, star above his head
    "C17": "d91640d9-44a2-4f10-9378-04fce7967b63",  # opening: black -> gold point -> lake
    "C18": "fe055506-f2a8-4b38-a12b-ba8636abea5a",  # total dark, one gold point
    "C19": "aef55adb-9c82-42c3-bc77-c5fa7f48b4b8",  # traveler sitting by the misty river
    "C20": "0a35c914-5a55-44ff-a6fe-9f18a18e58b5",  # gold reflection drifting downstream
    "C21": "3d949e01-9062-4422-bd53-6148f59eba20",  # road beside the river
    "C22": "7bd47e61-cb0b-4527-9306-f481dd84b3ed",  # low tracking behind the traveler
    "C23": "6a145dda-ddf6-44e7-9e2b-ffadac13bb51",  # crane reveal of the winding road
    "C24": "04680582-4693-49e2-a201-ac4407db2050",  # river time-lapse into the gorge
    "C25": "3c488207-3f2a-48bc-a645-a2bc1b21dc62",  # dark gorge, stillness
    "C26": "1edf2e83-ff41-4c3a-9885-5e98605f577e",  # bridge, then another road
}

# Silence before the first word (black + drone, the gold point fades up).
PREROLL = 3.0
# Silence/tail after the last word before the hard cut to black.
TAIL = 3.2

# Breaths / mouth noise between lines that the silence split caught.
# Checked against peak level and the transcript; none contain words.
DROP = {37, 38, 39, 43, 80, 83, 91, 95, 97, 99, 103, 104, 108, 112, 119, 121, 124, 137}

# Chunks that hold two lines; split at a point inside the pause between them
# (seconds in that narration part).
SPLITS = {66: 87.39, 134: 4.00, 140: 24.92}

# (chunks, caption text, voice fx preset, pause after the line in seconds).
# Pause None = default compression rule in build_audio.gap_rule().
LINES = [
    ([0], "Hey everyone, and welcome to Echoes in the Dark.", "echo", 1.3),
    ([1], "And today we finally get to announce the next song we've been working on.", "warm", 1.6),
    ([2], "Endless Destiny.", "title", 3.2),
    ([3], "And even the name itself is kind of a question, because… what actually is destiny?", "hall", 1.3),
    ([4], "Is destiny something waiting for us at the end of the road?", "hall", 1.2),
    ([5], "Or is destiny the road itself?", "hall", 1.5),
    ([6], "And if destiny has an ending…", "hall", 0.9),
    ([7, 8], "then why does the journey sometimes feel endless?", "echo", 2.2),
    ([9], "That's really where this song came from.", "warm", 1.0),
    ([10], "That feeling of moving forward without completely knowing where you're going.", "hall", 1.3),
    ([11], "You change.", "warm", 0.85),
    ([12], "You lose things.", "warm", 0.85),
    ([13], "You find things.", "warm", 0.85),
    ([14], "You meet people.", "warm", 0.85),
    ([15], "You leave people behind.", "warm", 0.85),
    ([16], "You make mistakes.", "warm", 0.85),
    ([17], "You try again.", "warm", 1.1),
    ([18, 19], "And somehow, through all of it, the journey keeps moving.", "hall", 1.4),
    ([20], "But where?", "echo", 2.6),
    ([21], "Have you ever stopped and wondered that?", "intimate", 1.8),
    # part 2
    ([22], "Where is all of this actually taking me?", "intimate", 1.3),
    ([23], "Are the choices I'm making today quietly building the person I'm going to become tomorrow?", "hall", 1.3),
    ([24, 25], "And what if the moments that feel pointless right now… aren't pointless at all?", "hall", 1.3),
    ([26], "What if the delay is part of the journey?", "hall", 1.2),
    ([27], "What if getting lost is part of finding the road?", "hall", 1.3),
    ([28, 29, 30, 31, 32], "What if the moment you think nothing is happening is actually the moment everything underneath you is changing?", "big", 2.0),
    ([33], "Because we always talk about destiny like it's somewhere far away.", "hall", 1.2),
    ([34], "Like one day we'll finally arrive.", "hall", 1.0),
    ([35], "One day everything will make sense.", "hall", 1.0),
    ([36], "One day we'll reach that place and say:", "hall", 0.9),
    ([40], "“This is it. This is what everything was leading toward.”", "memory", 1.6),
    ([41], "But what if that day never really comes?", "hall", 1.2),
    ([42], "Not because there is no destiny…", "hall", 1.0),
    ([44], "but because destiny keeps moving with us.", "big", 2.6),
    # part 3
    ([45, 46], "You reach one dream… and another appears.", "echo", 1.1),
    ([47, 48], "You cross one bridge… and suddenly there's another road.", "echo", 1.1),
    ([49, 50], "You answer one question… and somehow ten more questions appear.", "echo", 1.4),
    ([51], "So maybe destiny isn't a finish line.", "hall", 1.0),
    ([52], "Maybe it's a direction.", "hall", 1.0),
    ([53], "Maybe it's the thing pulling you forward even when you can't explain why.", "hall", 1.3),
    ([54], "And that's what I wanted Endless Destiny to feel like.", "big", 1.3),
    ([55], "A journey.", "hall", 0.9),
    ([56], "Not a perfect journey.", "hall", 0.9),
    ([57], "Not a straight road.", "hall", 1.3),
    ([58], "A journey with darkness.", "hall", 0.9),
    ([59], "With questions.", "hall", 0.9),
    ([60], "With distance.", "hall", 0.9),
    ([61], "With hope.", "big", 1.1),
    ([62, 63], "With moments where you feel like you know exactly where you're going… and moments where you have absolutely no idea.", "hall", 1.3),
    ([64], "Because that's life, isn't it?", "intimate", 1.4),
    ([65], "We want maps.", "hall", 0.8),
    (["66a"], "We want answers. We want guarantees. We want somebody to tell us:", "hall", 0.8),
    (["66b"], "“Go this way. Do this. Wait this long. Then everything will work out.”", "memory", 2.0),
    # part 4
    ([67], "But life doesn't really work like that.", "intimate", 1.2),
    ([68], "Sometimes all you get is one step.", "hall", 1.0),
    ([69], "And then another.", "echo", 1.0),
    ([70], "And another.", "echo", 2.0),
    ([71], "And you don't understand the path until you turn around years later and finally see what those steps became.", "hall", 1.3),
    ([72], "So here's another question.", "intimate", 0.9),
    ([73], "If you already knew exactly how your whole life would happen…", "hall", 0.9),
    ([74], "would the journey still mean anything?", "hall", 1.5),
    ([75], "If you knew every success before it happened…", "hall", 0.8),
    ([76], "every failure…", "hall", 0.8),
    ([77], "every friendship…", "hall", 0.8),
    ([78], "every goodbye…", "echo", 0.8),
    ([79], "every place you'd end up…", "hall", 0.9),
    ([81], "would you still feel the same wonder walking toward it?", "hall", 1.5),
    ([82], "Maybe the unknown is what gives destiny its power.", "big", 1.4),
    ([84], "Because we don't know.", "intimate", 1.0),
    ([85], "We hope.", "warm", 0.9),
    ([86], "We imagine.", "warm", 0.9),
    ([87], "We choose. And then we keep walking.", "hall", 2.8),
    # part 5
    ([88, 89], "That word, endless, can sound scary.", "dark", 1.0),
    ([90], "Endless distance.", "dark", 0.8),
    ([92], "Endless waiting.", "dark", 0.8),
    ([93], "Endless questions.", "dark", 1.4),
    ([94], "It could also mean an endless conversation between who we are now…", "hall", 0.9),
    ([96], "who we used to be…", "memory", 0.9),
    ([98], "and who we're still becoming.", "big", 1.6),
    ([100], "And that's why this song means a lot to us.", "intimate", 1.0),
    ([101], "Because Endless Destiny isn't really about pretending we know where the journey ends.", "hall", 1.0),
    ([102], "It's about asking whether it even needs to.", "hall", 1.4),
    ([105], "Maybe every ending becomes another beginning.", "big", 1.0),
    ([106], "Maybe every destination becomes another journey.", "big", 1.0),
    ([107], "Maybe the thing we spend our whole lives chasing isn't sitting somewhere at the end of the road.", "hall", 3.0),
    ([109], "Maybe it's been travelling beside us the entire time.", "center", 3.6),
    # part 6
    ([110], "So when you eventually hear this song, I don't want you to only listen to it as our story.", "intimate", 1.0),
    ([111], "Think about yours.", "intimate", 1.4),
    ([113], "Where are you going?", "hall", 1.0),
    ([114], "What are you chasing?", "hall", 1.0),
    ([115], "What are you afraid of leaving behind?", "hall", 1.0),
    ([116], "What dream keeps pulling you forward?", "hall", 1.0),
    ([117], "What road are you walking right now that still doesn't make sense?", "hall", 1.3),
    ([118], "And if you feel lost…", "intimate", 0.9),
    ([120], "are you actually lost?", "intimate", 1.3),
    ([122], "Or are you simply standing in a part of the journey you haven't understood yet?", "hall", 1.3),
    ([123], "Because maybe we're all doing the same thing.", "chorus", 1.0),
    ([125], "Walking.", "chorus", 0.75),
    ([126], "Wondering.", "chorus", 0.75),
    ([127], "Falling.", "chorus", 0.75),
    ([128], "Growing.", "chorus", 1.0),
    ([129], "Looking toward something in the distance,", "hall", 0.9),
    ([130], "and asking ourselves one question over and over again:", "hall", 0.9),
    ([131], "Where does this journey end?", "big", 1.8),
    ([132], "And maybe the answer is…", "intimate", 1.7),
    ([133], "it doesn't.", "reveal", 3.0),
    # part 7
    (["134a"], "Maybe destiny was never meant to be a final place.", "hall", 1.0),
    (["134b", 135], "Maybe destiny is endless.", "reveal", 1.8),
    ([136], "Our next song is Endless Destiny,", "title", 1.0),
    ([138], "and this journey is only beginning.", "big", 3.2),
    ([139], "If you knew every smile,", "hall", 1.0),
    (["140a"], "every tear,", "hall", 1.0),
    (["140b"], "every fall,", "hall", 1.4),
    ([141], "Would knowing the future mean anything at all?", "final", None),
]

# Voice effect presets. Numbers are send levels into shared reverb buses
# (room / hall / cathedral / space) or extra layers:
#   throw  = echo on the last word only      swell = reverse-reverb rise into the line
#   prox   = close-mic warmth                 memory = filtered "voice in your head"
#   ghost  = pitched-down shadow voice        chorus = several voices ("we")
#   tail   = long space reverb on the last word
VOICE_FX = {
    "warm":     dict(room=0.16, hall=0.09),
    "hall":     dict(room=0.12, hall=0.19),
    "big":      dict(room=0.10, hall=0.22, cath=0.22),
    "intimate": dict(room=0.10, hall=0.05, prox=1),
    "echo":     dict(room=0.12, hall=0.17, throw=0.55),
    "title":    dict(room=0.10, hall=0.24, cath=0.34, swell=0.55, throw=0.45),
    "reveal":   dict(room=0.10, hall=0.18, cath=0.30, throw=0.50, tail=0.35),
    "memory":   dict(memory=1, hall=0.34, cath=0.16),
    "dark":     dict(room=0.10, cath=0.34, ghost=0.30),
    "chorus":   dict(room=0.12, hall=0.24, chorus=1),
    "center":   dict(room=0.08, hall=0.14, cath=0.20, swell=0.45, tail=0.45, prox=1),
    "final":    dict(room=0.06, hall=0.08, prox=1, throw=0.40, tail=0.55),
}

# Music: (line index, chord, intensity 0-1, plucked arpeggio on/off).
# The pad crossfades into each chord a little before the line starts.
MUSIC = [
    (0, "Am", 0.35, 0), (2, "Fmaj7", 0.60, 0), (3, "Am", 0.40, 0), (6, "Fmaj7", 0.40, 0),
    (8, "C", 0.45, 0), (10, "G", 0.50, 1), (13, "Am", 0.50, 1), (17, "F", 0.50, 0),
    (18, "Am_low", 0.25, 0), (20, "Am", 0.35, 0), (22, "F", 0.40, 0), (24, "C", 0.40, 0),
    (25, "Dm", 0.45, 0), (26, "Am", 0.40, 0), (27, "F", 0.45, 1), (29, "G", 0.50, 1),
    (30, "C", 0.50, 0), (31, "Am", 0.40, 0), (32, "F", 0.45, 0), (33, "G", 0.50, 0),
    (34, "Am", 0.50, 1), (35, "F", 0.50, 1), (36, "C", 0.55, 1), (37, "G", 0.50, 0),
    (40, "F", 0.60, 0), (41, "Am", 0.45, 0), (44, "Em", 0.40, 0), (47, "F", 0.50, 0),
    (48, "C", 0.50, 0), (49, "G", 0.40, 0), (50, "Am", 0.45, 1), (52, "C", 0.50, 0),
    (53, "Am_low", 0.30, 0), (54, "Am", 0.35, 0), (57, "F", 0.45, 0), (58, "C", 0.40, 0),
    (59, "G", 0.45, 1), (61, "Am", 0.50, 1), (63, "F", 0.50, 1), (65, "C", 0.50, 1),
    (66, "G", 0.55, 0), (67, "Am", 0.50, 0), (68, "F", 0.40, 0), (71, "C", 0.45, 0),
    (72, "dark", 0.45, 0), (76, "F", 0.40, 0), (78, "C", 0.50, 0), (79, "Am", 0.35, 0),
    (81, "F", 0.45, 0), (82, "C", 0.50, 0), (83, "G", 0.60, 0), (84, "Am", 0.65, 0),
    (85, "A", 0.60, 0), (86, "D", 0.35, 0), (88, "Am", 0.40, 1), (90, "F", 0.45, 1),
    (92, "C", 0.45, 0), (93, "Am_low", 0.30, 0), (95, "F", 0.40, 0), (96, "C", 0.50, 1),
    (97, "G", 0.55, 1), (99, "Am", 0.55, 1), (100, "F", 0.60, 1), (101, "C", 0.60, 0),
    (103, "G", 0.65, 0), (104, "Am_low", 0.15, 0), (105, "Am", 0.55, 0), (106, "F", 0.50, 0),
    (107, "G", 0.60, 0), (108, "A", 0.85, 0), (110, "A", 0.30, 0), (113, "A", 0.15, 0),
]

# Music drops out completely for the held breath before the emotional center
# (end of L84 -> start of L85), exactly like the trailer brief asks.
MUSIC_DROPOUTS = [(84, 85)]

# Sound design + matching picture accents. (kind, line, where, offset):
#   where = "start" | "end" of the line's voice; offset in seconds.
CUES = [
    ("riser", 2, "start", 0.0), ("impact", 2, "start", 0.0),
    ("softboom", 18, "start", 0.0),
    ("glitch", 24, "start", 1.2),
    ("rumble", 25, "start", 5.4), ("glitch", 25, "start", 6.2),
    ("softboom", 53, "start", 0.0),
    ("step", 54, "end", -0.35), ("step", 55, "end", -0.30), ("step", 56, "end", -0.30),
    ("whoosh", 34, "end", 0.4), ("whoosh", 35, "end", 0.4),
    ("softboom", 72, "start", 0.0),
    ("heartbeat", 85, "end", 0.3), ("glow", 85, "end", 0.6),
    ("riser", 105, "start", 0.0), ("impact", 105, "start", 0.0),
    ("riser", 108, "start", 0.0), ("impact", 108, "start", 0.0), ("glow", 109, "start", 0.0),
    ("chime", 110, "start", 0.35), ("chime", 111, "start", 0.25), ("chime", 112, "start", 0.25),
]

# Picture. (anchor, offset, clip, source in-point, transition in, transition
# length, options). anchor = line index (cut lands `offset` s from that line's
# first word), ("c", chunk id) to cut on a phrase inside a line, ("e", line)
# to cut from the end of a line's last word, or "t0" for the very start.
# Clip "BLACK" is plain black. options: speed (<1 = slow motion).
SHOTS = [
    ("t0", 0.0, "C17", 0.0, None, 0, {}),
    (2, -0.10, "C02", 20.8, "fadewhite", 0.30, {}),
    (3, -0.30, "C18", 3.0, "fadeblack", 0.80, {}),
    (4, -0.25, "C05", 2.0, "fade", 0.60, {}),
    (5, -0.25, "C22", 0.5, "fade", 0.50, {}),
    (7, -0.30, "C23", 6.5, "fade", 0.60, {}),
    (8, -0.30, "C10", 0.5, "fade", 0.60, {}),
    (10, -0.15, "C11", 5.0, "fade", 0.25, {}),
    (11, -0.15, "C20", 4.0, "fade", 0.25, {}),
    (12, -0.15, "C07", 25.5, "fade", 0.25, {}),
    (13, -0.15, "C15", 20.0, "fade", 0.25, {}),
    (14, -0.15, "C06", 21.0, "fade", 0.25, {}),
    (15, -0.15, "C03", 28.3, "fade", 0.25, {"speed": 0.6}),
    (16, -0.15, "C13", 0.3, "fade", 0.25, {}),
    (17, -0.30, "C21", 1.5, "fade", 0.60, {}),
    (18, -0.20, "C25", 1.0, "fadeblack", 0.50, {}),
    (19, -0.40, "C19", 5.0, "fade", 1.00, {}),
    (21, -0.30, "C09", 0.5, "fade", 0.60, {}),
    (22, -0.30, "C20", 7.5, "fade", 0.60, {}),
    (23, -0.25, "C24", 0.5, "hblur", 0.50, {}),
    (24, -0.25, "C14", 17.0, "fade", 0.50, {}),
    (25, -0.30, "C07", 6.5, "fadeblack", 0.40, {}),
    (26, -0.30, "C10", 20.0, "fade", 0.80, {}),
    (27, -0.25, "C04", 4.5, "fade", 0.60, {}),
    (28, -0.25, "C03", 2.5, "fade", 0.50, {}),
    (29, -0.25, "C05", 12.0, "fade", 0.50, {}),
    (30, -0.20, "C04", 16.5, "fadewhite", 0.40, {}),
    (31, -0.25, "C03", 9.0, "fade", 0.50, {}),
    (32, -0.30, "C16", 12.0, "fade", 0.80, {}),
    (34, -0.40, "C11", 12.0, "fadeblack", 0.80, {}),
    (35, -0.25, "C26", 2.5, "zoomin", 0.50, {}),
    (36, -0.25, "C13", 13.5, "fade", 0.50, {}),
    (37, -0.30, "C02", 4.0, "fade", 0.60, {}),
    (39, -0.30, "C07", 24.0, "fade", 0.60, {}),
    (40, -0.30, "C12", 9.0, "fade", 0.80, {}),
    (41, -0.30, "C10", 12.5, "fade", 0.60, {}),
    (44, -0.20, "C25", 4.0, "fade", 0.40, {}),
    (45, -0.20, "C14", 8.0, "fade", 0.40, {}),
    (46, -0.20, "C06", 22.0, "fade", 0.40, {}),
    (47, -0.20, "C12", 24.5, "fade", 0.50, {}),
    (48, -0.25, "C22", 7.0, "fade", 0.50, {}),
    (("c", 63), -0.25, "C10", 16.0, "fade", 0.80, {}),
    (49, -0.30, "C19", 12.0, "fade", 0.70, {}),
    (50, -0.20, "C13", 22.5, "fade", 0.40, {}),
    (51, -0.20, "C09", 23.8, "fade", 0.40, {}),
    (52, -0.20, "C15", 3.0, "fadewhite", 0.30, {}),
    (53, -0.30, "C25", 7.0, "fadeblack", 0.60, {}),
    (54, -0.30, "C23", 0.5, "fade", 0.50, {}),
    (57, -0.30, "C12", 0.5, "fade", 0.70, {}),
    (58, -0.30, "C01", 0.5, "fadeblack", 0.60, {}),
    (60, -0.25, "C01", 9.5, "fade", 0.50, {}),
    (61, -0.20, "C03", 14.5, "fade", 0.40, {}),
    (62, -0.15, "C24", 10.0, "fade", 0.30, {}),
    (63, -0.15, "C15", 15.0, "fade", 0.30, {}),
    (64, -0.15, "C21", 9.0, "fade", 0.30, {}),
    (65, -0.15, "C08", 0.3, "fade", 0.30, {}),
    (66, -0.30, "C02", 10.0, "fade", 0.60, {}),
    (67, -0.30, "C11", 17.5, "fade", 0.70, {}),
    (68, -0.25, "C18", 8.0, "fadeblack", 0.50, {}),
    (69, -0.20, "C08", 10.0, "fade", 0.40, {}),
    (71, -0.25, "C14", 0.5, "fade", 0.50, {}),
    (72, -0.40, "C07", 0.8, "fadeblack", 1.00, {}),
    (73, -0.20, "C05", 0.4, "fade", 0.40, {}),
    (74, -0.20, "C19", 0.5, "fade", 0.40, {}),
    (75, -0.20, "C14", 22.5, "fade", 0.40, {}),
    (76, -0.30, "C04", 9.8, "fade", 0.80, {}),
    (77, -0.20, "C17", 20.0, "fadewhite", 0.40, {}),
    (78, -0.25, "C16", 16.5, "fade", 0.50, {}),
    (79, -0.30, "C08", 17.0, "fade", 0.80, {}),
    (81, -0.30, "C06", 3.0, "fade", 0.60, {}),
    (83, -0.30, "C09", 14.5, "fade", 0.60, {}),
    (84, -0.30, "C05", 18.0, "fade", 0.70, {}),
    (85, -2.20, "C01", 12.9, "fadeblack", 1.60, {}),
    (86, -0.50, "C16", 5.5, "fadeblack", 1.00, {}),
    (88, -0.20, "C22", 8.5, "fade", 0.50, {}),
    (89, -0.20, "C09", 7.0, "fade", 0.40, {}),
    (90, -0.20, "C21", 10.4, "fade", 0.40, {}),
    (91, -0.20, "C02", 16.5, "fade", 0.40, {}),
    (92, -0.20, "C09", 19.5, "fade", 0.40, {}),
    (93, -0.30, "C24", 6.5, "fade", 0.60, {}),
    (95, -0.30, "C13", 5.0, "fade", 0.60, {}),
    (96, -0.30, "C15", 8.0, "fade", 0.60, {}),
    (97, -0.12, "C22", 1.0, "fade", 0.25, {}),
    (98, -0.12, "C19", 14.5, "fade", 0.25, {}),
    (99, -0.12, "C01", 26.4, "fade", 0.25, {"speed": 0.5}),
    (100, -0.12, "C12", 10.0, "fade", 0.25, {}),
    (101, -0.25, "C05", 5.0, "fade", 0.60, {}),
    (102, -0.25, "C11", 0.5, "fade", 0.50, {}),
    (103, -0.25, "C23", 9.0, "fade", 0.40, {}),
    (104, -0.40, "C18", 0.6, "fadeblack", 0.80, {}),
    (105, -0.05, "C11", 22.5, "fadewhite", 0.30, {}),
    (106, -0.30, "C12", 14.0, "fade", 0.80, {}),
    (107, -0.30, "C04", 19.5, "fade", 0.60, {}),
    (108, -0.08, "C03", 22.6, "fadewhite", 0.35, {}),
    (109, -0.30, "C15", 22.0, "fade", 0.60, {}),
    (110, -0.10, "C04", 26.85, "fadeblack", 0.40, {"speed": 0.2}),
    (111, -0.10, "C04", 27.40, "fade", 0.25, {"speed": 0.25}),
    (112, -0.10, "C04", 27.95, "fade", 0.25, {"speed": 0.35}),
    (113, -0.40, "C18", 5.0, "fadeblack", 0.60, {}),
    # hard cut to black on her last word; silence holds
    (("e", 113), 0.25, "BLACK", 0.0, "fade", 0.08, {}),
]
