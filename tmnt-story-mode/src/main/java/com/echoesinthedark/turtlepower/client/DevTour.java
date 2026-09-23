package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.entity.KraangDroidEntity;
import com.echoesinthedark.turtlepower.entity.TrainingDummyEntity;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.CityEvents;
import com.echoesinthedark.turtlepower.story.StoryData;
import com.echoesinthedark.turtlepower.story.StoryManager;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.ForgeEventFactory;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * Developer tool only. Start the game with -Dturtlepower.devtour=tour to fly the camera around a
 * finished story world and save screenshots, or -Dturtlepower.devtour=story to play the whole story
 * automatically (teleporting and knocking out enemies) and log every step, so the story can be
 * checked from start to finish without playing it by hand. Does nothing in normal play.
 */
@Mod.EventBusSubscriber(modid = TurtlePower.MODID, value = Dist.CLIENT)
public final class DevTour {
    private DevTour() {}

    private static final String MODE = System.getProperty("turtlepower.devtour", "");

    /** One scripted beat: do something on the server, wait, maybe take a screenshot. */
    private record Beat(String name, int ticks, boolean shot, boolean hud, Consumer<ServerPlayer> action) {}

    private static final List<Beat> BEATS = new ArrayList<>();
    private static int index = -1;
    private static int wait = 0;
    private static int startDelay = 400;

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (MODE.isEmpty() || event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        MinecraftServer server = mc.getSingleplayerServer();
        if (mc.player == null || server == null || mc.level == null) return;
        if (startDelay > 0) {
            startDelay--;
            if (startDelay == 200) shot(mc, "00_start");
            return;
        }
        if (BEATS.isEmpty()) {
            if (MODE.equals("story")) planStory(); else planTour();
        }
        if (wait > 0) {
            wait--;
            if (wait == 0) {
                Beat b = BEATS.get(index);
                if (b.shot) shot(mc, String.format("%02d_%s", index + 1, b.name));
                server.execute(() -> log(server, b.name));
            }
            return;
        }
        index++;
        if (index >= BEATS.size()) {
            TurtlePower.LOGGER.info("DEVTOUR DONE");
            mc.stop();
            return;
        }
        Beat b = BEATS.get(index);
        server.execute(() -> {
            ServerPlayer sp = server.getPlayerList().getPlayers().get(0);
            try {
                b.action.accept(sp);
            } catch (Exception e) {
                TurtlePower.LOGGER.error("DEVTOUR beat {} failed", b.name, e);
            }
        });
        mc.options.hideGui = !b.hud;
        wait = Math.max(1, b.ticks);
    }

    private static void shot(Minecraft mc, String name) {
        Screenshot.grab(mc.gameDirectory, (MODE.equals("story") ? "story_" : "tour_") + name + ".png", mc.getMainRenderTarget(), m -> { });
    }

    private static void log(MinecraftServer server, String beat) {
        ServerPlayer sp = server.getPlayerList().getPlayers().get(0);
        StoryData.PlayerProgress pr = StoryData.get(server).progress(sp.getUUID());
        int brothers = server.overworld().getEntitiesOfClass(com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity.class,
                sp.getBoundingBox().inflate(24)).size();
        TurtlePower.LOGGER.info("STORYTEST {} -> step={} counter={} brothersNearby={} hp={}", beat, pr.step, pr.counter, brothers, sp.getHealth());
    }

    // ------------------------------------------------------------------ helpers

    private static Consumer<ServerPlayer> tp(String poi, double dx, double dy, double dz, float yaw, float pitch) {
        return sp -> {
            BlockPos p = StoryData.get(sp.getServer()).poi(poi);
            if (p == null) {
                TurtlePower.LOGGER.warn("DEVTOUR missing poi {}", poi);
                return;
            }
            sp.teleportTo(sp.getServer().overworld(), p.getX() + 0.5 + dx, p.getY() + dy, p.getZ() + 0.5 + dz, yaw, pitch);
        };
    }

    private static Consumer<ServerPlayer> fly(String poi, double dx, double dy, double dz, float yaw, float pitch) {
        Consumer<ServerPlayer> t = tp(poi, dx, dy, dz, yaw, pitch);
        return sp -> {
            sp.getAbilities().mayfly = true;
            sp.getAbilities().flying = true;
            sp.onUpdateAbilities();
            t.accept(sp);
        };
    }

    private static void killAll(ServerPlayer sp, Class<? extends LivingEntity> type, double radius, java.util.function.Predicate<LivingEntity> filter) {
        for (LivingEntity e : sp.serverLevel().getEntitiesOfClass(type, sp.getBoundingBox().inflate(radius), filter)) {
            e.invulnerableTime = 0;
            e.hurt(sp.damageSources().playerAttack(sp), 2000F);
        }
    }

