package com.echoesinthedark.echostrike.server;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.command.StrikeCommand;
import com.echoesinthedark.echostrike.game.StrikeGame;
import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.UUID;

/** Server-side glue: commands, game mode ticking, the tactical sprint speed boost, first-join kit. */
@Mod.EventBusSubscriber(modid = EchoStrike.MODID)
public final class ServerEvents {
    private ServerEvents() {}

    private static final UUID TAC_SPRINT_ID = UUID.fromString("5d6f3c1e-0b0a-4e2c-9f5e-1a2b3c4d5e6f");
    private static final AttributeModifier TAC_SPRINT = new AttributeModifier(TAC_SPRINT_ID, "Echo Strike tactical sprint", 0.22, AttributeModifier.Operation.MULTIPLY_TOTAL);

    @SubscribeEvent
    public static void onCommands(RegisterCommandsEvent event) {
        StrikeCommand.register(event.getDispatcher());
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase == TickEvent.Phase.END) {
            StrikeGame.get(event.getServer()).tick();
        }
    }

    @SubscribeEvent
    public static void onServerStopping(ServerStoppingEvent event) {
        StrikeGame.onServerStopping(event.getServer());
    }

    /** Operators move faster when sprinting with a gun: that's the tactical sprint. */
    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || event.player.level().isClientSide) return;
        Player p = event.player;
        AttributeInstance speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed == null) return;
        boolean want = p.isSprinting() && holdingGun(p) && !p.isUsingItem();
        boolean has = speed.getModifier(TAC_SPRINT_ID) != null;
        if (want && !has) speed.addTransientModifier(TAC_SPRINT);
        else if (!want && has) speed.removeModifier(TAC_SPRINT_ID);
    }

    private static boolean holdingGun(Player p) {
        return p.getMainHandItem().getItem() instanceof GunItem;
    }

    /** Guns never melee or punch blocks; the client sends a shoot packet instead. */
    @SubscribeEvent
    public static void onAttackEntity(AttackEntityEvent event) {
        if (holdingGun(event.getEntity())) event.setCanceled(true);
    }

    @SubscribeEvent
    public static void onLeftClickBlock(PlayerInteractEvent.LeftClickBlock event) {
        if (holdingGun(event.getEntity())) event.setCanceled(true);
    }

    @SubscribeEvent
    public static void onDeath(LivingDeathEvent event) {
        if (event.getEntity() instanceof ServerPlayer p) {
            StrikeGame.get(p.getServer()).onPlayerDeath(p);
        }
    }

    @SubscribeEvent
    public static void onRespawn(PlayerEvent.PlayerRespawnEvent event) {
        if (event.getEntity() instanceof ServerPlayer p) {
            StrikeGame.get(p.getServer()).onPlayerRespawn(p);
        }
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer p)) return;
        CompoundTag persisted = p.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
        if (persisted.getBoolean("EchoStrikeWelcomed")) return;
        persisted.putBoolean("EchoStrikeWelcomed", true);
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, persisted);
        p.getInventory().add(new ItemStack(ModItems.G18.get()));
        p.getInventory().add(new ItemStack(ModItems.LIGHT_AMMO.get(), 40));
        p.sendSystemMessage(Component.literal("[Echo Strike] Locked and loaded. Left click shoots, right click aims, R reloads.").withStyle(ChatFormatting.RED));
        p.sendSystemMessage(Component.literal("Sprint + crouch to slide, run at a block to vault it. Type /strike for game modes.").withStyle(ChatFormatting.GRAY));
    }
}
