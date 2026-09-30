"""Shared timing for picture and sound (6:00 cut). Every beat of the trailer lives
here so the renderer and the score can never drift apart."""

FPS = 24
DURATION = 360.0
W, H = 3840, 2160

# --- Act I: the void ---------------------------------------------------------
SPARK = 20.0                     # the gold star ignites
RINGS = [22.0 + 2.5 * i for i in range(27)] + [
    88.0, 89.2, 90.3, 91.2, 92.0, 92.7, 93.3, 93.8, 94.2, 94.55, 94.85]
# --- Act II: the echo --------------------------------------------------------
GATHER = (60.0, 94.4)            # dust is pulled into the star
BOOM = 95.0                      # the pulse that starts the formation

# --- Act III: the giant formation -------------------------------------------
GROW = (96.2, 274.5)             # growth front crawls over the giant emblem
GROW_RINGS = [110.0 + 10.0 * i for i in range(16)]  # slow heartbeat while it grows
SILENCE = (275.1, 276.0)         # everything holds its breath
COMPLETE = 276.0                 # full formation: the big hit

# --- Act IV: realistic detail -----------------------------------------------
MATERIALIZE = (276.4, 283.0)     # glowing lines solidify into engraved metal
SWEEPS = [(279.0, 283.0), (287.5, 291.5), (322.0, 326.0)]
ORBIT = (277.0, 301.0)           # slow perspective turn around the emblem

# --- Act V: the name ---------------------------------------------------------
LOCKUP = (298.0, 303.0)          # emblem glides into logo position
LETTERS = (302.5, 309.5)         # wordmark letters appear one by one
GLINT = 313.6                    # star glint on "Echoes in the Dark"
TAGLINE = (317.0, 329.0)

# --- Act VI: the light -------------------------------------------------------
REVEAL = (330.0, 332.6)          # light floods out from the star (official logo)
COLLAPSE = (345.8, 348.4)        # light collapses back into the star
STAR_OUT = 356.4                 # last echo, star goes dark
FADE_END = (357.4, 360.0)

LATE_RINGS = [BOOM, COMPLETE, GLINT, REVEAL[0], STAR_OUT]

# Narration (file index, start time in seconds). Files are in assets/voice/.
VOICE = [
    (1, 7.5),     # Before the light... there was only the dark.
    (2, 27.0),    # And in the dark... every sound leaves an echo.
    (3, 49.0),    # A whisper. A heartbeat. A single spark.
    (9, 74.0),    # They said nothing could grow here.
    (10, 86.0),   # They were wrong.
    (4, 100.0),   # From that spark... something began to grow.
    (5, 134.0),   # Line by line. Story by story.
    (11, 166.0),  # Every story we tell... carves itself into the dark.
    (12, 206.0),  # Bigger. Deeper. Darker than anything before.
    (13, 250.0),  # And now... it is almost here.
    (6, 279.5),   # This is where legends are born.
    (7, 311.8),   # Echoes... in the Dark.
    (14, 337.0),  # Our story begins now.
    (8, 350.2),   # Listen closely. The dark is calling.
]