    private static void spawn(ServerPlayer sp, EntityType<? extends Mob> type, String poi, double dx, double dz) {
        ServerLevel level = sp.serverLevel();
        BlockPos p = StoryData.get(sp.getServer()).poi(poi);
        Mob m = type.create(level);
        if (m == null || p == null) return;
        m.moveTo(p.getX() + 0.5 + dx, p.getY(), p.getZ() + 0.5 + dz, 0, 0);
        m.finalizeSpawn(level, level.getCurrentDifficultyAt(p), MobSpawnType.COMMAND, null, null);
        m.setNoAi(true);
        m.setYRot(0);
        m.setYHeadRot(0);
        level.addFreshEntity(m);
    }

    private static void beat(String name, int wait, boolean shot, Consumer<ServerPlayer> action) {
        BEATS.add(new Beat(name, wait, shot, false, action));
    }

    private static void hudBeat(String name, int wait, Consumer<ServerPlayer> action) {
        BEATS.add(new Beat(name, wait, true, true, action));
    }

    // ------------------------------------------------------------------ the camera tour

    private static void planTour() {
        hudBeat("hud_raph_room", 120, tp("raph_room", 0, 0, 0, 0, 10));
        beat("pit_tvs", 120, true, fly("lair_hall", 0, 3, 16, 180, 15));
        beat("hall_overview", 120, true, fly("lair_hall", 12, 9, -9, 45, 30));
        beat("dojo", 120, true, fly("dojo", 5, 3, -8, 50, 12));
        beat("lab", 120, true, fly("lab", -4, 2, 8, 210, 15));
        beat("kitchen", 120, true, fly("kitchen", -3, 2, -4, -45, 25));
        beat("garage", 120, true, fly("lair_entrance", -24, 3, 1, 60, 15));
        beat("stairs", 120, true, fly("lair_exit", 0, 0, 1, 0, 30));
        beat("sewer", 120, true, fly("sewer_exit_ladder", -12, 0, 0, -90, 5));
        beat("manhole_street", 120, true, fly("main_manhole", -3, 1, 6, 200, 30));
        beat("times_square", 120, true, fly("times_square", 0, 12, 18, 180, 25));
        beat("antonios", 120, true, fly("antonios", 0, 3, 8, 180, -15));
        beat("tcri", 160, true, fly("tcri_door", 22, 40, 30, 145, 15));
        beat("tcri_lab", 120, true, fly("tcri_boss", 0, 3, 8, 180, 10));
        beat("park", 120, true, fly("park", -10, 12, -10, -45, 35));
        beat("city_aerial", 160, true, fly("times_square", -60, 70, -60, -45, 30));
        beat("characters", 120, true, fly("times_square", 0, 0, 5, 180, 0).andThen(sp -> {
            spawn(sp, ModEntities.LEONARDO.get(), "times_square", -3, 0);
            spawn(sp, ModEntities.DONATELLO.get(), "times_square", -1.5, 0);
            spawn(sp, ModEntities.MICHELANGELO.get(), "times_square", 0, 0);
            spawn(sp, ModEntities.SPLINTER.get(), "times_square", 1.5, 0);
            spawn(sp, ModEntities.APRIL.get(), "times_square", 3, 0);
        }));
        beat("enemies", 120, true, fly("park", 0, 0, 7, 180, -5).andThen(sp -> {
            StoryManager.recallBrothers(sp);
            spawn(sp, ModEntities.KRAANG_DROID.get(), "park", -3, 0);
            spawn(sp, ModEntities.KRAANG_PRIME.get(), "park", 0, -1);
            spawn(sp, ModEntities.FOOT_NINJA.get(), "park", 3, 0);
            spawn(sp, ModEntities.TRAINING_DUMMY.get(), "park", 5, 0);
        }));
        beat("backs", 120, true, fly("times_square", 0, 1, -5, 0, 10));
    }

    // ------------------------------------------------------------------ the automatic story playthrough

