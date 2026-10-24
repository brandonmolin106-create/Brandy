package com.echoesinthedark.echostrike;

import com.echoesinthedark.echostrike.network.ModNetwork;
import com.echoesinthedark.echostrike.registry.ModCreativeTab;
import com.echoesinthedark.echostrike.registry.ModEntities;
import com.echoesinthedark.echostrike.registry.ModItems;
import com.mojang.logging.LogUtils;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

/**
 * Echo Strike: a BloodStrike-style shooter inside Minecraft.
 *
 * Hitscan guns with magazines, reloads, recoil and headshots; slide / vault / tactical sprint
 * movement; grenades, medkits and armor plates; enemy operatives with gun AI; and two game modes
 * (Wave Survival and Battle Royale with a shrinking zone) driven by the /strike command.
 */
@Mod(EchoStrike.MODID)
public class EchoStrike {
    public static final String MODID = "echostrike";
    public static final Logger LOGGER = LogUtils.getLogger();

    public EchoStrike() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        ModItems.ITEMS.register(modBus);
        ModEntities.ENTITY_TYPES.register(modBus);
        ModCreativeTab.TABS.register(modBus);
        modBus.addListener(this::commonSetup);
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        event.enqueueWork(ModNetwork::register);
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MODID, path);
    }
}
