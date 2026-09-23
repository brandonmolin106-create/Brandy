package com.echoesinthedark.turtlepower.registry;

import com.echoesinthedark.turtlepower.TurtlePower;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModCreativeTab {
    private ModCreativeTab() {}

    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, TurtlePower.MODID);

    public static final RegistryObject<CreativeModeTab> MAIN = TABS.register("main", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.turtlepower"))
            .icon(() -> new ItemStack(ModItems.SAI.get()))
            .displayItems((params, out) -> {
                for (RegistryObject<Item> item : ModItems.ITEMS.getEntries()) {
                    if (item != ModItems.KRAANG_BOLT) {
                        out.accept(item.get());
                    }
                }
            })
            .build());
}
