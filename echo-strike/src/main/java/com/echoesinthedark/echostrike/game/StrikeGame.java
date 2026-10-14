package com.echoesinthedark.echostrike.game;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.entity.OperativeEntity;
import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.registry.ModEntities;
import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.border.WorldBorder;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;

/**
 * The game modes. One per server, lives in memory while the server runs.
 *
 * WAVES: operatives spawn around the players in bigger and bigger waves. Survive as long as you can.
 * BATTLE_ROYALE: everyone is scattered over the map with a pistol, loot crates are dropped around,
 * the world border shrinks to a point, last one standing wins. Bots fill the lobby if you're alone.
 */
public final class StrikeGame {
    public enum Mode { NONE, WAVES, BATTLE_ROYALE }

    private static final Map<MinecraftServer, StrikeGame> GAMES = new WeakHashMap<>();

    /** Used by the developer test script only. */
    public static BlockPos devCenter = BlockPos.ZERO;

    public static StrikeGame get(MinecraftServer server) {
        return GAMES.computeIfAbsent(server, StrikeGame::new);
    }

    private final MinecraftServer server;
    private Mode mode = Mode.NONE;
    private ServerLevel level;
    private final Map<UUID, Integer> kills = new HashMap<>();
    private final Set<UUID> alive = new HashSet<>();
    private final Set<UUID> eliminated = new HashSet<>();
    private int tick;

    // waves
    private int wave;
    private int breakTicks;
    private int waveKills;

    // battle royale
    private BlockPos center;
    private double startSize;
    private int shrinkTicks;
    private int graceTicks;
    private double originalBorderSize = -1;
    private double originalBorderX, originalBorderZ;

    private StrikeGame(MinecraftServer server) {
        this.server = server;
    }

    public Mode mode() {
        return mode;
    }

    public int kills(Player p) {
        return kills.getOrDefault(p.getUUID(), 0);
    }

    public int wave() {
        return wave;
    }

    // ---------------------------------------------------------------- messaging

