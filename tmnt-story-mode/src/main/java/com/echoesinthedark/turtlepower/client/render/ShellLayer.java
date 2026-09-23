package com.echoesinthedark.turtlepower.client.render;

import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.client.model.TmntModels;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.EntityModelSet;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;

/** Draws a real 3D turtle shell on the back of any player wearing the Turtle Shell. */
public class ShellLayer extends RenderLayer<AbstractClientPlayer, PlayerModel<AbstractClientPlayer>> {
    private static final ResourceLocation TEXTURE = TurtlePower.id("textures/entity/player_shell.png");
    private final ModelPart shell;

    public ShellLayer(RenderLayerParent<AbstractClientPlayer, PlayerModel<AbstractClientPlayer>> parent, EntityModelSet models) {
        super(parent);
        this.shell = models.bakeLayer(TmntModels.PLAYER_SHELL).getChild("shell");
    }

    @Override
    public void render(PoseStack pose, MultiBufferSource buffers, int light, AbstractClientPlayer player,
                       float limbSwing, float limbSwingAmount, float partialTick, float ageInTicks, float netHeadYaw, float headPitch) {
        if (!player.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.TURTLE_SHELL.get()) || player.isInvisible()) {
            return;
        }
        pose.pushPose();
        getParentModel().body.translateAndRotate(pose);
        shell.render(pose, buffers.getBuffer(RenderType.entityCutoutNoCull(TEXTURE)), light, OverlayTexture.NO_OVERLAY);
        pose.popPose();
    }
}
