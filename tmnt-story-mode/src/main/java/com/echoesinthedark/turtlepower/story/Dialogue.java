package com.echoesinthedark.turtlepower.story;

import com.echoesinthedark.turtlepower.network.DialoguePacket;
import com.echoesinthedark.turtlepower.network.ModNetwork;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.network.PacketDistributor;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Sends lines of dialogue to players. The client shows them in the dialogue box at the bottom of the
 * screen, writes them to chat and reads them out loud with text-to-speech.
 */
public final class Dialogue {
    private Dialogue() {}

    public enum Kind {
        /** Story lines. Always shown, always spoken. */
        STORY,
        /** Random idle chatter from the brothers. */
        CHATTER,
        /** Short battle cries and enemy taunts. */
        COMBAT
    }

    public record Line(Speaker speaker, String text) {}

    public static Line line(Speaker speaker, String text) {
        return new Line(speaker, text);
    }

    private static final Map<UUID, Map<String, Long>> COOLDOWNS = new HashMap<>();

    public static void say(ServerPlayer player, Speaker speaker, String text) {
        say(player, speaker, text, Kind.STORY);
    }

    public static void say(ServerPlayer player, Speaker speaker, String text, Kind kind) {
        ModNetwork.CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), new DialoguePacket(speaker, text, kind));
    }

    public static void scene(ServerPlayer player, Line... lines) {
        for (Line l : lines) {
            say(player, l.speaker(), l.text(), Kind.STORY);
        }
    }

    /** True (and starts the cooldown) if this player has not heard a line with this key for {@code ticks}. */
    public static boolean ready(ServerPlayer player, String key, int ticks) {
        long now = player.serverLevel().getGameTime();
        Map<String, Long> map = COOLDOWNS.computeIfAbsent(player.getUUID(), u -> new HashMap<>());
        Long last = map.get(key);
        if (last != null && now - last < ticks && now >= last) {
            return false;
        }
        map.put(key, now);
        return true;
    }

    /** Say something to every player near a position, respecting a per-player cooldown. */
    public static void sayNearby(ServerLevel level, Vec3 pos, double radius, Speaker speaker, String text, Kind kind,
                                 String cooldownKey, int cooldownTicks) {
        for (ServerPlayer p : level.players()) {
            if (p.position().distanceToSqr(pos) <= radius * radius && ready(p, cooldownKey, cooldownTicks)) {
                say(p, speaker, text, kind);
            }
        }
    }

    public static void forget(UUID player) {
        COOLDOWNS.remove(player);
    }
}
