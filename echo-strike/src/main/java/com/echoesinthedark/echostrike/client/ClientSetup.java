package com.echoesinthedark.echostrike.client;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.client.render.OperativeRenderer;
import com.echoesinthedark.echostrike.registry.ModEntities;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Registers renderers, model shapes, key bindings and the HUD. */
@Mod.EventBusSubscriber(modid = EchoStrike.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClientSetup {
    private ClientSetup() {}

    public static final ModelLayerLocation OPERATIVE_LAYER = new ModelLayerLocation(EchoStrike.id("operative"), "main");

    /** A normal humanoid using the 64x64 skin layout so the left and right limbs can differ. */
    private static LayerDefinition operativeModel() {
        MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
        PartDefinition root = mesh.getRoot();
        root.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(32, 48)
                .addBox(-1.0F, -2.0F, -2.0F, 4.0F, 12.0F, 4.0F), PartPose.offset(5.0F, 2.0F, 0.0F));
        root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(16, 48)
                .addBox(-2.0F, 0.0F, -2.0F, 4.0F, 12.0F, 4.0F), PartPose.offset(1.9F, 12.0F, 0.0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    @SubscribeEvent
    public static void layers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(OPERATIVE_LAYER, ClientSetup::operativeModel);
    }

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModEntities.OPERATIVE.get(), OperativeRenderer::new);
        event.registerEntityRenderer(ModEntities.FRAG_GRENADE.get(), ThrownItemRenderer::new);
    }

    @SubscribeEvent
    public static void keys(RegisterKeyMappingsEvent event) {
        event.register(ModKeys.RELOAD);
    }

    @SubscribeEvent
    public static void overlays(RegisterGuiOverlaysEvent event) {
        event.registerAboveAll("strike_hud", (gui, g, partialTick, w, h) -> StrikeHud.render(g, w, h, partialTick));
    }
}
