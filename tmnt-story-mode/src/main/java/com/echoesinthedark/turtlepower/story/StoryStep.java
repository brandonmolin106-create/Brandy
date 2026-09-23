package com.echoesinthedark.turtlepower.story;

/** Every step of the story, in order. */
public enum StoryStep {
    NOT_STARTED(0, "", "", null, 0),

    // Chapter 1: Shell Shocked
    GET_SAIS(1, "Chapter 1: Shell Shocked", "Grab your sais from the weapon rack chest in the dojo", "weapon_rack", 0),
    TRAINING(1, "Chapter 1: Shell Shocked", "Train with Master Splinter: knock down the training dummies", "dojo", 3),
    EAT_PIZZA(1, "Chapter 1: Shell Shocked", "Grab a slice from the pizza box in the kitchen and eat it", "pizza_box", 0),
    DONNIE_LAB(1, "Chapter 1: Shell Shocked", "Go see what Donnie found in his lab", "lab", 0),

    // Chapter 2: Topside
    EXIT_SEWER(2, "Chapter 2: Topside", "Take the stairs up to the sewer, climb the ladder and pop the manhole", "main_manhole", 0),
    ROOFTOPS(2, "Chapter 2: Topside", "Climb a fire escape up to the rooftops", "fire_escape_main", 0),
    MEET_APRIL(2, "Chapter 2: Topside", "Meet April O'Neil inside Antonio's Pizza (right click her)", "april", 0),

    // Chapter 3: The Kraang Invasion
    PORTAL(3, "Chapter 3: The Kraang Invasion", "A Kraang portal is opening in Times Square! Get there", "times_square", 0),
    DEFEAT_KRAANG(3, "Chapter 3: The Kraang Invasion", "Defeat the Kraang droids", "times_square", 8),
    COLLECT_MUTAGEN(3, "Chapter 3: The Kraang Invasion", "Collect mutagen canisters (Kraang drop them, and Kraang crates have them)", "kraang_crate", 5),

    // Chapter 4: Mutagen Madness
    MUTANT_LOOSE(4, "Chapter 4: Mutagen Madness", "A mutant is loose in Central Park! Stop Spider Bytez", "park", 0),
    RETURN_LAB(4, "Chapter 4: Mutagen Madness", "Bring the mutagen back to Donnie's lab", "lab", 0),

    // Chapter 5: Showdown at TCRI
    INFILTRATE_TCRI(5, "Chapter 5: Showdown at TCRI", "Sneak into TCRI, the Kraang's secret headquarters", "tcri_door", 0),
    BOSS(5, "Chapter 5: Showdown at TCRI", "Defeat Kraang Prime!", "tcri_boss", 0),
    RETURN_HOME(5, "Chapter 5: Showdown at TCRI", "Head home to the lair. Pizza party!", "lair_hall", 0),

    FREE_ROAM(6, "Protect New York", "The city is yours. Watch out for Kraang portals, mutagen spills and the Foot Clan!", null, 0);

    public final int chapter;
    public final String chapterTitle;
    public final String objective;
    /** Point of interest the objective arrow points at, or null. */
    public final String target;
    /** How many things you need (dummies, droids, canisters). 0 = not a counting step. */
    public final int goal;

    StoryStep(int chapter, String chapterTitle, String objective, String target, int goal) {
        this.chapter = chapter;
        this.chapterTitle = chapterTitle;
        this.objective = objective;
        this.target = target;
        this.goal = goal;
    }

    public StoryStep next() {
        return this == FREE_ROAM ? FREE_ROAM : values()[ordinal() + 1];
    }

    public boolean atLeast(StoryStep other) {
        return ordinal() >= other.ordinal();
    }

    public static StoryStep firstOfChapter(int chapter) {
        for (StoryStep s : values()) {
            if (s.chapter == chapter) return s;
        }
        return FREE_ROAM;
    }
}
