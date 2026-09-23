package com.echoesinthedark.turtlepower.client;

import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.client.model.TmntModels;
import com.echoesinthedark.turtlepower.client.render.RaphaelRenderer;
import com.echoesinthedark.turtlepower.client.render.ShellLayer;
import com.echoesinthedark.turtlepower.client.render.TmntHumanoidRenderer;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Registers renderers, model shapes and HUD overlays. */
@Mod.EventBusSubscriber(modid = TurtlePower.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClientSetup {
    private ClientSetup() {}

    static RaphaelRenderer raphaelRenderer;

    private static ResourceLocation tex(String name) {
        return TurtlePower.id("textures/entity/" + name + ".png");
    }

    @SubscribeEvent
    public static void layers(EntityRenderersEvent.RegisterLayerDefinitions event) {
        event.registerLayerDefinition(TmntModels.TURTLE, TmntModels::turtle);
        event.registerLayerDefinition(TmntModels.RAT, TmntModels::rat);
        event.registerLayerDefinition(TmntModels.KRAANG, TmntModels::kraang);
        event.registerLayerDefinition(TmntModels.HUMAN, TmntModels::human);
        event.registerLayerDefinition(TmntModels.PLAYER_SHELL, TmntModels::playerShell);
    }

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(ModEntities.LEONARDO.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.TURTLE, tex("leonardo"), 0.97F, 0.5F));
        event.registerEntityRenderer(ModEntities.DONATELLO.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.TURTLE, tex("donatello"), 1.02F, 0.5F));
        event.registerEntityRenderer(ModEntities.MICHELANGELO.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.TURTLE, tex("michelangelo"), 0.92F, 0.5F));
        event.registerEntityRenderer(ModEntities.SPLINTER.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.RAT, tex("splinter"), 1.0F, 0.5F));
        event.registerEntityRenderer(ModEntities.APRIL.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.HUMAN, tex("april"), 0.94F, 0.5F));
        event.registerEntityRenderer(ModEntities.TRAINING_DUMMY.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.HUMAN, tex("training_dummy"), 1.0F, 0.4F));
        event.registerEntityRenderer(ModEntities.KRAANG_DROID.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.KRAANG, tex("kraang_droid"), 1.0F, 0.5F));
        event.registerEntityRenderer(ModEntities.KRAANG_PRIME.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.KRAANG, tex("kraang_prime"), 1.8F, 1.0F));
        event.registerEntityRenderer(ModEntities.FOOT_NINJA.get(), c -> new TmntHumanoidRenderer<>(c, TmntModels.HUMAN, tex("foot_ninja"), 1.0F, 0.5F));
        event.registerEntityRenderer(ModEntities.SHURIKEN.get(), ThrownItemRenderer::new);
        event.registerEntityRenderer(ModEntities.SMOKE_BOMB.get(), ThrownItemRenderer::new);
        event.registerEntityRenderer(ModEntities.KRAANG_BOLT.get(), c -> new ThrownItemRenderer<>(c, 1.2F, true));
    }

    @SubscribeEvent
    public static void addLayers(EntityRenderersEvent.AddLayers event) {
        for (String skin : event.getSkins()) {
            PlayerRenderer r = event.getSkin(skin);
            if (r != null) {
                r.addLayer(new ShellLayer(r, event.getEntityModels()));
            }
        }
        raphaelRenderer = new RaphaelRenderer(event.getContext());
    }

    @SubscribeEvent
    public static void overlays(RegisterGuiOverlaysEvent event) {
        event.registerAboveAll("objective", (gui, g, partialTick, w, h) -> ObjectiveHud.render(g, w, h, partialTick));
        event.registerAboveAll("dialogue", (gui, g, partialTick, w, h) -> DialogueHud.render(g, w, h));
    }
}
