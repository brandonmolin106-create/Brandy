package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.Config;
import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.client.render.RaphaelRenderer;
import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.client.event.RenderArmEvent;
import net.minecraftforge.client.event.RenderPlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Makes you look like Raphael: anyone wearing Raph's mask is drawn with the Raphael skin (green
 * skin, plastron, pads), including your own arms in first person.
 */
@Mod.EventBusSubscriber(modid = TurtlePower.MODID, value = Dist.CLIENT)
public final class ClientEvents {
    private ClientEvents() {}

    private static boolean isRaph(Player p) {
        return Config.RAPH_SKIN.get() && p.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.RAPH_MASK.get());
    }

    @SubscribeEvent
    public static void onRenderPlayer(RenderPlayerEvent.Pre event) {
        RaphaelRenderer raph = ClientSetup.raphaelRenderer;
        if (raph == null || event.getRenderer() instanceof RaphaelRenderer) {
            return;
        }
        if (event.getEntity() instanceof AbstractClientPlayer player && isRaph(player)) {
            event.setCanceled(true);
            float pt = event.getPartialTick();
            float yaw = Mth.lerp(pt, player.yRotO, player.getYRot());
            raph.render(player, yaw, pt, event.getPoseStack(), event.getMultiBufferSource(), event.getPackedLight());
        }
    }

    /** Our renderer's renderRightHand fires RenderArmEvent again; this stops us from looping forever. */
    private static boolean drawingArm;

    @SubscribeEvent
    public static void onRenderArm(RenderArmEvent event) {
        RaphaelRenderer raph = ClientSetup.raphaelRenderer;
        AbstractClientPlayer player = event.getPlayer();
        if (drawingArm || raph == null || !isRaph(player)) {
            return;
        }
        event.setCanceled(true);
        drawingArm = true;
        try {
            if (event.getArm() == HumanoidArm.RIGHT) {
                raph.renderRightHand(event.getPoseStack(), event.getMultiBufferSource(), event.getPackedLight(), player);
            } else {
                raph.renderLeftHand(event.getPoseStack(), event.getMultiBufferSource(), event.getPackedLight(), player);
            }
        } finally {
            drawingArm = false;
        }
    }

    @SubscribeEvent
    public static void onLogout(ClientPlayerNetworkEvent.LoggingOut event) {
        DialogueHud.clear();
        ObjectiveHud.clear();
        Tts.stop();
    }
}
