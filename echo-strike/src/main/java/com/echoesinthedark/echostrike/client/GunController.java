package com.echoesinthedark.echostrike.client;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.network.ModNetwork;
import com.echoesinthedark.echostrike.network.ReloadPacket;
import com.echoesinthedark.echostrike.network.ShootPacket;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.client.event.RenderGuiOverlayEvent;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.client.gui.overlay.VanillaGuiOverlay;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Turns the mouse into a trigger. Left click (held for full auto) asks the server to shoot,
 * right click aims (zoom + tighter spread), R reloads. Recoil kicks the camera right here on the
 * client so it feels instant.
 */
@Mod.EventBusSubscriber(modid = EchoStrike.MODID, value = Dist.CLIENT)
public final class GunController {
    private GunController() {}

    private static boolean attackWasDown;
    private static long lastShotTick = -100000L;
    /** 0 = hip, 1 = fully aimed. Eased every tick so the zoom glides. */
    private static float zoom, zoomO;
    private static boolean aiming;
    private static float lastSpread;
    /** Recoil kick, 1 right after a shot, decaying fast. */
    private static float kick, kickO;
    /** Sprint pose, eased 0..1. */
    private static float sprint, sprintO;
    private static float reloadO, reloadNow;

    public static boolean isAiming() {
        return aiming;
    }

    public static float zoomProgress(float partialTick) {
        return Mth.lerp(partialTick, zoomO, zoom);
    }

    public static float kickProgress(float partialTick) {
        return Mth.lerp(partialTick, kickO, kick);
    }

    public static float sprintProgress(float partialTick) {
        return Mth.lerp(partialTick, sprintO, sprint);
    }

    /** 0..1 reload animation progress (from the stack's reload timer), smoothed between ticks. */
    public static float reloadAnim(ItemStack stack, float partialTick) {
        return Mth.lerp(partialTick, reloadO, reloadNow);
    }

    /** The current cone of fire in degrees, for the crosshair. */
    public static float currentSpread() {
        return lastSpread;
    }

    public static GunType heldGun(LocalPlayer p) {
        ItemStack s = p.getMainHandItem();
        return s.getItem() instanceof GunItem g ? g.type : null;
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        zoomO = zoom;
        kickO = kick;
        sprintO = sprint;
        reloadO = reloadNow;
        if (p == null || mc.level == null) {
            attackWasDown = false;
            aiming = false;
            zoom = kick = sprint = reloadNow = 0;
            return;
        }
        GunType gun = heldGun(p);
        boolean inGame = mc.screen == null && !mc.isPaused();
        aiming = gun != null && inGame && mc.options.keyUse.isDown() && !p.isSprinting();
        zoom = Mth.clamp(zoom + (aiming ? 0.25F : -0.25F), 0, 1);
        kick *= 0.55F;
        if (kick < 0.02F) kick = 0;
        boolean sprinting = gun != null && p.isSprinting() && !aiming;
        sprint = Mth.clamp(sprint + (sprinting ? 0.2F : -0.25F), 0, 1);
        float rp = gun == null ? -1 : GunItem.reloadProgress(p.getMainHandItem(), mc.level.getGameTime());
        reloadNow = rp < 0 ? 0 : rp;

        if (gun == null) {
            attackWasDown = mc.options.keyAttack.isDown();
            lastSpread = 0;
            return;
        }
        ItemStack stack = p.getMainHandItem();
        lastSpread = gun.spread * com.echoesinthedark.echostrike.combat.Gunplay.spreadMultiplier(p, aiming);

        if (ModKeys.RELOAD.consumeClick() && inGame) {
            ModNetwork.CHANNEL.sendToServer(new ReloadPacket());
        }

        boolean attack = inGame && mc.options.keyAttack.isDown();
        boolean trigger = gun.auto ? attack : (attack && !attackWasDown);
        attackWasDown = attack;
        if (!trigger) return;

        long now = mc.level.getGameTime();
        if (now - lastShotTick < gun.ticksPerShot) return;
        if (GunItem.isReloading(stack, now)) return;
        lastShotTick = now;
        ModNetwork.CHANNEL.sendToServer(new ShootPacket(aiming));
        if (GunItem.getAmmo(stack) > 0 || p.isCreative()) {
            kick(p, gun);
        }
    }

    private static void kick(LocalPlayer p, GunType gun) {
        float r = p.getRandom().nextFloat();
        float scale = aiming ? 0.6F : 1.0F;
        float up = gun.recoilVertical * (0.6F + r * 0.5F) * scale;
        float side = (p.getRandom().nextFloat() - 0.5F) * gun.recoilHorizontal * 1.6F * scale;
        p.setXRot(Mth.clamp(p.getXRot() - up, -90, 90));
        p.setYRot(p.getYRot() + side);
        kick = 1.0F;
    }

    /** Left click with a gun never swings or breaks blocks. */
    @SubscribeEvent
    public static void onClick(InputEvent.InteractionKeyMappingTriggered event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || heldGun(mc.player) == null) return;
        if (event.isAttack()) {
            event.setCanceled(true);
            event.setSwingHand(false);
        }
        // Right click stays enabled so chests and doors still open while you're aiming;
        // GunItem.use() itself does nothing.
    }

    /** Aiming zooms in. The sniper gets a real scope. */
    @SubscribeEvent
    public static void onFov(ViewportEvent.ComputeFov event) {
        if (!event.usedConfiguredFov()) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        GunType gun = heldGun(mc.player);
        if (gun == null || zoom <= 0 && zoomO <= 0) return;
        float t = zoomProgress((float) event.getPartialTick());
        double factor = 1.0 / Mth.lerp(t, 1.0F, gun.zoom);
        event.setFOV(event.getFOV() * factor);
    }

    /** Our HUD draws its own crosshair. */
    @SubscribeEvent
    public static void onOverlay(RenderGuiOverlayEvent.Pre event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        if (event.getOverlay().id().equals(VanillaGuiOverlay.CROSSHAIR.id()) && heldGun(mc.player) != null) {
            event.setCanceled(true);
        }
    }
}
