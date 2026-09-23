package com.echoesinthedark.turtlepower.story;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.entity.Brother;
import com.echoesinthedark.turtlepower.entity.KraangDroidEntity;
import com.echoesinthedark.turtlepower.entity.KraangPrimeEntity;
import com.echoesinthedark.turtlepower.entity.Mutation;
import com.echoesinthedark.turtlepower.entity.StoryNpcEntity;
import com.echoesinthedark.turtlepower.entity.TrainingDummyEntity;
import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import com.echoesinthedark.turtlepower.network.ModNetwork;
import com.echoesinthedark.turtlepower.network.ObjectivePacket;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.StoryData.PlayerProgress;
import com.echoesinthedark.turtlepower.world.BuildJob;
import com.echoesinthedark.turtlepower.world.BuildQueue;
import com.echoesinthedark.turtlepower.world.Layout;
import com.echoesinthedark.turtlepower.world.StoryWorldBuilder;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Spider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.FlatLevelSource;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.event.entity.living.LivingEntityUseItemEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.network.PacketDistributor;
import org.jetbrains.annotations.Nullable;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Runs the story: builds the world, starts players off in the lair, checks objectives, spawns the
 * big story fights, keeps the brothers next to you, and hands out rewards.
 */
@Mod.EventBusSubscriber(modid = TurtlePower.MODID)
public final class StoryManager {
    private StoryManager() {}

    public static final ResourceKey<Biome> NEW_YORK_BIOME = ResourceKey.create(Registries.BIOME, TurtlePower.id("new_york"));
    public static final String WAVE_TAG = "turtlepower_wave";
    public static final String BOSS_TAG = "turtlepower_story_boss";

    @Nullable private static BuildJob activeJob;
    private static final Set<UUID> START_AFTER_BUILD = new HashSet<>();
    private static boolean startEveryoneAfterBuild;
    private static final Map<UUID, ServerBossEvent> BOSS_BARS = new HashMap<>();

    // =================================================================== building

    public static boolean isBuilding() {
        return activeJob != null;
    }

    /** True for worlds made with the "TMNT New York" world type. */
    public static boolean isTmntWorld(ServerLevel overworld) {
        return overworld.getChunkSource().getGenerator() instanceof FlatLevelSource flat
                && flat.settings().getBiome().is(NEW_YORK_BIOME);
    }

    /** Start building the city centred on (x, z). Returns false if it's already built or building. */
    public static boolean beginBuild(ServerLevel level, int x, int z, @Nullable ServerPlayer starter, boolean worldType) {
        StoryData d = StoryData.get(level.getServer());
        if (activeJob != null || d.built || level.dimension() != Level.OVERWORLD) {
            return false;
        }
        int y0 = StoryWorldBuilder.pickStreetLevel(level, x, z);
        BlockPos centre = new BlockPos(x, y0, z);
        BuildQueue q = new BuildQueue(level.getSeed() ^ centre.asLong());
        Layout layout = StoryWorldBuilder.plan(q, centre);
        TurtlePower.LOGGER.info("Planned TMNT story world at {} with {} blocks", centre, q.size());
        d.building = true;
        if (starter != null) START_AFTER_BUILD.add(starter.getUUID());
        if (worldType) startEveryoneAfterBuild = true;
        activeJob = new BuildJob(level, q, layout, job -> onBuilt(job, worldType));
        level.getServer().getPlayerList().broadcastSystemMessage(Component.literal(
                "Cowabunga! Building New York City, the sewers and the lair. Hang tight for a few seconds...")
                .withStyle(ChatFormatting.GREEN), false);
        return true;
    }

    private static void onBuilt(BuildJob job, boolean setWorldSpawn) {
        ServerLevel level = job.level();
        StoryData d = StoryData.get(level.getServer());
        Layout L = job.layout();
        d.built = true;
        d.building = false;
        d.y0 = L.y0;
        d.origin = new BlockPos(L.ox, L.y0, L.oz);
        d.pois.clear();
        d.pois.putAll(L.pois());
        d.poiLists.clear();
        L.poiLists().forEach((k, v) -> d.poiLists.put(k, List.copyOf(v)));
        d.setDirty();
        BlockPos home = d.poi("raph_room");
        if (setWorldSpawn && home != null) {
            level.setDefaultSpawnPos(home, 0F);
        }
        for (ServerPlayer p : level.getServer().getPlayerList().getPlayers()) {
            if (startEveryoneAfterBuild || START_AFTER_BUILD.contains(p.getUUID())) {
                startStory(p);
            }
        }
        START_AFTER_BUILD.clear();
        startEveryoneAfterBuild = false;
    }

    // =================================================================== starting