    private void broadcast(Component msg) {
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            p.sendSystemMessage(msg);
        }
    }

    private void title(ServerPlayer p, String title, String sub, ChatFormatting color) {
        p.connection.send(new ClientboundSetTitlesAnimationPacket(5, 40, 10));
        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(sub).withStyle(ChatFormatting.WHITE)));
        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal(title).withStyle(color, ChatFormatting.BOLD)));
    }

    private void titleAll(String title, String sub, ChatFormatting color) {
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            title(p, title, sub, color);
        }
    }

    private void actionBarAll(String text, ChatFormatting color) {
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            p.displayClientMessage(Component.literal(text).withStyle(color), true);
        }
    }

    private void soundAll(net.minecraft.sounds.SoundEvent sound, float pitch) {
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            p.level().playSound(null, p.getX(), p.getY(), p.getZ(), sound, SoundSource.MASTER, 1.0F, pitch);
        }
    }

    // ---------------------------------------------------------------- loadouts

    public static void giveKit(ServerPlayer p, String kit) {
        p.getInventory().clearContent();
        p.setHealth(p.getMaxHealth());
        p.getFoodData().setFoodLevel(20);
        switch (kit.toLowerCase()) {
            case "sniper" -> {
                p.getInventory().add(new ItemStack(ModItems.AWM.get()));
                p.getInventory().add(new ItemStack(ModItems.DEAGLE.get()));
                p.getInventory().add(new ItemStack(ModItems.SNIPER_ROUNDS.get(), 30));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 35));
            }
            case "shotgun", "breacher" -> {
                p.getInventory().add(new ItemStack(ModItems.M870.get()));
                p.getInventory().add(new ItemStack(ModItems.VECTOR.get()));
                p.getInventory().add(new ItemStack(ModItems.SHOTGUN_SHELLS.get(), 40));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 99));
            }
            case "smg", "rusher" -> {
                p.getInventory().add(new ItemStack(ModItems.MP5.get()));
                p.getInventory().add(new ItemStack(ModItems.UMP45.get()));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 64));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 64));
            }
            case "heavy", "lmg" -> {
                p.getInventory().add(new ItemStack(ModItems.M249.get()));
                p.getInventory().add(new ItemStack(ModItems.G18.get()));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 64));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 64));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 40));
            }
            case "pistol", "starter" -> {
                p.getInventory().add(new ItemStack(ModItems.G18.get()));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 40));
            }
            case "m4", "ranger" -> {
                p.getInventory().add(new ItemStack(ModItems.M4A1.get()));
                p.getInventory().add(new ItemStack(ModItems.DEAGLE.get()));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 64));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 64));
            }
            default -> {
                p.getInventory().add(new ItemStack(ModItems.AK47.get()));
                p.getInventory().add(new ItemStack(ModItems.G18.get()));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 64));
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 56));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 40));
            }
        }
        p.getInventory().add(new ItemStack(ModItems.COMBAT_KNIFE.get()));
        p.getInventory().add(new ItemStack(ModItems.FRAG_GRENADE.get(), 2));
        p.getInventory().add(new ItemStack(ModItems.MEDKIT.get(), 2));
        p.getInventory().add(new ItemStack(ModItems.ARMOR_PLATE.get(), 2));
        p.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.STRIKE_VEST.get()));
        p.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModItems.STRIKE_HELMET.get()));
        p.getInventory().selected = 0;
        p.inventoryMenu.broadcastChanges();
    }

    // ---------------------------------------------------------------- lifecycle

    public void stop(boolean announce) {
        if (mode == Mode.NONE) return;
        Mode old = mode;
        mode = Mode.NONE;
        if (level != null) {
            for (OperativeEntity op : level.getEntitiesOfClass(OperativeEntity.class, playArea(), StrikeGame::isGameSpawned)) {
                op.discard();
            }
            if (originalBorderSize > 0) {
                WorldBorder b = level.getWorldBorder();
                b.setCenter(originalBorderX, originalBorderZ);
                b.setSize(originalBorderSize);
                originalBorderSize = -1;
            }
        }
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (p.gameMode.getGameModeForPlayer() == GameType.SPECTATOR && eliminated.contains(p.getUUID())) {
                p.setGameMode(GameType.SURVIVAL);
                if (center != null) {
                    p.teleportTo(level, center.getX() + 0.5, center.getY() + 1, center.getZ() + 0.5, p.getYRot(), 0);
                }
            }
        }
        eliminated.clear();
        if (announce) {
            broadcast(Component.literal("[Echo Strike] " + (old == Mode.WAVES ? "Wave Survival" : "Battle Royale") + " over.").withStyle(ChatFormatting.GRAY));
        }
        alive.clear();
        kills.clear();
    }

    public boolean startWaves(ServerPlayer starter) {
        stop(false);
        mode = Mode.WAVES;
        level = starter.serverLevel();
        center = starter.blockPosition();
        wave = 0;
        waveKills = 0;
        breakTicks = 100;
        kills.clear();
        alive.clear();
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            alive.add(p.getUUID());
            p.setGameMode(GameType.SURVIVAL);
            giveKit(p, "assault");
        }
        titleAll("WAVE SURVIVAL", "Operatives incoming. Hold the line!", ChatFormatting.RED);
        broadcast(Component.literal("[Echo Strike] Wave Survival started. Each wave is bigger and meaner. /strike stop to quit.").withStyle(ChatFormatting.GOLD));
        return true;
    }

    public boolean startBattleRoyale(ServerPlayer starter, int minutes, int bots) {
        stop(false);
        mode = Mode.BATTLE_ROYALE;
        level = starter.serverLevel();
        kills.clear();
        alive.clear();
        eliminated.clear();
        center = starter.blockPosition();
        startSize = 320;
        shrinkTicks = Math.max(1, minutes) * 1200;
        graceTicks = 200;

        WorldBorder border = level.getWorldBorder();
        originalBorderSize = border.getSize();
        originalBorderX = border.getCenterX();
        originalBorderZ = border.getCenterZ();
        border.setCenter(center.getX() + 0.5, center.getZ() + 0.5);
        border.setSize(startSize);
        border.setDamagePerBlock(0.5);
        border.setDamageSafeZone(1);

        RandomSource rand = level.random;
        List<ServerPlayer> players = new ArrayList<>(server.getPlayerList().getPlayers());
        for (ServerPlayer p : players) {
            alive.add(p.getUUID());
            p.setGameMode(GameType.SURVIVAL);
            giveKit(p, "starter");
            BlockPos spot = randomSpot(rand, startSize * 0.38);
            p.teleportTo(level, spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, rand.nextFloat() * 360, 0);
            p.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE, graceTicks, 4, false, false));
        }
        int crates = 28 + bots;
        for (int i = 0; i < crates; i++) {
            LootCrates.place(level, randomSpot(rand, startSize * 0.45), rand);
        }
        for (int i = 0; i < bots; i++) {
            BlockPos spot = randomSpot(rand, startSize * 0.42);
            spawnOperative(spot, 1 + rand.nextInt(3), 1 + i);
        }
        titleAll("BATTLE ROYALE", "Last one standing wins. The zone closes in " + minutes + " min.", ChatFormatting.AQUA);
        broadcast(Component.literal("[Echo Strike] Battle Royale: " + players.size() + " players, " + bots + " bots, " + crates
                + " loot crates. Find guns, watch the zone!").withStyle(ChatFormatting.GOLD));
        return true;
    }

    private BlockPos randomSpot(RandomSource rand, double radius) {
        double a = rand.nextDouble() * Math.PI * 2;
        double r = Math.sqrt(rand.nextDouble()) * radius;
        int x = center.getX() + (int) (Math.cos(a) * r);
        int z = center.getZ() + (int) (Math.sin(a) * r);
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
        return new BlockPos(x, y, z);
    }

    @Nullable
    private OperativeEntity spawnOperative(BlockPos pos, int tier, int team) {
        OperativeEntity op = ModEntities.OPERATIVE.get().create(level);
        if (op == null) return null;
        op.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, level.random.nextFloat() * 360, 0);
        op.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), MobSpawnType.EVENT, null, null);
        op.setTier(tier);
        op.setSquad(team);
        op.getPersistentData().putBoolean("StrikeSpawned", true);
        level.addFreshEntity(op);
        return op;
    }

    // ---------------------------------------------------------------- events from the world

    public void onKill(ServerPlayer killer, Entity victim) {
        if (mode == Mode.NONE) return;
        kills.merge(killer.getUUID(), 1, Integer::sum);
        if (mode == Mode.WAVES && victim instanceof OperativeEntity) {
            waveKills++;
        }
        if (victim instanceof OperativeEntity || victim instanceof Player) {
            killer.displayClientMessage(Component.literal("ELIMINATED  (" + kills(killer) + " kills)").withStyle(ChatFormatting.RED, ChatFormatting.BOLD), true);
        }
    }

    public void onPlayerDeath(ServerPlayer p) {
        if (mode == Mode.NONE || !alive.remove(p.getUUID())) return;
        if (mode == Mode.BATTLE_ROYALE) {
            eliminated.add(p.getUUID());
            broadcast(Component.literal(p.getName().getString() + " was eliminated. " + alive.size() + " left.").withStyle(ChatFormatting.YELLOW));
        } else {
            broadcast(Component.literal(p.getName().getString() + " went down on wave " + wave + " with " + kills(p) + " kills.").withStyle(ChatFormatting.YELLOW));
        }
    }

    public void onPlayerRespawn(ServerPlayer p) {
        if (mode == Mode.BATTLE_ROYALE && eliminated.contains(p.getUUID())) {
            p.setGameMode(GameType.SPECTATOR);
            if (center != null) {
                p.teleportTo(level, center.getX() + 0.5, center.getY() + 30, center.getZ() + 0.5, 0, 60);
            }
            p.displayClientMessage(Component.literal("You're out. Spectating until the round ends.").withStyle(ChatFormatting.GRAY), false);
        } else if (mode == Mode.WAVES) {
            // Waves are forgiving: you come back with a fresh kit and keep playing.
            alive.add(p.getUUID());
            giveKit(p, "assault");
        }
    }

    // ---------------------------------------------------------------- ticking

    public void tick() {
        if (mode == Mode.NONE || level == null) return;
        tick++;
        if (server.getPlayerList().getPlayerCount() == 0) {
            stop(false);
            return;
        }
        if (mode == Mode.WAVES) tickWaves();
        else tickBattleRoyale();
    }

    private void tickWaves() {
        List<OperativeEntity> ops = level.getEntitiesOfClass(OperativeEntity.class, playArea(), e -> e.isAlive() && isGameSpawned(e));
        if (breakTicks > 0) {
            breakTicks--;
            if (breakTicks % 20 == 0 && breakTicks <= 100 && breakTicks > 0) {
                actionBarAll("Wave " + (wave + 1) + " in " + (breakTicks / 20) + "...", ChatFormatting.YELLOW);
                soundAll(SoundEvents.NOTE_BLOCK_PLING.get(), 1.0F + (5 - breakTicks / 20) * 0.15F);
            }
            if (breakTicks == 0) {
                nextWave();
            }
            return;
        }
        if (ops.isEmpty()) {
            titleAll("WAVE " + wave + " CLEARED", "Supplies dropped. Next wave in 15s.", ChatFormatting.GREEN);
            soundAll(SoundEvents.PLAYER_LEVELUP, 1.0F);
            for (ServerPlayer p : participants()) {
                p.getInventory().add(new ItemStack(ModItems.HEAVY_AMMO.get(), 30));
                p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 24));
                p.getInventory().add(new ItemStack(ModItems.MEDKIT.get()));
                p.getInventory().add(new ItemStack(ModItems.ARMOR_PLATE.get()));
                if (wave % 3 == 0) {
                    GunType[] rewards = {GunType.M870, GunType.AWM, GunType.M249, GunType.VECTOR, GunType.M4A1, GunType.UMP45};
                    GunType g = rewards[(wave / 3 - 1) % rewards.length];
                    p.getInventory().add(new ItemStack(ModItems.gunFor(g)));
                    p.getInventory().add(new ItemStack(g.ammo.get(), 40));
                }
            }
            breakTicks = 300;
        } else if (tick % 40 == 0) {
            actionBarAll("Wave " + wave + "   |   " + ops.size() + " operatives left", ChatFormatting.RED);
            // Nudge wandering operatives toward the nearest player so waves never stall.
            for (OperativeEntity op : ops) {
                if (op.getTarget() == null) {
                    Player near = level.getNearestPlayer(op, 64);
                    if (near != null) op.setTarget(near);
                }
            }
        }
    }

    /** Players taking part: alive ones in the game's level, else anyone on the server. */
    private List<ServerPlayer> participants() {
        List<ServerPlayer> out = new ArrayList<>();
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (p.level() == level && p.isAlive() && !p.isSpectator()) out.add(p);
        }
        if (out.isEmpty()) out.addAll(server.getPlayerList().getPlayers());
        return out;
    }

    private void nextWave() {
        List<ServerPlayer> players = participants();
        if (players.isEmpty()) return;
        wave++;
        waveKills = 0;
        int count = 3 + wave * 2 + players.size();
        RandomSource rand = level.random;
        for (int i = 0; i < count; i++) {
            ServerPlayer around = players.get(rand.nextInt(players.size()));
            double a = rand.nextDouble() * Math.PI * 2;
            double r = 16 + rand.nextDouble() * 16;
            int x = (int) (around.getX() + Math.cos(a) * r);
            int z = (int) (around.getZ() + Math.sin(a) * r);
            int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
            int tier = Math.min(4, (wave - 1) / 2 + (rand.nextInt(4) == 0 ? 1 : 0));
            OperativeEntity op = spawnOperative(new BlockPos(x, y, z), tier, 99);
            if (op != null) op.setTarget(around);
        }
        titleAll("WAVE " + wave, count + " operatives", ChatFormatting.RED);
        soundAll(SoundEvents.RAID_HORN.get(), 1.0F);
    }

    private void tickBattleRoyale() {
        WorldBorder border = level.getWorldBorder();
        if (graceTicks > 0) {
            graceTicks--;
            if (graceTicks == 0) {
                border.lerpSizeBetween(startSize, 12, shrinkTicks * 50L);
                titleAll("THE ZONE IS CLOSING", "Stay inside the border!", ChatFormatting.AQUA);
                soundAll(SoundEvents.RAID_HORN.get(), 0.8F);
            } else if (graceTicks % 20 == 0 && graceTicks <= 100) {
                actionBarAll("Zone closes in " + (graceTicks / 20) + "...", ChatFormatting.AQUA);
            }
            return;
        }
        if (tick % 40 == 0) {
            List<OperativeEntity> bots = level.getEntitiesOfClass(OperativeEntity.class, playArea(), e -> e.isAlive() && isGameSpawned(e));
            int left = alive.size() + bots.size();
            actionBarAll(left + " left   |   zone " + (int) border.getSize() + " blocks", ChatFormatting.AQUA);
            // Bots outside the zone walk in; the border hurts them like it hurts you.
            for (OperativeEntity bot : bots) {
                if (!border.isWithinBounds(bot.getBoundingBox())) {
                    Vec3 c = new Vec3(border.getCenterX(), bot.getY(), border.getCenterZ());
                    bot.getNavigation().moveTo(c.x, c.y, c.z, 1.2);
                } else if (bot.getTarget() == null && tick % 200 == 0) {
                    Player near = level.getNearestPlayer(bot, 40);
                    if (near != null && alive.contains(near.getUUID())) bot.setTarget(near);
                }
            }
            if (left <= 1) {
                finishBattleRoyale(bots);
            }
        }
    }

    private void finishBattleRoyale(List<OperativeEntity> bots) {
        String winner;
        if (alive.size() == 1) {
            UUID id = alive.iterator().next();
            ServerPlayer p = server.getPlayerList().getPlayer(id);
            winner = p == null ? "someone" : p.getName().getString();
            if (p != null) {
                title(p, "VICTORY", "You are the last one standing! " + kills(p) + " kills", ChatFormatting.GOLD);
                p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.MASTER, 1.0F, 1.0F);
            }
        } else if (!bots.isEmpty()) {
            winner = "the bots";
        } else {
            winner = "nobody";
        }
        broadcast(Component.literal("[Echo Strike] Battle Royale over. Winner: " + winner).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (!alive.contains(p.getUUID())) {
                title(p, "ROUND OVER", winner + " won", ChatFormatting.GRAY);
            }
        }
        stop(false);
    }

    private AABB playArea() {
        BlockPos c = center != null ? center : BlockPos.ZERO;
        return new AABB(c).inflate(640, 320, 640);
    }

    private static boolean isGameSpawned(OperativeEntity e) {
        return e.getPersistentData().getBoolean("StrikeSpawned");
    }

    public static void onServerStopping(MinecraftServer server) {
        StrikeGame g = GAMES.remove(server);
        if (g != null) g.stop(false);
    }

    public static String describe(StrikeGame g) {
        return switch (g.mode) {
            case NONE -> "No game running. Try /strike waves start or /strike br start.";
            case WAVES -> "Wave Survival, wave " + g.wave;
            case BATTLE_ROYALE -> "Battle Royale, " + g.alive.size() + " players alive";
        };
    }

    static {
        EchoStrike.LOGGER.debug("StrikeGame loaded");
    }
}