    private static void planStory() {
        hudBeat("wake_up", 100, sp -> sp.addEffect(new net.minecraft.world.effect.MobEffectInstance(
                net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE, 20 * 900, 4, false, false)));
        hudBeat("get_sais", 80, sp -> sp.getInventory().add(new ItemStack(ModItems.SAI.get())));
        hudBeat("training", 100, tp("dojo", 0, 0, 0, 90, 0).andThen(sp ->
                killAll(sp, TrainingDummyEntity.class, 20, e -> true)));
        hudBeat("eat_pizza", 80, tp("kitchen", 0, 0, 0, 0, 0).andThen(sp ->
                ForgeEventFactory.onItemUseFinish(sp, new ItemStack(ModItems.PIZZA_SLICE.get()), 0, ItemStack.EMPTY)));
        hudBeat("donnie_lab", 120, tp("lab", 0, 0, 0, 180, 0));
        hudBeat("climb_ladder", 60, tp("sewer_exit_ladder", 0, 3, 1, 180, -60));
        hudBeat("topside", 120, tp("main_manhole", 0, 1, 0, 180, 0));
        hudBeat("rooftops", 120, tp("fire_escape_main", 0, 21, -3, 0, 20));
        hudBeat("meet_april", 160, tp("april", 0, 0, 1.5, 180, 0));
        hudBeat("times_square", 120, tp("times_square", 0, 0, -9, 0, 0));
        hudBeat("kraang_fight", 160, sp -> { });
        for (int i = 0; i < 5; i++) {
            beat("defeat_wave_" + i, 80, false, sp -> killAll(sp, KraangDroidEntity.class, 60,
                    e -> e.getPersistentData().getBoolean(StoryManager.WAVE_TAG)));
        }
        hudBeat("collect_mutagen", 100, sp -> sp.getInventory().add(new ItemStack(ModItems.MUTAGEN_CANISTER.get(), 5)));
        hudBeat("spider_bytez", 160, tp("park", 0, 0, -8, 0, 10));
        beat("defeat_spider", 80, false, sp -> killAll(sp, LivingEntity.class, 40,
                e -> e.getPersistentData().getBoolean(StoryManager.BOSS_TAG)));
        hudBeat("retro_mutagen", 120, tp("lab", 0, 0, 0, 180, 0));
        hudBeat("tcri", 160, tp("tcri_boss", 0, 0, 6, 180, 0));
        hudBeat("kraang_prime", 160, sp -> { });
        beat("defeat_prime", 100, false, sp -> killAll(sp, com.echoesinthedark.turtlepower.entity.KraangPrimeEntity.class, 40, e -> true));
        hudBeat("home", 200, tp("lair_hall", 0, 0, 0, 180, 0));
        beat("lair_monsters", 20, false, sp -> {
            int n = sp.serverLevel().getEntitiesOfClass(net.minecraft.world.entity.monster.Monster.class,
                    sp.getBoundingBox().inflate(40, 12, 40)).size();
            TurtlePower.LOGGER.info("STORYTEST monsters inside the lair: {}", n);
        });
        for (CityEvents.Type t : CityEvents.Type.values()) {
            hudBeat("event_" + t.name().toLowerCase(), 120, tp("times_square", 0, 0, -14, 0, 20).andThen(sp ->
                    CityEvents.trigger(sp, StoryData.get(sp.getServer()), t)));
        }
        hudBeat("t_phone", 100, sp -> StoryManager.useTPhone(sp));
        beat("mutate_pig", 100, true, tp("times_square", 0, 0, -14, 0, 20).andThen(sp -> {
            Mob pig = EntityType.PIG.create(sp.serverLevel());
            if (pig != null) {
                pig.moveTo(sp.getX(), sp.getY(), sp.getZ() + 3, 180, 0);
                sp.serverLevel().addFreshEntity(pig);
                com.echoesinthedark.turtlepower.entity.Mutation.mutate(sp.serverLevel(), pig, sp);
            }
            for (Entity e : sp.serverLevel().getEntitiesOfClass(Mob.class, sp.getBoundingBox().inflate(6))) {
                TurtlePower.LOGGER.info("STORYTEST nearby mob: {}", e.getName().getString());
            }
        }));
        beat("brothers_defend", 200, true, sp -> {
            // A Kraang droid that targets Raph: the brothers must go after it.
            KraangDroidEntity d = ModEntities.KRAANG_DROID.get().create(sp.serverLevel());
            if (d != null) {
                d.moveTo(sp.getX() + 6, sp.getY(), sp.getZ(), 0, 0);
                sp.serverLevel().addFreshEntity(d);
                d.setTarget(sp);
                TurtlePower.LOGGER.info("STORYTEST defend target spawned {}", d.getUUID());
            }
        });
        beat("check_defend", 20, false, sp -> {
            int alive = sp.serverLevel().getEntitiesOfClass(KraangDroidEntity.class, sp.getBoundingBox().inflate(30), LivingEntity::isAlive).size();
            TurtlePower.LOGGER.info("STORYTEST kraang still alive near raph after brothers defend: {}", alive);
        });
    }
}
