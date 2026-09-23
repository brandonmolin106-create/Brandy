package com.echoesinthedark.turtlepower;

import com.echoesinthedark.turtlepower.network.ModNetwork;
import com.echoesinthedark.turtlepower.registry.ModBlocks;
import com.echoesinthedark.turtlepower.registry.ModCreativeTab;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;
import com.mojang.logging.LogUtils;

/**
 * TMNT Turtle Power: Story Mode (unofficial fan mod).
 *
 * You play as Raphael. Leonardo, Donatello and Michelangelo follow you and jump in whenever
 * something tries to hurt you. The mod builds the lair, the sewers and a slice of New York City
 * and walks you through a five chapter story against the Kraang.
 */
@Mod(TurtlePower.MODID)
public class TurtlePower {
    public static final String MODID = "turtlepower";
    public static final Logger LOGGER = LogUtils.getLogger();

    public TurtlePower() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();

        ModBlocks.BLOCKS.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModEntities.ENTITY_TYPES.register(modBus);
        ModCreativeTab.TABS.register(modBus);

        modBus.addListener(this::commonSetup);

        ModLoadingContext.get().registerConfig(ModConfig.Type.CLIENT, Config.CLIENT_SPEC);
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, Config.COMMON_SPEC);
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        event.enqueueWork(ModNetwork::register);
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MODID, path);
    }
}
