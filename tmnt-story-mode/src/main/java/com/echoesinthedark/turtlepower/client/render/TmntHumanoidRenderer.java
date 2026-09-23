package com.echoesinthedark.turtlepower.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Mob;

/** Renders any of our humanoid characters with a fixed texture and size. */
public class TmntHumanoidRenderer<T extends Mob> extends HumanoidMobRenderer<T, HumanoidModel<T>> {
    private final ResourceLocation texture;
    private final float scale;

    public TmntHumanoidRenderer(EntityRendererProvider.Context ctx, ModelLayerLocation layer, ResourceLocation texture,
                                float scale, float shadow) {
        super(ctx, new HumanoidModel<>(ctx.bakeLayer(layer)), shadow);
        this.texture = texture;
        this.scale = scale;
    }

    @Override
    public ResourceLocation getTextureLocation(T entity) {
        return texture;
    }

    @Override
    protected void scale(T entity, PoseStack pose, float partialTick) {
        if (scale != 1.0F) {
            pose.scale(scale, scale, scale);
        }
    }
}
