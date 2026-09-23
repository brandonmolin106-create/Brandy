package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.network.ObjectivePacket;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** Top-left mission panel: chapter, objective, progress, and a green arrow pointing where to go. */
public final class ObjectiveHud {
    private ObjectiveHud() {}

    private static final ResourceLocation ARROW = TurtlePower.id("textures/gui/arrow.png");
    @Nullable private static ObjectivePacket objective;

    public static void set(ObjectivePacket packet) {
        objective = packet.chapter().isEmpty() ? null : packet;
    }

    public static void clear() {
        objective = null;
    }

    public static void render(GuiGraphics g, int width, int height, float partialTick) {
        Minecraft mc = Minecraft.getInstance();
        if (objective == null || !Config.SHOW_OBJECTIVE_HUD.get() || mc.player == null || mc.options.renderDebug) {
            return;
        }
        Font font = mc.font;
        // Stay clear of boss health bars in the middle of the top of the screen.
        int panelW = Math.max(110, Math.min(190, (width - 182) / 2 - 6));
        List<FormattedCharSequence> title = font.split(Component.literal(objective.chapter()).withStyle(s -> s.withBold(true)), panelW - 30);
        List<FormattedCharSequence> lines = font.split(Component.literal(objective.objective()), panelW - 12);
        int h = 6 + title.size() * 10 + lines.size() * 10 + (objective.progress().isEmpty() ? 0 : 10) + (objective.target() != null ? 12 : 0);
        int x = 4, y = 4;
        g.fill(x, y, x + panelW, y + h, 0x90000000);
        g.fill(x, y, x + 2, y + h, 0xFF3FBF3F);
        int ty = y + 4;
        for (FormattedCharSequence t : title) {
            g.drawString(font, t, x + 6, ty, 0xFF6DFF6D, true);
            ty += 10;
        }
        ty += 2;
        for (FormattedCharSequence line : lines) {
            g.drawString(font, line, x + 6, ty, 0xFFFFFFFF, true);
            ty += 10;
        }
        if (!objective.progress().isEmpty()) {
            g.drawString(font, "Progress: " + objective.progress(), x + 6, ty, 0xFFFFD84A, true);
            ty += 10;
        }
        BlockPos target = objective.target();
        if (target != null) {
            Player p = mc.player;
            double dx = target.getX() + 0.5 - p.getX();
            double dz = target.getZ() + 0.5 - p.getZ();
            double dy = target.getY() - p.getY();
            int dist = (int) Math.sqrt(dx * dx + dz * dz + dy * dy);
            // Minecraft yaw: 0 = south, 90 = west.
            float targetYaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
            float rel = Mth.wrapDegrees(targetYaw - p.getViewYRot(partialTick));
            int ax = x + panelW - 18, ay = y + 4;
            g.pose().pushPose();
            g.pose().translate(ax + 7, ay + 7, 0);
            g.pose().mulPose(Axis.ZP.rotationDegrees(rel));
            g.blit(ARROW, -7, -7, 14, 14, 0, 0, 16, 16, 16, 16);
            g.pose().popPose();
            String where = dist + " blocks away";
            if (dy > 3) where += ", UP";
            else if (dy < -3) where += ", DOWN";
            if (dist < 4) where = "You're here!";
            g.drawString(font, where, x + 6, ty + 1, 0xFF9FE0FF, true);
        }
    }
}
