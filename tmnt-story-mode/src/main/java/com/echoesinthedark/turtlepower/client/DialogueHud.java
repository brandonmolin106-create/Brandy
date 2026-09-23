package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.network.DialoguePacket;
import com.echoesinthedark.turtlepower.story.Dialogue;
import com.echoesinthedark.turtlepower.story.Speaker;
import net.minecraft.Util;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.FormattedCharSequence;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;

/**
 * The story dialogue box above the hotbar: a face portrait, the speaker's name in their colour, and
 * the line typing itself out while the text-to-speech voice reads it.
 */
public final class DialogueHud {
    private DialogueHud() {}

    private static final Deque<DialoguePacket> QUEUE = new ArrayDeque<>();
    private static DialoguePacket current;
    private static long shownAt;
    private static long duration;

    public static void push(DialoguePacket p) {
        if (Config.DIALOGUE_IN_CHAT.get()) {
            Minecraft.getInstance().gui.getChat().addMessage(chatLine(p));
        }
        if (p.kind() != Dialogue.Kind.STORY) {
            // Battle cries and chatter only show up when nobody else is talking.
            boolean busy = !QUEUE.isEmpty() || (current != null && Util.getMillis() - shownAt < duration);
            if (busy) return;
        }
        QUEUE.add(p);
    }

    public static void clear() {
        QUEUE.clear();
        current = null;
    }

    private static Component chatLine(DialoguePacket p) {
        Style nameStyle = Style.EMPTY.withColor(TextColor.fromRgb(p.speaker().color)).withBold(true);
        if (p.speaker() == Speaker.NARRATOR) {
            return Component.literal(p.text()).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(0xCCCCCC)).withItalic(true));
        }
        return Component.literal("[" + p.speaker().displayName + "] ").withStyle(nameStyle)
                .append(Component.literal(p.text()).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(0xFFFFFF)).withBold(false)));
    }

    private static void advance() {
        long now = Util.getMillis();
        if (current != null && now - shownAt < duration) {
            return;
        }
        current = QUEUE.poll();
        if (current == null) {
            return;
        }
        shownAt = now;
        int chars = current.text().length();
        duration = current.kind() == Dialogue.Kind.COMBAT ? 1000L + 55L * chars : 1400L + 68L * chars;
        // If you're racing through the story, speed the old lines up so the box keeps up with you.
        int backlog = QUEUE.size();
        if (backlog > 6) duration = duration * 35 / 100;
        else if (backlog > 3) duration = duration * 60 / 100;
        boolean speak = current.kind() != Dialogue.Kind.CHATTER || Config.SPEAK_IDLE_CHATTER.get();
        if (speak) {
            String prefix = Config.SPEAK_SPEAKER_NAMES.get() && current.speaker() != Speaker.NARRATOR
                    ? current.speaker().displayName.replace(" (you)", "") + " says: " : "";
            Tts.say(prefix + current.text(), backlog > 3);
        }
    }

    public static void render(GuiGraphics g, int width, int height) {
        advance();
        if (current == null) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        Font font = mc.font;
        long age = Util.getMillis() - shownAt;
        int boxW = Math.min(width - 20, 340);
        int textW = boxW - 50;
        String shown = current.text().substring(0, (int) Math.min(current.text().length(), age * 50 / 1000 + 1));
        List<FormattedCharSequence> lines = font.split(Component.literal(shown), textW);
        int lineCount = Math.max(2, Math.min(4, font.split(Component.literal(current.text()), textW).size()));
        int boxH = 18 + lineCount * 10;
        int x = (width - boxW) / 2;
        int y = height - 76 - boxH;

        // Fade in/out.
        float alpha = Math.min(1F, age / 150F);
        long left = duration - age;
        if (left < 200) alpha = Math.max(0F, left / 200F);
        int a = (int) (alpha * 200) << 24;
        int border = (int) (alpha * 255) << 24 | current.speaker().color;

        g.fill(x, y, x + boxW, y + boxH, a | 0x101010);
        g.fill(x, y, x + boxW, y + 1, border);
        g.fill(x, y + boxH - 1, x + boxW, y + boxH, border);
        g.fill(x, y, x + 1, y + boxH, border);
        g.fill(x + boxW - 1, y, x + boxW, y + boxH, border);

        int textX = x + 8;
        if (!current.speaker().portrait.isEmpty()) {
            ResourceLocation tex = TurtlePower.id("textures/entity/" + current.speaker().portrait + ".png");
            int s = 32;
            int px = x + 6, py = y + (boxH - s) / 2;
            g.fill(px - 1, py - 1, px + s + 1, py + s + 1, border);
            g.blit(tex, px, py, s, s, 8, 8, 8, 8, 64, 64);
            g.blit(tex, px, py, s, s, 40, 8, 8, 8, 64, 64);
            textX = px + s + 8;
        }
        int ty = y + 5;
        if (current.speaker() != Speaker.NARRATOR) {
            g.drawString(font, Component.literal(current.speaker().displayName).withStyle(s -> s.withBold(true)),
                    textX, ty, current.speaker().color | 0xFF000000, true);
            ty += 11;
        }
        for (int i = 0; i < lines.size() && i < 4; i++) {
            g.drawString(font, lines.get(i), textX, ty + i * 10, 0xFFFFFFFF, true);
        }
        if (!QUEUE.isEmpty() && (age / 400) % 2 == 0) {
            g.drawString(font, "v", x + boxW - 10, y + boxH - 11, 0xFFAAAAAA, false);
        }
    }
}
