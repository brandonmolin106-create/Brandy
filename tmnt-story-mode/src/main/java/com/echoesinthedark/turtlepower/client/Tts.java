package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.TurtlePower;
import com.mojang.text2speech.Narrator;
import net.minecraft.client.GameNarrator;
import net.minecraft.client.Minecraft;
import org.jetbrains.annotations.Nullable;

import java.lang.reflect.Field;

/**
 * Text-to-speech using the same speech engine Minecraft's built-in Narrator uses (Windows voices on
 * Windows, the system voice on macOS, flite on Linux). It works even when Minecraft's own Narrator
 * option is off, and can be switched off in the mod config or with sneak + right click on the T-Phone.
 */
public final class Tts {
    private Tts() {}

    @Nullable private static Narrator narrator;
    private static boolean looked;

    @Nullable
    private static Narrator engine() {
        if (!looked) {
            looked = true;
            // Re-use the engine Minecraft already started, so we don't load the speech library twice.
            try {
                GameNarrator gn = Minecraft.getInstance().getNarrator();
                for (Field f : GameNarrator.class.getDeclaredFields()) {
                    if (Narrator.class.isAssignableFrom(f.getType())) {
                        f.setAccessible(true);
                        narrator = (Narrator) f.get(gn);
                        break;
                    }
                }
            } catch (Throwable t) {
                TurtlePower.LOGGER.debug("Could not reuse Minecraft's narrator", t);
            }
            if (narrator == null) {
                try {
                    narrator = Narrator.getNarrator();
                } catch (Throwable t) {
                    TurtlePower.LOGGER.warn("Text-to-speech is not available on this computer", t);
                }
            }
        }
        return narrator;
    }

    public static boolean available() {
        Narrator n = engine();
        try {
            return n != null && n.active();
        } catch (Throwable t) {
            return false;
        }
    }

    public static void say(String text) {
        say(text, false);
    }

    /** @param interrupt cut off whatever is being said right now (used when the story is catching up) */
    public static void say(String text, boolean interrupt) {
        if (!Config.TEXT_TO_SPEECH.get() || text.isBlank()) {
            return;
        }
        Narrator n = engine();
        if (n == null) {
            return;
        }
        try {
            if (n.active()) {
                n.say(text, interrupt);
            }
        } catch (Throwable t) {
            TurtlePower.LOGGER.debug("Text-to-speech failed", t);
        }
    }

    public static void stop() {
        Narrator n = engine();
        if (n != null) {
            try {
                n.clear();
            } catch (Throwable ignored) {
            }
        }
    }
}