    public static void startStory(ServerPlayer p) {
        MinecraftServer server = p.getServer();
        StoryData d = StoryData.get(server);
        if (!d.built) {
            return;
        }
        PlayerProgress pr = d.progress(p.getUUID());
        ServerLevel ow = server.overworld();
        BlockPos home = d.poi("raph_room");
        if (home != null) {
            p.teleportTo(ow, home.getX() + 0.5, home.getY(), home.getZ() + 0.5, 180F, 0F);
            p.setRespawnPosition(ow.dimension(), home, 180F, true, false);
        }
        equip(p, EquipmentSlot.HEAD, new ItemStack(ModItems.RAPH_MASK.get()));
        equip(p, EquipmentSlot.CHEST, new ItemStack(ModItems.TURTLE_SHELL.get()));

        title(p, Component.literal("TURTLE POWER").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD),
                Component.literal("Story Mode - you are Raphael").withStyle(ChatFormatting.RED));
        Dialogue.scene(p, StoryScripts.OPENING);
        p.sendSystemMessage(Component.literal("Tip: the green arrow in the top-left shows where to go. Your T-Phone (from Donnie) repeats the mission.")
                .withStyle(ChatFormatting.GRAY));
        enter(p, pr, StoryStep.GET_SAIS, true);
        maintainBrothers(p, pr, d);
        p.refreshDisplayName();
    }

    private static void equip(ServerPlayer p, EquipmentSlot slot, ItemStack stack) {
        if (p.getItemBySlot(slot).isEmpty()) {
            p.setItemSlot(slot, stack);
        } else if (!p.getInventory().add(stack)) {
            p.drop(stack, false);
        }
    }

    // =================================================================== steps

    static void enter(ServerPlayer p, PlayerProgress pr, StoryStep step, boolean announceChapter) {
        StoryStep old = pr.step;
        pr.step = step;
        pr.counter = 0;
        pr.eventSpawned = false;
        pr.bossId = null;
        StoryData d = StoryData.get(p.getServer());
        d.setDirty();
        if (announceChapter || old.chapter != step.chapter) {
            String[] parts = step.chapterTitle.split(": ", 2);
            if (parts.length == 2 && step != StoryStep.FREE_ROAM) {
                title(p, Component.literal(parts[0]).withStyle(ChatFormatting.GREEN),
                        Component.literal(parts[1]).withStyle(ChatFormatting.WHITE));
            }
        }
        Dialogue.scene(p, StoryScripts.enter(step));
        setup(p, pr, step, d);
        sendObjective(p);
    }

    public static void complete(ServerPlayer p) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.progress(p.getUUID());
        StoryStep s = pr.step;
        if (s == StoryStep.NOT_STARTED || s == StoryStep.FREE_ROAM) {
            return;
        }
        Dialogue.scene(p, StoryScripts.done(s));
        reward(p, s);
        p.playNotifySound(SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8F, 1.2F);
        enter(p, pr, s.next(), false);
    }

    private static void setup(ServerPlayer p, PlayerProgress pr, StoryStep step, StoryData d) {
        ServerLevel ow = p.getServer().overworld();
        switch (step) {
            case TRAINING -> ensureDummies(ow, d);
            case DEFEAT_KRAANG -> {
                BlockPos ts = d.poi("times_square");
                if (ts != null) {
                    for (int i = 0; i < 4; i++) spawnWaveDroid(ow, ts, p);
                    pr.eventSpawned = true;
                }
            }
            case BOSS -> spawnKraangPrime(p, pr, d);
            case FREE_ROAM -> {
                celebrate(p);
                pr.nextEventTick = ow.getGameTime() + 20L * 60;
            }
            default -> { }
        }
    }

    private static void reward(ServerPlayer p, StoryStep s) {
        switch (s) {
            case TRAINING -> p.giveExperiencePoints(15);
            case DONNIE_LAB -> give(p, new ItemStack(ModItems.T_PHONE.get()));
            case MEET_APRIL -> give(p, new ItemStack(ModItems.PIZZA_SLICE.get(), 4));
            case DEFEAT_KRAANG -> p.giveExperiencePoints(30);
            case MUTANT_LOOSE -> give(p, new ItemStack(ModItems.SMOKE_BOMB.get(), 4));
            case RETURN_LAB -> give(p, new ItemStack(ModItems.RETRO_MUTAGEN.get(), 3));
            case BOSS -> p.giveExperiencePoints(100);
            case RETURN_HOME -> {
                give(p, new ItemStack(ModItems.MIKEY_SPECIAL_PIZZA.get(), 3));
                give(p, new ItemStack(ModItems.PIZZA_SLICE.get(), 8));
                title(p, Component.literal("TURTLE POWER!").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD),
                        Component.literal("You beat the story. Now go protect New York!").withStyle(ChatFormatting.YELLOW));
            }
            default -> { }
        }
    }

    private static void give(ServerPlayer p, ItemStack stack) {
        if (!p.getInventory().add(stack)) {
            p.drop(stack, false);
        }
    }

    // =================================================================== per-player checks

    private static void tickPlayer(ServerPlayer p, StoryData d, long tick) {
        PlayerProgress pr = d.players.get(p.getUUID());
        if (pr == null || pr.step == StoryStep.NOT_STARTED || !p.isAlive()) {
            return;
        }
        hothead(p);
        if (p.level().dimension() != Level.OVERWORLD) {
            return;
        }
        ServerLevel level = p.serverLevel();
        switch (pr.step) {
            case GET_SAIS -> {
                if (p.getInventory().contains(new ItemStack(ModItems.SAI.get()))) complete(p);
            }
            case DONNIE_LAB, RETURN_LAB -> {
                if (near(p, d, "lab", 6)) complete(p);
            }
            case EXIT_SEWER -> {
                if (p.getY() >= d.y0 + 0.5 && inCity(p, d)) complete(p);
            }
            case ROOFTOPS -> {
                if (p.getY() >= d.y0 + 13 && inCity(p, d)) complete(p);
            }
            case MEET_APRIL -> {
                if (near(p, d, "april", 2.5)) complete(p);
            }
            case PORTAL -> {
                portalEffects(level, d);
                if (near(p, d, "times_square", 18)) complete(p);
            }
            case DEFEAT_KRAANG -> {
                portalEffects(level, d);
                manageWave(level, p, pr, d);
            }
            case COLLECT_MUTAGEN -> {
                int have = count(p, ModItems.MUTAGEN_CANISTER.get());
                int shown = Math.min(have, pr.step.goal);
                if (shown != pr.counter) {
                    pr.counter = shown;
                    d.setDirty();
                    sendObjective(p);
                }
                if (have >= pr.step.goal) complete(p);
            }
            case MUTANT_LOOSE -> {
                if (near(p, d, "park", 30)) {
                    Entity boss = pr.bossId == null ? null : level.getEntity(pr.bossId);
                    if (boss == null || !boss.isAlive()) {
                        spawnSpiderBytez(p, pr, d);
                    }
                }
            }
            case INFILTRATE_TCRI -> {
                BlockPos boss = d.poi("tcri_boss");
                if (boss != null && p.blockPosition().distSqr(boss) < 12 * 12 && p.getY() < d.y0 + 9) complete(p);
            }
            case BOSS -> {
                BlockPos bp = d.poi("tcri_boss");
                if (bp != null && p.blockPosition().distSqr(bp) < 30 * 30 && tick % 100 == 0) {
                    Entity boss = pr.bossId == null ? null : level.getEntity(pr.bossId);
                    if (boss == null || !boss.isAlive()) {
                        spawnKraangPrime(p, pr, d);
                    }
                }
            }
            case RETURN_HOME -> {
                if (near(p, d, "lair_hall", 14)) complete(p);
            }
            default -> { }
        }
        CityEvents.tick(p, pr, d);
    }

    /** Raph's set bonus: mask + shell. */
    private static void hothead(ServerPlayer p) {
        if (!p.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.RAPH_MASK.get())
                || !p.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.TURTLE_SHELL.get())) {
            return;
        }
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 60, 0, true, false, true));
        if (p.getHealth() < p.getMaxHealth() * 0.4F) {
            p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 60, 1, true, false, true));
        }
        if (p.isInWater()) {
            p.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 60, 0, true, false, true));
        }
    }

    static boolean near(ServerPlayer p, StoryData d, String poi, double radius) {
        BlockPos pos = d.poi(poi);
        return pos != null && p.position().distanceToSqr(Vec3.atBottomCenterOf(pos)) <= radius * radius;
    }

    static boolean inCity(Player p, StoryData d) {
        return Math.abs(p.getX() - d.origin.getX()) <= Layout.EDGE && Math.abs(p.getZ() - d.origin.getZ()) <= Layout.EDGE;
    }

    private static int count(Player p, Item item) {
        int n = 0;
        for (ItemStack s : p.getInventory().items) if (s.is(item)) n += s.getCount();
        for (ItemStack s : p.getInventory().offhand) if (s.is(item)) n += s.getCount();
        return n;
    }

    // =================================================================== story fights

    private static void portalEffects(ServerLevel level, StoryData d) {
        BlockPos ts = d.poi("times_square");
        if (ts == null) return;
        double x = ts.getX() + 0.5, y = ts.getY(), z = ts.getZ() + 0.5;
        level.sendParticles(ParticleTypes.PORTAL, x, y + 1.5, z, 60, 1.2, 1.5, 1.2, 0.4);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, x, y + 2, z, 20, 0.6, 1.5, 0.6, 0.02);
        level.sendParticles(KraangDroidEntity.PINK, x, y + 0.2, z, 20, 2.5, 0.1, 2.5, 0.0);
        if (level.random.nextInt(4) == 0) {
            level.playSound(null, ts, SoundEvents.PORTAL_AMBIENT, SoundSource.HOSTILE, 0.6F, 1.4F);
        }
    }

    private static void spawnWaveDroid(ServerLevel level, BlockPos centre, ServerPlayer target) {
        KraangDroidEntity droid = ModEntities.KRAANG_DROID.get().create(level);
        if (droid == null) return;
        double ang = level.random.nextDouble() * Math.PI * 2;
        double r = 1 + level.random.nextDouble() * 2;
        droid.moveTo(centre.getX() + 0.5 + Math.cos(ang) * r, centre.getY(), centre.getZ() + 0.5 + Math.sin(ang) * r,
                level.random.nextFloat() * 360, 0);
        droid.finalizeSpawn(level, level.getCurrentDifficultyAt(centre), MobSpawnType.EVENT, null, null);
        droid.getPersistentData().putBoolean(WAVE_TAG, true);
        droid.setPersistenceRequired();
        droid.setTarget(target);
        level.addFreshEntity(droid);
        level.sendParticles(ParticleTypes.PORTAL, droid.getX(), droid.getY() + 1, droid.getZ(), 40, 0.4, 1, 0.4, 0.6);
        level.playSound(null, droid.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 0.8F, 1.6F);
    }

    private static void manageWave(ServerLevel level, ServerPlayer p, PlayerProgress pr, StoryData d) {
        BlockPos ts = d.poi("times_square");
        if (ts == null || p.blockPosition().distSqr(ts) > 56 * 56) return;
        List<KraangDroidEntity> alive = level.getEntitiesOfClass(KraangDroidEntity.class, new AABB(ts).inflate(56),
                e -> e.isAlive() && e.getPersistentData().getBoolean(WAVE_TAG));
        int stillNeeded = pr.step.goal - pr.counter;
        if (alive.size() < Math.min(3, stillNeeded) && level.random.nextInt(3) == 0) {
            spawnWaveDroid(level, ts, p);
        }
    }

    private static void spawnSpiderBytez(ServerPlayer p, PlayerProgress pr, StoryData d) {
        ServerLevel level = p.serverLevel();
        BlockPos park = d.poi("park");
        if (park == null) return;
        Spider spider = EntityType.SPIDER.create(level);
        if (spider == null) return;
        spider.moveTo(park.getX() + 0.5, park.getY(), park.getZ() + 0.5, 0, 0);
        spider.finalizeSpawn(level, level.getCurrentDifficultyAt(park), MobSpawnType.EVENT, null, null);
        spider.getAttribute(Attributes.MAX_HEALTH).setBaseValue(40.0);
        spider.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(4.0);
        Mutation.applyBuffs(spider, "Spider Bytez");
        spider.getPersistentData().putBoolean(BOSS_TAG, true);
        spider.setTarget(p);
        level.addFreshEntity(spider);
        level.sendParticles(ParticleTypes.SNEEZE, spider.getX(), spider.getY() + 1, spider.getZ(), 60, 1, 1, 1, 0.05);
        pr.bossId = spider.getUUID();
        pr.eventSpawned = true;
        StoryData.get(p.getServer()).setDirty();
        trackBossBar(spider, BossEvent.BossBarColor.GREEN);
        Dialogue.scene(p, StoryScripts.SPIDER_BYTEZ_APPEARS);
    }

    private static void spawnKraangPrime(ServerPlayer p, PlayerProgress pr, StoryData d) {
        ServerLevel level = p.server.overworld();
        BlockPos at = d.poi("tcri_portal");
        if (at == null) return;
        KraangPrimeEntity boss = ModEntities.KRAANG_PRIME.get().create(level);
        if (boss == null) return;
        boss.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, 0, 0);
        boss.finalizeSpawn(level, level.getCurrentDifficultyAt(at), MobSpawnType.EVENT, null, null);
        boss.setTarget(p);
        level.addFreshEntity(boss);
        level.sendParticles(ParticleTypes.PORTAL, boss.getX(), boss.getY() + 2, boss.getZ(), 120, 1.2, 2, 1.2, 0.8);
        level.playSound(null, at, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 0.6F, 1.5F);
        for (int i = 0; i < 2; i++) spawnWaveDroid(level, at.offset(i * 4 - 2, 0, 3), p);
        pr.bossId = boss.getUUID();
        pr.eventSpawned = true;
        d.setDirty();
    }

    private static void celebrate(ServerPlayer p) {
        ServerLevel level = p.serverLevel();
        for (int i = 0; i < 5; i++) {
            ItemStack rocket = new ItemStack(Items.FIREWORK_ROCKET);
            net.minecraft.nbt.CompoundTag fw = rocket.getOrCreateTagElement("Fireworks");
            net.minecraft.nbt.ListTag explosions = new net.minecraft.nbt.ListTag();
            net.minecraft.nbt.CompoundTag ex = new net.minecraft.nbt.CompoundTag();
            ex.putByte("Type", (byte) (i % 2 == 0 ? 1 : 4));
            ex.putIntArray("Colors", new int[]{0x3E8E3A, 0x1F4FD8, 0x7B2FBF, 0xF08A1C, 0xD01A1A});
            explosions.add(ex);
            fw.put("Explosions", explosions);
            fw.putByte("Flight", (byte) 1);
            FireworkRocketEntity e = new FireworkRocketEntity(level, p.getX() + level.random.nextGaussian() * 3,
                    p.getY() + 1, p.getZ() + level.random.nextGaussian() * 3, rocket);
            level.addFreshEntity(e);
        }
    }

    public static void ensureDummies(ServerLevel level, StoryData d) {
        for (BlockPos pos : d.poiList("dummies")) {
            if (!level.isLoaded(pos)) continue;
            List<TrainingDummyEntity> here = level.getEntitiesOfClass(TrainingDummyEntity.class, new AABB(pos).inflate(1.5));
            if (here.isEmpty()) {
                TrainingDummyEntity dummy = ModEntities.TRAINING_DUMMY.get().create(level);
                if (dummy != null) {
                    dummy.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 90F, 0);
                    dummy.setYHeadRot(90F);
                    level.addFreshEntity(dummy);
                    level.sendParticles(ParticleTypes.POOF, dummy.getX(), dummy.getY() + 1, dummy.getZ(), 10, 0.3, 0.5, 0.3, 0.01);
                }
            }
        }
    }

    // =================================================================== boss bars for story mutants

    private static void trackBossBar(LivingEntity e, BossEvent.BossBarColor color) {
        ServerBossEvent bar = new ServerBossEvent(e.getDisplayName(), color, BossEvent.BossBarOverlay.NOTCHED_6);
        BOSS_BARS.put(e.getUUID(), bar);
    }

    private static void tickBossBars(MinecraftServer server) {
        ServerLevel level = server.overworld();
        BOSS_BARS.entrySet().removeIf(entry -> {
            Entity e = level.getEntity(entry.getKey());
            ServerBossEvent bar = entry.getValue();
            if (!(e instanceof LivingEntity le) || !le.isAlive()) {
                bar.removeAllPlayers();
                return true;
            }
            bar.setProgress(le.getHealth() / le.getMaxHealth());
            for (ServerPlayer p : level.players()) {
                boolean close = p.distanceToSqr(le) < 48 * 48;
                if (close && !bar.getPlayers().contains(p)) bar.addPlayer(p);
                if (!close && bar.getPlayers().contains(p)) bar.removePlayer(p);
            }
            return false;
        });
    }

    // =================================================================== brothers

    /** Make sure Leo, Donnie and Mikey are with this player; spawn fresh ones if they got lost. */
    static void maintainBrothers(ServerPlayer p, PlayerProgress pr, StoryData d) {
        if (!p.isAlive() || p.isSpectator() || activeJob != null) return;
        ServerLevel level = p.serverLevel();
        for (Brother b : Brother.values()) {
            UUID id = pr.brothers.get(b);
            Entity e = id == null ? null : level.getEntity(id);
            if (e instanceof TurtleBrotherEntity t && t.isAlive()) {
                continue;
            }
            TurtleBrotherEntity bro = b.entityType().create(level);
            if (bro == null) continue;
            bro.moveTo(p.getX(), p.getY(), p.getZ(), p.getYRot(), 0);
            bro.setOwner(p);
            bro.equipWeapon();
            pr.brothers.put(b, bro.getUUID());
            level.addFreshEntity(bro);
            bro.teleportToOwner(p, true);
            d.setDirty();
        }
    }

    public static boolean isCurrentBrother(Player owner, TurtleBrotherEntity bro) {
        if (!(owner.level() instanceof ServerLevel sl)) return true;
        StoryData d = StoryData.get(sl.getServer());
        PlayerProgress pr = d.players.get(owner.getUUID());
        if (pr == null) return true;
        UUID cur = pr.brothers.get(bro.brother());
        if (cur == null) {
            pr.brothers.put(bro.brother(), bro.getUUID());
            d.setDirty();
            return true;
        }
        return cur.equals(bro.getUUID());
    }

    /** A spawn-egg brother was adopted: make it the "real" one. */
    public static void adoptBrother(ServerPlayer p, TurtleBrotherEntity bro) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.progress(p.getUUID());
        UUID old = pr.brothers.put(bro.brother(), bro.getUUID());
        if (old != null && !old.equals(bro.getUUID())) {
            Entity e = p.serverLevel().getEntity(old);
            if (e != null) e.discard();
        }
        d.setDirty();
    }

    public static void recallBrothers(ServerPlayer p) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        if (pr == null) return;
        maintainBrothers(p, pr, d);
        for (UUID id : pr.brothers.values()) {
            if (p.serverLevel().getEntity(id) instanceof TurtleBrotherEntity bro) {
                bro.setTarget(null);
                bro.teleportToOwner(p, true);
            }
        }
    }

    // =================================================================== hooks from items/entities

    public static void useTPhone(ServerPlayer p) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        if (pr == null || pr.step == StoryStep.NOT_STARTED) {
            Dialogue.say(p, Speaker.DONNIE, d.built ? "No mission yet. Type /tmnt start to begin the story!"
                    : "No signal down here. Type /tmnt start to build New York and begin the story!");
            return;
        }
        String prog = pr.step.goal > 0 ? " (" + pr.counter + "/" + pr.step.goal + ")" : "";
        Dialogue.say(p, Speaker.DONNIE, "T-Phone says: " + pr.step.objective + prog + ". Calling the guys over!");
        recallBrothers(p);
        sendObjective(p);
    }

    public static void brotherHint(ServerPlayer p, TurtleBrotherEntity bro) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        Brother b = bro.brother();
        if (pr == null || pr.step == StoryStep.NOT_STARTED || pr.step == StoryStep.FREE_ROAM) {
            Dialogue.say(p, b.speaker, b.chatter[p.getRandom().nextInt(b.chatter.length)], Dialogue.Kind.CHATTER);
            return;
        }
        String hint = switch (b) {
            case LEO -> "Stay focused, Raph. Our mission: ";
            case DONNIE -> "According to my calculations, we should: ";
            case MIKEY -> "Dude, I totally remember the plan! It's... ";
        };
        Dialogue.say(p, b.speaker, hint + pr.step.objective.toLowerCase() + ".");
    }

    public static void talkToNpc(ServerPlayer p, StoryNpcEntity npc) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        StoryStep step = pr == null ? StoryStep.NOT_STARTED : pr.step;
        if (npc.isSplinter()) {
            switch (step) {
                case GET_SAIS -> Dialogue.say(p, Speaker.SPLINTER, "Your sais wait on the weapon rack by the west wall, Raphael. The chest.");
                case TRAINING -> Dialogue.say(p, Speaker.SPLINTER, "The dummies will not hit back. Strike them until they fall. There are three.");
                default -> Dialogue.say(p, Speaker.SPLINTER, StoryScripts.SPLINTER_WISDOM[p.getRandom().nextInt(StoryScripts.SPLINTER_WISDOM.length)]);
            }
        } else {
            if (step == StoryStep.MEET_APRIL) {
                complete(p);
            } else {
                Dialogue.say(p, Speaker.APRIL, StoryScripts.APRIL_CHATTER[p.getRandom().nextInt(StoryScripts.APRIL_CHATTER.length)]);
            }
        }
    }

    public static void onDummyDestroyed(ServerPlayer p) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        if (pr == null || pr.step != StoryStep.TRAINING) return;
        pr.counter++;
        d.setDirty();
        if (pr.counter == 1) Dialogue.say(p, Speaker.MIKEY, "Whoa! That dummy never saw it coming!", Dialogue.Kind.COMBAT);
        sendObjective(p);
        if (pr.counter >= pr.step.goal) complete(p);
    }

    public static void sendObjective(ServerPlayer p) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        ObjectivePacket msg;
        if (pr == null || pr.step == StoryStep.NOT_STARTED) {
            msg = new ObjectivePacket("", "", "", null);
        } else {
            String progress = pr.step.goal > 0 ? pr.counter + "/" + pr.step.goal : "";
            msg = new ObjectivePacket(pr.step.chapterTitle, pr.step.objective, progress, targetFor(p, pr, d));
        }
        ModNetwork.CHANNEL.send(PacketDistributor.PLAYER.with(() -> p), msg);
    }

    @Nullable
    private static BlockPos targetFor(ServerPlayer p, PlayerProgress pr, StoryData d) {
        if (pr.step.target == null) return null;
        if (pr.step.target.equals("kraang_crate")) {
            BlockPos best = null;
            for (BlockPos c : d.poiList("kraang_crates")) {
                if (best == null || c.distSqr(p.blockPosition()) < best.distSqr(p.blockPosition())) best = c;
            }
            return best;
        }
        return d.poi(pr.step.target);
    }

    static void title(ServerPlayer p, Component title, Component subtitle) {
        p.connection.send(new ClientboundSetTitlesAnimationPacket(10, 70, 20));
        p.connection.send(new ClientboundSetTitleTextPacket(title));
        p.connection.send(new ClientboundSetSubtitleTextPacket(subtitle));
    }

    // =================================================================== Forge events

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        MinecraftServer server = event.getServer();
        if (activeJob != null) {
            activeJob.tick();
            if (activeJob.isDone()) activeJob = null;
            return;
        }
        long tick = server.getTickCount();
        StoryData d = StoryData.get(server);
        if (!d.built) return;
        if (tick % 10 == 0) {
            for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                tickPlayer(p, d, tick);
            }
        }
        if (tick % 40 == 5) {
            for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                PlayerProgress pr = d.players.get(p.getUUID());
                if (pr != null && pr.step != StoryStep.NOT_STARTED) maintainBrothers(p, pr, d);
            }
        }
        if (tick % 20 == 0) tickBossBars(server);
        if (tick % 1200 == 0) {
            BlockPos dojo = d.poi("dojo");
            if (dojo != null && !server.overworld().getEntitiesOfClass(Player.class, new AABB(dojo).inflate(40)).isEmpty()) {
                ensureDummies(server.overworld(), d);
            }
        }
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer p)) return;
        MinecraftServer server = p.getServer();
        StoryData d = StoryData.get(server);
        if (d.built) {
            PlayerProgress pr = d.progress(p.getUUID());
            if (pr.step == StoryStep.NOT_STARTED) {
                startStory(p);
            } else {
                sendObjective(p);
                p.refreshDisplayName();
                Dialogue.say(p, Speaker.MIKEY, "Raph's back! Booyakasha!", Dialogue.Kind.CHATTER);
            }
            return;
        }
        if (activeJob != null) return;
        ServerLevel ow = server.overworld();
        if (isTmntWorld(ow)) {
            BlockPos spawn = ow.getSharedSpawnPos();
            beginBuild(ow, spawn.getX(), spawn.getZ(), p, true);
        } else if (Config.OFFER_STORY_IN_NORMAL_WORLDS.get() && !d.offered.contains(p.getUUID())) {
            d.offered.add(p.getUUID());
            d.setDirty();
            offerStory(p);
        }
    }

    public static void offerStory(ServerPlayer p) {
        Component button = Component.literal("[ START TMNT STORY MODE ]").withStyle(s -> s
                .withColor(ChatFormatting.GREEN).withBold(true)
                .withClickEvent(new ClickEvent(ClickEvent.Action.RUN_COMMAND, "/tmnt start"))
                .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal(
                        "Builds New York City, the sewers and the lair right where you are standing\n"
                                + "(about 190 x 190 blocks). Best in a brand new world!"))));
        p.sendSystemMessage(Component.literal("TMNT Turtle Power is installed! ").withStyle(ChatFormatting.GREEN).append(button));
        p.sendSystemMessage(Component.literal("(or type /tmnt start later)").withStyle(ChatFormatting.GRAY));
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer p)) return;
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.players.get(p.getUUID());
        if (pr != null) {
            for (UUID id : pr.brothers.values()) {
                Entity e = p.serverLevel().getEntity(id);
                if (e != null) e.discard();
            }
        }
        Dialogue.forget(p.getUUID());
    }

    @SubscribeEvent
    public static void onChangedDimension(PlayerEvent.PlayerChangedDimensionEvent event) {
        if (event.getEntity() instanceof ServerPlayer p) sendObjective(p);
    }

    @SubscribeEvent
    public static void onEat(LivingEntityUseItemEvent.Finish event) {
        if (!(event.getEntity() instanceof ServerPlayer p)) return;
        ItemStack item = event.getItem();
        if (!item.is(ModItems.PIZZA_SLICE.get()) && !item.is(ModItems.MIKEY_SPECIAL_PIZZA.get())) return;
        PlayerProgress pr = StoryData.get(p.getServer()).players.get(p.getUUID());
        if (pr != null && pr.step == StoryStep.EAT_PIZZA) complete(p);
    }

    @SubscribeEvent
    public static void onDeath(LivingDeathEvent event) {
        LivingEntity dead = event.getEntity();
        if (!(dead.level() instanceof ServerLevel level) || dead instanceof Player) return;
        StoryData d = StoryData.get(level.getServer());
        if (!d.built) return;
        for (ServerPlayer p : level.players()) {
            PlayerProgress pr = d.players.get(p.getUUID());
            if (pr == null) continue;
            double dist = p.distanceToSqr(dead);
            if (dead instanceof KraangPrimeEntity) {
                if (pr.step == StoryStep.BOSS && dist < 64 * 64) complete(p);
            } else if (dead instanceof KraangDroidEntity) {
                if (pr.step == StoryStep.DEFEAT_KRAANG && dist < 48 * 48) {
                    pr.counter++;
                    d.setDirty();
                    sendObjective(p);
                    if (pr.counter >= pr.step.goal) complete(p);
                }
            } else if (dead.getPersistentData().getBoolean(BOSS_TAG)) {
                if (pr.step == StoryStep.MUTANT_LOOSE && dist < 64 * 64) complete(p);
            }
        }
    }

    @SubscribeEvent
    public static void onDrops(LivingDropsEvent event) {
        LivingEntity dead = event.getEntity();
        if (!(dead instanceof KraangDroidEntity) || dead instanceof KraangPrimeEntity || !(dead.level() instanceof ServerLevel level)) return;
        StoryData d = StoryData.get(level.getServer());
        boolean storyNeedsMutagen = false;
        for (ServerPlayer p : level.players()) {
            PlayerProgress pr = d.players.get(p.getUUID());
            if (pr != null && pr.step == StoryStep.COLLECT_MUTAGEN && p.distanceToSqr(dead) < 48 * 48) {
                storyNeedsMutagen = true;
            }
        }
        if (!storyNeedsMutagen) return;
        boolean has = event.getDrops().stream().anyMatch(ie -> ie.getItem().is(ModItems.MUTAGEN_CANISTER.get()));
        if (!has) {
            event.getDrops().add(new ItemEntity(level, dead.getX(), dead.getY() + 0.5, dead.getZ(),
                    new ItemStack(ModItems.MUTAGEN_CANISTER.get())));
        }
    }

    @SubscribeEvent
    public static void onNameFormat(PlayerEvent.NameFormat event) {
        if (!(event.getEntity() instanceof ServerPlayer p) || p.getServer() == null) return;
        PlayerProgress pr = StoryData.get(p.getServer()).players.get(p.getUUID());
        if (pr != null && pr.step != StoryStep.NOT_STARTED) {
            boolean alone = p.getServer().getPlayerCount() <= 1;
            event.setDisplayname(Component.literal(alone ? "Raphael" : "Raphael (" + event.getUsername().getString() + ")")
                    .withStyle(ChatFormatting.RED));
        }
    }

    @SubscribeEvent
    public static void onCommands(RegisterCommandsEvent event) {
        com.echoesinthedark.turtlepower.command.TmntCommand.register(event.getDispatcher());
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        // Worlds made with the "TMNT New York" world type build the city straight away.
        ServerLevel ow = event.getServer().overworld();
        StoryData d = StoryData.get(event.getServer());
        if (!d.built && activeJob == null && isTmntWorld(ow)) {
            BlockPos spawn = ow.getSharedSpawnPos();
            beginBuild(ow, spawn.getX(), spawn.getZ(), null, true);
        }
    }

    @SubscribeEvent
    public static void onServerStopped(ServerStoppedEvent event) {
        activeJob = null;
        START_AFTER_BUILD.clear();
        startEveryoneAfterBuild = false;
        BOSS_BARS.values().forEach(ServerBossEvent::removeAllPlayers);
        BOSS_BARS.clear();
    }

    // =================================================================== commands support

    public static void jumpTo(ServerPlayer p, StoryStep step) {
        StoryData d = StoryData.get(p.getServer());
        PlayerProgress pr = d.progress(p.getUUID());
        if (step == StoryStep.NOT_STARTED) {
            pr.step = StoryStep.NOT_STARTED;
            d.setDirty();
            sendObjective(p);
            return;
        }
        enter(p, pr, step, true);
        maintainBrothers(p, pr, d);
        if (step.atLeast(StoryStep.EXIT_SEWER)) give(p, new ItemStack(ModItems.T_PHONE.get()));
        if (step.atLeast(StoryStep.TRAINING) && !p.getInventory().contains(new ItemStack(ModItems.SAI.get()))) {
            give(p, new ItemStack(ModItems.SAI.get()));
        }
    }

    public static void goHome(ServerPlayer p) {
        StoryData d = StoryData.get(p.getServer());
        BlockPos home = d.poi("raph_room");
        if (home != null) {
            p.teleportTo(p.getServer().overworld(), home.getX() + 0.5, home.getY(), home.getZ() + 0.5, 180F, 0F);
            recallBrothers(p);
        }
    }
}
