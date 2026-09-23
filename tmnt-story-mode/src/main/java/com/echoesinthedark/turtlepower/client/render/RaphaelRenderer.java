package com.echoesinthedark.turtlepower.client.render;

import com.echoesinthedark.turtlepower.TurtlePower;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.resources.ResourceLocation;

/** A normal player renderer that uses Raphael's skin instead of your Minecraft skin. */
public class RaphaelRenderer extends PlayerRenderer {
    public static final ResourceLocation SKIN = TurtlePower.id("textures/entity/raphael.png");

    public RaphaelRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, false);
        addLayer(new ShellLayer(this, ctx.getModelSet()));
    }

    @Override
    public ResourceLocation getTextureLocation(AbstractClientPlayer player) {
        return SKIN;
    }
}
