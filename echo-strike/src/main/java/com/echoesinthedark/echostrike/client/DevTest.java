package com.echoesinthedark.echostrike.client;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.entity.OperativeEntity;
import com.echoesinthedark.echostrike.game.ArenaBuilder;
import com.echoesinthedark.echostrike.game.LootCrates;
import com.echoesinthedark.echostrike.game.StrikeGame;
import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.network.ModNetwork;
import com.echoesinthedark.echostrike.network.ReloadPacket;
import com.echoesinthedark.echostrike.network.ShootPacket;
import com.echoesinthedark.echostrike.registry.ModEntities;
import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * Developer tool only. Start the game with -Dechostrike.devtest=true (./gradlew runClient
 * -Pdevtest="World") and it plays a scripted session: builds the arena, shoots every gun at
 * operatives, slides, throws a grenade, runs a wave and a battle royale, takes screenshots,
 * logs "DEVTEST ..." lines so the result can be checked from the log, then quits.
 */
@Mod.EventBusSubscriber(modid = EchoStrike.MODID, value = Dist.CLIENT)
public final class DevTest {
    private DevTest() {}

    private static final String MODE = System.getProperty("echostrike.devtest", "");
    private static final boolean ENABLED = !MODE.isEmpty();

    private record Beat(String name, int ticks, boolean shot, Consumer<ServerPlayer> server, Runnable client) {}

    private static final List<Beat> BEATS = new ArrayList<>();
    private static int index = -1;
    private static int wait;
    private static int startDelay = 200;
    private static int shotsLeft;
    private static int shotEvery;
    private static boolean slideNow;
    private static int slideHold;
    private static int killsBefore;

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!ENABLED || event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        MinecraftServer server = mc.getSingleplayerServer();
        if (mc.player == null && mc.screen instanceof net.minecraft.client.gui.screens.ConfirmScreen confirm) {
            // e.g. "use this world's resource pack?" or the experimental-settings warning: press the
            // first (positive) button so the scripted run can continue.
            for (net.minecraft.client.gui.components.events.GuiEventListener child : confirm.children()) {
                if (child instanceof net.minecraft.client.gui.components.Button button) {
                    EchoStrike.LOGGER.info("DEVTEST pressed '{}' on: {}", button.getMessage().getString(), confirm.getTitle().getString());
                    button.onPress();
                    break;
                }
            }
            return;
        }
        if (mc.player == null || server == null || mc.level == null) return;
        if (startDelay > 0) {
            startDelay--;
            return;
        }
        if (BEATS.isEmpty()) {
            if (MODE.equals("world")) planWorld();
            else if (MODE.equals("guns")) planGuns();
            else plan();
        }

