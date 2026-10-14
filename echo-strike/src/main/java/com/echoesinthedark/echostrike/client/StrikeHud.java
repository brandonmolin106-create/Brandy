package com.echoesinthedark.echostrike.client;

import com.echoesinthedark.echostrike.game.StrikeGame;
import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.network.HitmarkerPacket;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ItemStack;

/**
 * The shooter HUD: dynamic crosshair, hitmarker, ammo counter with a reload bar, sniper scope.
 */
public final class StrikeHud {
    private StrikeHud() {}

    private static int hitTicks;
    private static int hitKind;
    private static long hitAt;

    public static void hitmarker(int kind) {
        hitKind = kind;
        hitTicks = kind == HitmarkerPacket.KILL ? 14 : 8;
        Minecraft mc = Minecraft.getInstance();
        hitAt = mc.level == null ? 0 : mc.level.getGameTime();
        if (mc.player != null) {
            float pitch = kind == HitmarkerPacket.KILL ? 0.7F : kind == HitmarkerPacket.HEADSHOT ? 1.6F : 1.2F;
            mc.player.playSound(SoundEvents.ARROW_HIT_PLAYER, 0.5F, pitch);
        }
    }

    public static void render(GuiGraphics g, int width, int height, float partialTick) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.level == null || mc.options.hideGui) return;
        GunType gun = GunController.heldGun(p);
        if (gun == null) return;
        ItemStack stack = p.getMainHandItem();
        int cx = width / 2, cy = height / 2;
        long now = mc.level.getGameTime();
        float zoom = GunController.zoomProgress(partialTick);

        // ---- sniper scope
        if (gun.is(GunType.Class.SNIPER) && zoom > 0.85F) {
            int r = Math.min(width, height) / 2 - 10;
            g.fill(0, 0, width, cy - r, 0xF0000000);
            g.fill(0, cy + r, width, height, 0xF0000000);
            g.fill(0, cy - r, cx - r, cy + r, 0xF0000000);
            g.fill(cx + r, cy - r, width, cy + r, 0xF0000000);
            g.fill(cx - r, cy, cx + r, cy + 1, 0xC0000000);
            g.fill(cx, cy - r, cx + 1, cy + r, 0xC0000000);
            g.fill(cx - 1, cy - 1, cx + 2, cy + 2, 0xFFFF2020);
        } else {
            // ---- dynamic crosshair: the gap grows with the cone of fire
            float spread = GunController.currentSpread();
            int gap = 3 + Math.round(spread * 2.2F);
            int len = 5;
            int color = GunItem.getAmmo(stack) == 0 ? 0xFFFF4040 : 0xFFFFFFFF;
            g.fill(cx - gap - len, cy, cx - gap, cy + 1, color);
            g.fill(cx + gap + 1, cy, cx + gap + 1 + len, cy + 1, color);
            g.fill(cx, cy - gap - len, cx + 1, cy - gap, color);
            g.fill(cx, cy + gap + 1, cx + 1, cy + gap + 1 + len, color);
            g.fill(cx, cy, cx + 1, cy + 1, color);
        }

        // ---- hitmarker (an X that fades)
        if (hitTicks > 0) {
            int age = (int) (now - hitAt);
            if (age > hitTicks) {
                hitTicks = 0;
            } else {
                int color = switch (hitKind) {
                    case HitmarkerPacket.KILL -> 0xFFFF3030;
                    case HitmarkerPacket.HEADSHOT -> 0xFFFFD040;
                    default -> 0xFFFFFFFF;
                };
                int size = hitKind == HitmarkerPacket.KILL ? 9 : 7;
                for (int i = 3; i <= size; i++) {
                    g.fill(cx - i, cy - i, cx - i + 1, cy - i + 1, color);
                    g.fill(cx + i, cy - i, cx + i + 1, cy - i + 1, color);
                    g.fill(cx - i, cy + i, cx - i + 1, cy + i + 1, color);
                    g.fill(cx + i, cy + i, cx + i + 1, cy + i + 1, color);
                }
            }
        }

        // ---- ammo panel, bottom right
        Font font = mc.font;
        int ammo = GunItem.getAmmo(stack);
        int reserve = p.isCreative() ? 999 : GunItem.countAmmoInInventory(p, gun.ammo.get());
        String name = gun.displayName();
        String counter = ammo + " / " + reserve;
        int panelW = 120, panelH = 40;
        int x = width - panelW - 6, y = height - panelH - 6;
        g.fill(x, y, x + panelW, y + panelH, 0x90000000);
        g.fill(x, y, x + 2, y + panelH, ammo == 0 ? 0xFFFF3030 : 0xFFE02030);
        g.drawString(font, name, x + 8, y + 5, 0xFFDDDDDD, true);
        g.pose().pushPose();
        g.pose().translate(x + 8, y + 16, 0);
        g.pose().scale(2.0F, 2.0F, 1.0F);
        g.drawString(font, counter, 0, 0, ammo == 0 ? 0xFFFF5050 : 0xFFFFFFFF, true);
        g.pose().popPose();
        float reload = GunItem.reloadProgress(stack, now);
        if (reload >= 0) {
            int barW = panelW - 16;
            g.fill(x + 8, y + panelH - 6, x + 8 + barW, y + panelH - 3, 0xFF303030);
            g.fill(x + 8, y + panelH - 6, x + 8 + Math.round(barW * reload), y + panelH - 3, 0xFFFFC832);
            g.drawString(font, "RELOADING", x + panelW - 8 - font.width("RELOADING"), y + 5, 0xFFFFC832, true);
        } else if (ammo == 0) {
            g.drawString(font, "PRESS R", x + panelW - 8 - font.width("PRESS R"), y + 5, 0xFFFF5050, true);
        } else if (GunController.isAiming()) {
            g.drawString(font, "ADS", x + panelW - 8 - font.width("ADS"), y + 5, 0xFF80D0FF, true);
        }
        if (MovementController.isSliding()) {
            g.drawString(font, "SLIDE", x + 8, y - 10, 0xFF80FF80, true);
        }
    }

    @SuppressWarnings("unused")
    private static String modeName(StrikeGame.Mode mode) {
        return mode.name();
    }
}
