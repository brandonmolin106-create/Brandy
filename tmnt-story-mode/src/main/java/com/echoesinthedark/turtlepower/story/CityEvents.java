package com.echoesinthedark.turtlepower.story;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.entity.FootNinjaEntity;
import com.echoesinthedark.turtlepower.entity.KraangDroidEntity;
import com.echoesinthedark.turtlepower.entity.Mutation;
import com.echoesinthedark.turtlepower.registry.ModBlocks;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.StoryData.PlayerProgress;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import org.jetbrains.annotations.Nullable;

import java.util.Locale;

/**
 * Random things that happen while you are out in the city: Kraang portals, mutagen spills, Foot
 * Clan ambushes, lost pizza deliveries and Kraang supply drops.
 */
public final class CityEvents {
    private CityEvents() {}

    public enum Type { KRAANG_PORTAL, MUTAGEN_SPILL, FOOT_AMBUSH, PIZZA_DROP, KRAANG_SUPPLY }

    /** Story steps where random events are allowed (not during the big scripted fights). */
    private static boolean allowed(StoryStep s) {
        return switch (s) {
            case MEET_APRIL, COLLECT_MUTAGEN, RETURN_LAB, INFILTRATE_TCRI, RETURN_HOME, FREE_ROAM -> true;
            default -> false;
        };
    }

    static void tick(ServerPlayer p, PlayerProgress pr, StoryData d) {
        if (!Config.RANDOM_EVENTS.get() || !allowed(pr.step)) return;
        if (p.getY() < d.y0 || !StoryManager.inCity(p, d)) return;
        ServerLevel level = p.serverLevel();
        long now = level.getGameTime();
        if (pr.nextEventTick == 0 || pr.nextEventTick - now > 20L * 60 * 60) {
            schedule(pr, now, d);
            return;
        }
        if (now < pr.nextEventTick) return;
        schedule(pr, now, d);
        Type[] types = Type.values();
        trigger(p, d, types[level.random.nextInt(types.length)]);
    }

    private static void schedule(PlayerProgress pr, long now, StoryData d) {
        int min = Config.EVENT_MIN_MINUTES.get();
        int max = Math.max(min, Config.EVENT_MAX_MINUTES.get());
        pr.nextEventTick = now + 20L * 60 * min + (long) (Math.random() * 20 * 60 * (max - min + 1));
        d.setDirty();
    }

    public static Type parse(String s) {
        return Type.valueOf(s.toUpperCase(Locale.ROOT));
    }