        // continuous actions while a beat runs
        if (shotsLeft > 0 && mc.level.getGameTime() % Math.max(1, shotEvery) == 0) {
            ModNetwork.CHANNEL.sendToServer(new ShootPacket(true));
            shotsLeft--;
        }
        if (slideHold > 0) {
            slideHold--;
            mc.options.keyUp.setDown(true);
            mc.player.setSprinting(true);
            mc.options.keyShift.setDown(slideHold <= 18); // run first, then crouch into the slide
            if (slideHold == 0) {
                mc.options.keyShift.setDown(false);
                mc.options.keyUp.setDown(false);
            }
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
            EchoStrike.LOGGER.info("DEVTEST DONE");
            mc.stop();
            return;
        }
        Beat b = BEATS.get(index);
        if (b.client != null) b.client.run();
        if (b.server != null) {
            server.execute(() -> {
                ServerPlayer sp = server.getPlayerList().getPlayers().get(0);
                try {
                    b.server.accept(sp);
                } catch (Exception e) {
                    EchoStrike.LOGGER.error("DEVTEST beat {} failed", b.name, e);
                }
            });
        }
        wait = Math.max(1, b.ticks);
    }

    private static void shot(Minecraft mc, String name) {
        Screenshot.grab(mc.gameDirectory, "devtest_" + name + ".png", mc.getMainRenderTarget(), m -> { });
    }

    private static void log(MinecraftServer server, String beat) {
        ServerPlayer sp = server.getPlayerList().getPlayers().get(0);
        ServerLevel level = sp.serverLevel();
        int ops = level.getEntitiesOfClass(OperativeEntity.class, sp.getBoundingBox().inflate(80)).size();
        ItemStack held = sp.getMainHandItem();
        String gun = held.getItem() instanceof GunItem g ? g.type.id + " ammo=" + GunItem.getAmmo(held) + " reloading=" + GunItem.isReloading(held, level.getGameTime()) : "none";
        StrikeGame game = StrikeGame.get(server);
        EchoStrike.LOGGER.info("DEVTEST {} -> hp={} gun={} operativesNearby={} kills={} mode={} pos={}",
                beat, sp.getHealth(), gun, ops, game.kills(sp), game.mode(), sp.blockPosition());
    }

    // ------------------------------------------------------------------ helpers

    private static void beat(String name, int ticks, boolean shot, Consumer<ServerPlayer> server) {
        BEATS.add(new Beat(name, ticks, shot, server, null));
    }

    private static void beat(String name, int ticks, boolean shot, Consumer<ServerPlayer> server, Runnable client) {
        BEATS.add(new Beat(name, ticks, shot, server, client));
    }

    private static Consumer<ServerPlayer> look(float yaw, float pitch) {
        return sp -> sp.connection.teleport(sp.getX(), sp.getY(), sp.getZ(), yaw, pitch);
    }

    private static Consumer<ServerPlayer> tp(double dx, double dy, double dz, float yaw, float pitch) {
        return sp -> {
            BlockPos c = StrikeGame.devCenter;
            sp.connection.teleport(c.getX() + 0.5 + dx, c.getY() + dy, c.getZ() + 0.5 + dz, yaw, pitch);
        };
    }

    private static Consumer<ServerPlayer> spawnOps(int count, int tier, double dz) {
        return sp -> {
            ServerLevel level = sp.serverLevel();
            for (int i = 0; i < count; i++) {
                OperativeEntity op = ModEntities.OPERATIVE.get().create(level);
                if (op == null) continue;
                op.moveTo(sp.getX() + (i - (count - 1) / 2.0) * 1.5, sp.getY(), sp.getZ() + dz, 180, 0);
                op.finalizeSpawn(level, level.getCurrentDifficultyAt(op.blockPosition()), MobSpawnType.EVENT, null, null);
                op.setTier(tier);
                op.setNoAi(true);
                level.addFreshEntity(op);
            }
        };
    }

    private static Consumer<ServerPlayer> hold(ItemStack stack) {
        return sp -> {
            sp.getInventory().setItem(0, stack);
            sp.getInventory().selected = 0;
            sp.inventoryMenu.broadcastChanges();
        };
    }

    private static Consumer<ServerPlayer> killOps() {
        return sp -> {
            for (OperativeEntity op : sp.serverLevel().getEntitiesOfClass(OperativeEntity.class, sp.getBoundingBox().inflate(80))) {
                op.discard();
            }
        };
    }

    private static Runnable shoot(int shots, int every) {
        return () -> {
            shotsLeft = shots;
            shotEvery = every;
        };
    }

    // ------------------------------------------------------------------ gun model / animation check

    private static void planGuns() {
        beat("spawn", 40, false, sp -> {
            sp.setGameMode(GameType.SURVIVAL);
            StrikeGame.devCenter = sp.blockPosition();
            ArenaBuilder.build(sp.serverLevel(), StrikeGame.devCenter, sp.getRandom());
            sp.serverLevel().setDayTime(6000);
            tp(0, 0, 22, 180, 0).accept(sp);
            StrikeGame.giveKit(sp, "assault");
        });
        beat("ops", 30, false, spawnOps(1, 2, -6).andThen(s -> {
            for (OperativeEntity op : s.serverLevel().getEntitiesOfClass(OperativeEntity.class, s.getBoundingBox().inflate(40))) {
                op.setAggressive(true);
                // Turn it sideways so the screenshots show the gun's profile in its hands.
                op.moveTo(op.getX() + 2.5, op.getY(), op.getZ(), 90, 0);
                op.setYBodyRot(90);
                op.setYHeadRot(90);
            }
        }));
        for (var entry : new Object[][]{{"ak47", ModItems.AK47}, {"awm", ModItems.AWM}, {"m870", ModItems.M870}, {"g18", ModItems.G18},
                {"mp5", ModItems.MP5}, {"m249", ModItems.M249}, {"deagle", ModItems.DEAGLE}, {"m4a1", ModItems.M4A1}}) {
            String name = (String) entry[0];
            var item = (net.minecraftforge.registries.RegistryObject<net.minecraft.world.item.Item>) entry[1];
            beat(name + "_hip", 25, true, hold(new ItemStack(item.get())).andThen(look(180, 0)), () -> Minecraft.getInstance().options.keyUse.setDown(false));
            beat(name + "_ads", 25, true, sp -> { }, () -> Minecraft.getInstance().options.keyUse.setDown(true));
            beat(name + "_shot", 2, true, sp -> { }, () -> {
                Minecraft.getInstance().options.keyUse.setDown(false);
                ModNetwork.CHANNEL.sendToServer(new ShootPacket(false));
            });
            if (name.equals("ak47") || name.equals("awm")) {
                beat(name + "_reload", 20, true, sp -> { }, () -> ModNetwork.CHANNEL.sendToServer(new ReloadPacket()));
                beat(name + "_sprint", 20, true, tp(-18, 0, 18, -90, 0), () -> {
                    Minecraft.getInstance().options.keyUp.setDown(true);
                    Minecraft.getInstance().player.setSprinting(true);
                });
                beat(name + "_sprint_end", 10, false, tp(0, 0, 22, 180, 0), () -> Minecraft.getInstance().options.keyUp.setDown(false));
            }
        }
        beat("third_person", 30, true, hold(new ItemStack(ModItems.AK47.get())).andThen(look(180, 0)),
                () -> Minecraft.getInstance().options.setCameraType(net.minecraft.client.CameraType.THIRD_PERSON_FRONT));
        beat("third_person_back", 30, true, look(180, 10),
                () -> Minecraft.getInstance().options.setCameraType(net.minecraft.client.CameraType.THIRD_PERSON_BACK));
        beat("first_person_again", 10, false, sp -> { },
                () -> Minecraft.getInstance().options.setCameraType(net.minecraft.client.CameraType.FIRST_PERSON));
        beat("inventory", 30, true, sp -> { }, () -> {
            Minecraft mc = Minecraft.getInstance();
            mc.setScreen(new net.minecraft.client.gui.screens.inventory.InventoryScreen(mc.player));
        });
        beat("end", 10, false, sp -> { }, () -> Minecraft.getInstance().setScreen(null));
    }

    // ------------------------------------------------------------------ the shipped world

    /** Builds the arena at the world spawn, points the spawn at it, and quits so the world saves. */
    private static void planWorld() {
        beat("world_arena", 40, false, sp -> {
            ServerLevel level = sp.serverLevel();
            BlockPos spawn = level.getSharedSpawnPos();
            int y = level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, spawn.getX(), spawn.getZ());
            BlockPos center = new BlockPos(spawn.getX(), y, spawn.getZ());
            StrikeGame.devCenter = center;
            ArenaBuilder.build(level, center, sp.getRandom());
            level.setDefaultSpawnPos(center.offset(0, 0, 18), 180);
            level.setDayTime(1000);
            sp.connection.teleport(center.getX() + 0.5, center.getY(), center.getZ() + 18.5, 180, 0);
        });
        beat("world_view", 40, true, tp(-20, 14, 20, -135, 35));
        beat("world_save", 10, false, sp -> sp.getServer().saveEverything(true, true, true));
    }

    // ------------------------------------------------------------------ the script

    private static void plan() {
        beat("spawn", 40, true, sp -> {
            sp.setGameMode(GameType.SURVIVAL);
            StrikeGame.devCenter = sp.blockPosition();
            sp.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE, 20 * 600, 2, false, false));
        });
        beat("arena", 60, true, sp -> {
            ArenaBuilder.build(sp.serverLevel(), StrikeGame.devCenter, sp.getRandom());
            tp(0, 3, 14, 180, 10).accept(sp);
            sp.serverLevel().setDayTime(6000);
        });
        beat("arena_view", 60, true, tp(-18, 12, 18, -135, 35));
        beat("kit", 40, true, sp -> {
            tp(0, 0, 22, 180, 0).accept(sp);
            StrikeGame.giveKit(sp, "assault");
        });
        beat("targets", 30, true, spawnOps(3, 1, -7));
        beat("ak47_fire", 50, true, hold(new ItemStack(ModItems.AK47.get())).andThen(look(180, 2)), shoot(20, 4));
        beat("ak47_reload", 60, true, sp -> { }, () -> ModNetwork.CHANNEL.sendToServer(new ReloadPacket()));
        beat("m4a1_fire", 40, true, hold(new ItemStack(ModItems.M4A1.get())).andThen(look(180, 2)), shoot(15, 3));
        beat("awm_fire", 50, true, hold(new ItemStack(ModItems.AWM.get())).andThen(look(180, 2)), shoot(3, 32));
        beat("m870_fire", 40, true, hold(new ItemStack(ModItems.M870.get())).andThen(look(180, 2)), shoot(3, 16));
        beat("mp5_fire", 40, true, hold(new ItemStack(ModItems.MP5.get())).andThen(look(180, 2)), shoot(20, 2));
        beat("vector_fire", 40, true, hold(new ItemStack(ModItems.VECTOR.get())).andThen(look(180, 2)), shoot(30, 1));
        beat("ump45_fire", 40, true, hold(new ItemStack(ModItems.UMP45.get())).andThen(look(180, 2)), shoot(12, 3));
        beat("m249_fire", 40, true, hold(new ItemStack(ModItems.M249.get())).andThen(look(180, 2)), shoot(14, 3));
        beat("g18_fire", 40, true, hold(new ItemStack(ModItems.G18.get())).andThen(look(180, 2)), shoot(12, 3));
        beat("deagle_fire", 40, true, hold(new ItemStack(ModItems.DEAGLE.get())).andThen(look(180, 2)), shoot(4, 9));
        beat("grenade", 70, true, hold(new ItemStack(ModItems.FRAG_GRENADE.get(), 4)).andThen(look(180, -20)), () -> {
            Minecraft mc = Minecraft.getInstance();
            mc.gameMode.useItem(mc.player, net.minecraft.world.InteractionHand.MAIN_HAND);
        });
        beat("after_fight", 20, true, sp -> { });
        beat("clear", 10, false, killOps());
        beat("slide", 40, true, hold(new ItemStack(ModItems.AK47.get())).andThen(tp(-20, 0, 18, -90, 15)), () -> slideHold = 32);
        beat("slide_done", 10, true, sp -> { });
        beat("vault_setup", 10, false, sp -> {
            BlockPos c = StrikeGame.devCenter;
            for (int i = -2; i <= 2; i++) {
                sp.serverLevel().setBlock(new BlockPos(c.getX() + 8, c.getY(), c.getZ() + 20 + i), net.minecraft.world.level.block.Blocks.IRON_BLOCK.defaultBlockState(), 3);
            }
            sp.connection.teleport(c.getX() + 4.5, c.getY() + 1, c.getZ() + 20.5, -90, 10);
        });
        beat("vault", 30, true, sp -> { }, () -> {
            slideHold = 0;
            Minecraft.getInstance().options.keyUp.setDown(true);
        });
        beat("vault_done", 10, true, sp -> { }, () -> Minecraft.getInstance().options.keyUp.setDown(false));
        beat("ai_fight", 100, true, sp -> {
            tp(0, 0, 22, 180, 0).accept(sp);
            spawnOps(2, 2, -9).andThen(s -> {
                for (OperativeEntity op : s.serverLevel().getEntitiesOfClass(OperativeEntity.class, s.getBoundingBox().inflate(40))) {
                    op.setNoAi(false);
                    op.setTarget(s);
                }
            }).accept(sp);
        });
        beat("ai_fight_2", 60, true, sp -> { });
        beat("clear2", 10, false, killOps());
        beat("crate", 40, true, sp -> {
            tp(0, 0, 22, 180, 20).accept(sp);
            LootCrates.place(sp.serverLevel(), StrikeGame.devCenter.offset(0, 0, 17), sp.getRandom());
        });
        beat("waves_start", 130, true, sp -> StrikeGame.get(sp.getServer()).startWaves(sp));
        beat("wave_1", 120, true, sp -> { });
        beat("waves_stop", 20, false, sp -> StrikeGame.get(sp.getServer()).stop(true));
        beat("br_start", 60, true, sp -> StrikeGame.get(sp.getServer()).startBattleRoyale(sp, 1, 6));
        beat("br_zone", 260, true, sp -> { });
        beat("br_stop", 20, false, sp -> StrikeGame.get(sp.getServer()).stop(true));
        beat("end", 20, false, sp -> { });
    }
}
