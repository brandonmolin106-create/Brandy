package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.network.DialoguePacket;
import com.echoesinthedark.turtlepower.network.ObjectivePacket;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;

/** Client-side entry points called from packets and items. Only ever loaded on the client. */
public final class ClientHooks {
    private ClientHooks() {}

    public static void onDialogue(DialoguePacket packet) {
        DialogueHud.push(packet);
    }

    public static void onObjective(ObjectivePacket packet) {
        ObjectiveHud.set(packet);
    }

    public static void toggleTextToSpeech() {
        setTextToSpeech(!Config.TEXT_TO_SPEECH.get());
    }

    public static void setTextToSpeech(boolean on) {
        Config.TEXT_TO_SPEECH.set(on);
        Config.TEXT_TO_SPEECH.save();
        Minecraft mc = Minecraft.getInstance();
        if (!on) {
            Tts.stop();
        }
        if (mc.player != null) {
            String extra = on && !Tts.available() ? " (no speech voice found on this computer)" : "";
            mc.player.displayClientMessage(Component.literal("Story voice: " + (on ? "ON" : "OFF") + extra)
                    .withStyle(on ? ChatFormatting.GREEN : ChatFormatting.GRAY), true);
        }
        if (on) {
            Tts.say("Voice on. Booyakasha!");
        }
    }
}
