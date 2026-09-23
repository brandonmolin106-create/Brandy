package com.echoesinthedark.turtlepower.story;

/** Everyone who can talk in the story, with the colour their name is drawn in. */
public enum Speaker {
    LEO("Leonardo", 0x4D7CFF, "leonardo"),
    DONNIE("Donatello", 0xB070FF, "donatello"),
    MIKEY("Michelangelo", 0xFF9F30, "michelangelo"),
    RAPH("Raphael (you)", 0xFF4A4A, "raphael"),
    SPLINTER("Master Splinter", 0xE0C080, "splinter"),
    APRIL("April O'Neil", 0xFFDC50, "april"),
    KRAANG("Kraang", 0xFF78CF, "kraang_droid"),
    KRAANG_PRIME("Kraang Prime", 0xC860FF, "kraang_prime"),
    FOOT("Foot Ninja", 0xC0C0C0, "foot_ninja"),
    NARRATOR("", 0xE8E8E8, "");

    public final String displayName;
    public final int color;
    /** Texture name used to draw the little face portrait in the dialogue box. */
    public final String portrait;

    Speaker(String displayName, int color, String portrait) {
        this.displayName = displayName;
        this.color = color;
        this.portrait = portrait;
    }
}
