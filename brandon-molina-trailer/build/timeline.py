import json, os
S = os.path.dirname(os.path.abspath(__file__))
FPS = 30
W, H = 1080, 1920
TOTAL = 68.0

PICKS = json.load(open(f'{S}/picks.json'))

# the nine story clips: (pick index, start, end)
CLIPS = [
    (0, 5.0, 10.2),   # heavier than you can explain
    (1, 10.2, 15.2),  # surrounded by people, still alone
    (2, 15.2, 18.8),  # perfect words
    (3, 18.8, 23.4),  # you can just be here
    (4, 25.8, 30.0),  # keep going
    (5, 30.0, 33.2),  # look at the sky
    (6, 33.2, 37.6),  # fall asleep
    (7, 37.6, 40.4),  # don't have to answer
    (8, 40.4, 44.6),  # pretend you're happy
]
INTERLUDE = (23.4, 25.8)
MONTAGE = (44.6, 48.6)
HOLD = (9, 48.6, 61.0)   # direct look -> title
TITLE_IN, TAG_IN = 56.0, 57.4
SKY_START = 61.0
HANDLE_IN = 62.2
FADE_OUT = (66.3, 68.0)

# narration: (file index, start, reverb size 0..1)
VO = [
    (1, 5.6, 0.25), (2, 10.6, 0.3), (3, 15.6, 0.3), (4, 19.6, 0.85),
    (5, 26.2, 0.3), (6, 30.3, 0.45), (7, 33.5, 0.35), (8, 38.0, 0.35),
    (9, 40.8, 0.5), (10, 45.6, 0.9), (11, 50.6, 1.0), (12, 53.6, 1.0),
]
VO_TEXT = [
    "If tonight feels heavier than you can explain…",
    "if you're surrounded by people… but still feel alone…",
    "you don't have to find the perfect words.",
    "You can just be here.",
    "Watch when you need something that helps you keep going.",
    "Listen while you look at the sky.",
    "Put one of my videos on while you're trying to fall asleep.",
    "You don't have to answer.",
    "You don't have to pretend you're happy.",
    "Just take this moment.",
    "Breathe.",
    "Stay.",
]

# hits / cuts where a flash + impact land
IMPACTS = [(25.8, 0.6), (40.4, 0.8), (44.6, 0.7), (48.6, 1.0)]
SOFT_HITS = [c[1] for c in CLIPS[1:4]] + [c[1] for c in CLIPS[5:8]]
GLIMPSE = (2.55, 3.05)