    public static void trigger(ServerPlayer p, StoryData d, Type type) {
        ServerLevel level = p.serverLevel();
        BlockPos at = findSpot(level, p, 10, 20);
        if (at == null) at = p.blockPosition().offset(6, 0, 6);
        switch (type) {
            case KRAANG_PORTAL -> {
                Dialogue.say(p, Speaker.DONNIE, "Portal energy spiking right next to you, Raph! Kraang incoming!");
                level.sendParticles(ParticleTypes.PORTAL, at.getX() + 0.5, at.getY() + 1.5, at.getZ() + 0.5, 150, 1, 1.5, 1, 0.8);
                level.playSound(null, at, SoundEvents.PORTAL_TRIGGER, SoundSource.HOSTILE, 0.5F, 1.6F);
                int n = 2 + level.random.nextInt(2);
                for (int i = 0; i < n; i++) spawn(level, ModEntities.KRAANG_DROID.get(), at.offset(i - 1, 0, i % 2), p);
            }
            case MUTAGEN_SPILL -> {
                Dialogue.say(p, Speaker.APRIL, "Raph! A Kraang van just crashed near you and spilled mutagen everywhere. Something's mutating!");
                for (int i = 0; i < 6; i++) {
                    BlockPos o = at.offset(level.random.nextInt(5) - 2, 0, level.random.nextInt(5) - 2);
                    BlockPos ground = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, o);
                    if (level.getBlockState(ground).isAir() && !level.getBlockState(ground.below()).isAir()) {
                        level.setBlock(ground, ModBlocks.MUTAGEN_OOZE.get().defaultBlockState(), 3);
                    }
                }
                EntityType<? extends Mob> victim = switch (level.random.nextInt(3)) {
                    case 0 -> EntityType.SPIDER;
                    case 1 -> EntityType.ZOMBIE;
                    default -> EntityType.SILVERFISH;
                };
                Mob m = spawn(level, victim, at, p);
                if (m != null) Mutation.mutate(level, m, null);
            }
            case FOOT_AMBUSH -> {
                Dialogue.say(p, Speaker.LEO, "Foot Clan! It's an ambush! Back to back, guys!");
                int n = 2 + level.random.nextInt(2);
                for (int i = 0; i < n; i++) {
                    BlockPos s = findSpot(level, p, 6, 12);
                    Mob m = spawn(level, ModEntities.FOOT_NINJA.get(), s == null ? at : s, p);
                    if (m != null) level.sendParticles(ParticleTypes.LARGE_SMOKE, m.getX(), m.getY() + 1, m.getZ(), 20, 0.4, 0.8, 0.4, 0.02);
                }
            }
            case PIZZA_DROP -> {
                Dialogue.say(p, Speaker.MIKEY, "Dude! The pizza delivery guy saw a Kraang, screamed, and dropped his pizzas. Finders keepers!");
                ItemStack[] loot = {new ItemStack(ModItems.PIZZA_SLICE.get(), 4), new ItemStack(ModItems.MIKEY_SPECIAL_PIZZA.get())};
                for (ItemStack s : loot) {
                    ItemEntity ie = new ItemEntity(level, p.getX() + 1, p.getY() + 1, p.getZ() + 1, s);
                    level.addFreshEntity(ie);
                }
            }
            case KRAANG_SUPPLY -> {
                Dialogue.say(p, Speaker.DONNIE, "Kraang supply drop nearby! Two droids are guarding a crate of mutagen. Go get it!");
                BlockPos ground = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, at);
                if (level.getBlockState(ground).isAir()) {
                    level.setBlock(ground, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.NORTH), 3);
                    if (level.getBlockEntity(ground) instanceof ChestBlockEntity chest) {
                        chest.setCustomName(Component.literal("Kraang Crate"));
                        chest.setItem(0, new ItemStack(ModItems.MUTAGEN_CANISTER.get(), 2));
                        chest.setItem(1, new ItemStack(ModItems.SMOKE_BOMB.get(), 2));
                        if (level.random.nextInt(3) == 0) chest.setItem(2, new ItemStack(ModItems.KRAANG_BLASTER.get()));
                    }
                    level.setBlock(ground.east(), ModBlocks.KRAANG_PANEL.get().defaultBlockState(), 3);
                }
                spawn(level, ModEntities.KRAANG_DROID.get(), at.offset(2, 0, 0), p);
                spawn(level, ModEntities.KRAANG_DROID.get(), at.offset(-2, 0, 0), p);
            }
        }
    }

    /** A random open spot on the ground (street or roof) some distance from the player. */
    @Nullable
    private static BlockPos findSpot(ServerLevel level, ServerPlayer p, int minDist, int maxDist) {
        for (int i = 0; i < 20; i++) {
            double ang = level.random.nextDouble() * Math.PI * 2;
            int dist = minDist + level.random.nextInt(maxDist - minDist + 1);
            int x = (int) Math.floor(p.getX() + Math.cos(ang) * dist);
            int z = (int) Math.floor(p.getZ() + Math.sin(ang) * dist);
            if (!level.isLoaded(new BlockPos(x, 0, z))) continue;
            BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, new BlockPos(x, 0, z));
            if (Math.abs(top.getY() - p.getY()) > 20) continue;
            if (level.getBlockState(top).isAir() && level.getBlockState(top.above()).isAir()
                    && level.getFluidState(top.below()).isEmpty()) {
                return top;
            }
        }
        return null;
    }

    @Nullable
    private static Mob spawn(ServerLevel level, EntityType<? extends Mob> type, BlockPos at, ServerPlayer target) {
        Mob m = type.create(level);
        if (m == null) return null;
        m.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, level.random.nextFloat() * 360, 0);
        m.finalizeSpawn(level, level.getCurrentDifficultyAt(at), MobSpawnType.EVENT, null, null);
        m.setTarget(target);
        level.addFreshEntity(m);
        if (m instanceof KraangDroidEntity || m instanceof FootNinjaEntity) {
            level.sendParticles(ParticleTypes.PORTAL, m.getX(), m.getY() + 1, m.getZ(), 30, 0.4, 1, 0.4, 0.5);
        }
        return m;
    }
}
