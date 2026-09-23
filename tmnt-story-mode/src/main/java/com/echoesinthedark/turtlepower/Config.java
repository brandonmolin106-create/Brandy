package com.echoesinthedark.turtlepower;

import net.minecraftforge.common.ForgeConfigSpec;

public final class Config {
    private Config() {}

    public static final ForgeConfigSpec CLIENT_SPEC;
    public static final ForgeConfigSpec.BooleanValue TEXT_TO_SPEECH;
    public static final ForgeConfigSpec.BooleanValue SPEAK_SPEAKER_NAMES;
    public static final ForgeConfigSpec.BooleanValue SPEAK_IDLE_CHATTER;
    public static final ForgeConfigSpec.BooleanValue RAPH_SKIN;
    public static final ForgeConfigSpec.BooleanValue SHOW_OBJECTIVE_HUD;
    public static final ForgeConfigSpec.BooleanValue DIALOGUE_IN_CHAT;

    public static final ForgeConfigSpec COMMON_SPEC;
    public static final ForgeConfigSpec.BooleanValue RANDOM_EVENTS;
    public static final ForgeConfigSpec.IntValue EVENT_MIN_MINUTES;
    public static final ForgeConfigSpec.IntValue EVENT_MAX_MINUTES;
    public static final ForgeConfigSpec.BooleanValue IDLE_CHATTER;
    public static final ForgeConfigSpec.BooleanValue OFFER_STORY_IN_NORMAL_WORLDS;

    static {
        ForgeConfigSpec.Builder c = new ForgeConfigSpec.Builder();
        c.push("voice");
        TEXT_TO_SPEECH = c.comment("Read story dialogue out loud with your computer's text-to-speech voice.")
                .define("textToSpeech", true);
        SPEAK_SPEAKER_NAMES = c.comment("Say who is talking before each line (\"Leo says...\").")
                .define("speakSpeakerNames", false);
        SPEAK_IDLE_CHATTER = c.comment("Also read the brothers' random idle chatter out loud.")
                .define("speakIdleChatter", true);
        c.pop();
        c.push("look");
        RAPH_SKIN = c.comment("Draw you as Raphael (green skin, red mask, shell) once the story has started.")
                .define("raphaelSkin", true);
        SHOW_OBJECTIVE_HUD = c.comment("Show the current story objective in the top-left corner.")
                .define("objectiveHud", true);
        DIALOGUE_IN_CHAT = c.comment("Also copy every line of dialogue into the chat window.")
                .define("dialogueInChat", false);
        c.pop();
        CLIENT_SPEC = c.build();

        ForgeConfigSpec.Builder s = new ForgeConfigSpec.Builder();
        s.push("story");
        RANDOM_EVENTS = s.comment("Random city events (Kraang portals, mutagen spills, Foot Clan ambushes, pizza drops).")
                .define("randomEvents", true);
        EVENT_MIN_MINUTES = s.defineInRange("eventMinMinutes", 3, 1, 120);
        EVENT_MAX_MINUTES = s.defineInRange("eventMaxMinutes", 6, 1, 240);
        IDLE_CHATTER = s.comment("Let Leo, Donnie and Mikey talk to you now and then.")
                .define("idleChatter", true);
        OFFER_STORY_IN_NORMAL_WORLDS = s.comment("In worlds that were not made with the TMNT New York world type, show a clickable chat message offering to start the story.")
                .define("offerStoryInNormalWorlds", true);
        s.pop();
        COMMON_SPEC = s.build();
    }
}
