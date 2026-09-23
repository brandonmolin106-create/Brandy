package com.echoesinthedark.turtlepower.registry;

import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.block.ManholeCoverBlock;
import com.echoesinthedark.turtlepower.block.MutagenOozeBlock;
import com.echoesinthedark.turtlepower.block.MutagenTankBlock;
import com.echoesinthedark.turtlepower.block.PizzaBoxBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModBlocks {
    private ModBlocks() {}

    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, TurtlePower.MODID);

    /** A sewer manhole cover. It works like a trapdoor you can open by hand, and you can climb through it from a ladder. */
    public static final RegistryObject<Block> MANHOLE_COVER = BLOCKS.register("manhole_cover",
            () -> new ManholeCoverBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.METAL).strength(3.0F, 6.0F).sound(SoundType.METAL).noOcclusion()));

    /** Glowing puddle of spilled mutagen. Step in it and weird things happen. */
    public static final RegistryObject<Block> MUTAGEN_OOZE = BLOCKS.register("mutagen_ooze",
            () -> new MutagenOozeBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.EMERALD).strength(0.2F).sound(SoundType.SLIME_BLOCK)
                    .lightLevel(s -> 10).noOcclusion().pushReaction(PushReaction.DESTROY)));

    /** Donnie's glass mutagen tank. */
    public static final RegistryObject<Block> MUTAGEN_TANK = BLOCKS.register("mutagen_tank",
            () -> new MutagenTankBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.EMERALD).strength(1.5F).sound(SoundType.GLASS)
                    .lightLevel(s -> 14).noOcclusion()
                    .isViewBlocking((s, l, p) -> false).isSuffocating((s, l, p) -> false)));

    /** Alien wall panel from Kraang tech. */
    public static final RegistryObject<Block> KRAANG_PANEL = BLOCKS.register("kraang_panel",
            () -> new Block(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_PINK).strength(4.0F, 9.0F).sound(SoundType.METAL)
                    .lightLevel(s -> 7).requiresCorrectToolForDrops()));

    /** A box of pizza from Antonio's. Right click to grab a slice. */
    public static final RegistryObject<Block> PIZZA_BOX = BLOCKS.register("pizza_box",
            () -> new PizzaBoxBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.WOOD).strength(0.5F).sound(SoundType.WOOL).noOcclusion()
                    .pushReaction(PushReaction.DESTROY)));
}
