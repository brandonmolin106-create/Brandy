package com.echoesinthedark.echostrike.client.render;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.client.ClientSetup;
import com.echoesinthedark.echostrike.entity.OperativeEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.resources.ResourceLocation;

/** Humanoid soldier with armor rendering, holding whatever gun it spawned with. */
public class OperativeRenderer extends HumanoidMobRenderer<OperativeEntity, HumanoidModel<OperativeEntity>> {
    private static final ResourceLocation[] SKINS = {
            EchoStrike.id("textures/entity/operative_0.png"),
            EchoStrike.id("textures/entity/operative_1.png"),
            EchoStrike.id("textures/entity/operative_2.png"),
            EchoStrike.id("textures/entity/operative_3.png"),
    };

    public OperativeRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new HumanoidModel<>(ctx.bakeLayer(ClientSetup.OPERATIVE_LAYER)), 0.5F);
        addLayer(new HumanoidArmorLayer<>(this,
                new HumanoidModel<>(ctx.bakeLayer(ModelLayers.PLAYER_INNER_ARMOR)),
                new HumanoidModel<>(ctx.bakeLayer(ModelLayers.PLAYER_OUTER_ARMOR)),
                ctx.getModelManager()));
    }

    /** Hold the gun up with both hands when fighting, carry it low otherwise. */
    @Override
    public void render(OperativeEntity entity, float yaw, float partialTick, com.mojang.blaze3d.vertex.PoseStack pose,
                       net.minecraft.client.renderer.MultiBufferSource buffer, int light) {
        boolean fighting = entity.isAggressive();
        getModel().rightArmPose = fighting ? HumanoidModel.ArmPose.BOW_AND_ARROW : HumanoidModel.ArmPose.ITEM;
        getModel().leftArmPose = fighting ? HumanoidModel.ArmPose.BOW_AND_ARROW : HumanoidModel.ArmPose.EMPTY;
        super.render(entity, yaw, partialTick, pose, buffer, light);
    }

    @Override
    public ResourceLocation getTextureLocation(OperativeEntity entity) {
        return SKINS[Math.floorMod(entity.getSquad(), SKINS.length)];
    }
}
