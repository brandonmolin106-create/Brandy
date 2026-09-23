package com.echoesinthedark.turtlepower.block;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.state.properties.BlockSetType;

/**
 * Iron manhole cover. Unlike a vanilla iron trapdoor you can pop it open with your hand, and because
 * it is a trapdoor, Minecraft lets you climb through it when it sits on top of a ladder facing the
 * same way.
 */
public class ManholeCoverBlock extends TrapDoorBlock {
    public static final BlockSetType MANHOLE = BlockSetType.register(new BlockSetType(
            "turtlepower_manhole", true, SoundType.METAL,
            SoundEvents.IRON_DOOR_CLOSE, SoundEvents.IRON_DOOR_OPEN,
            SoundEvents.IRON_TRAPDOOR_CLOSE, SoundEvents.IRON_TRAPDOOR_OPEN,
            SoundEvents.METAL_PRESSURE_PLATE_CLICK_OFF, SoundEvents.METAL_PRESSURE_PLATE_CLICK_ON,
            SoundEvents.STONE_BUTTON_CLICK_OFF, SoundEvents.STONE_BUTTON_CLICK_ON));

    public ManholeCoverBlock(Properties properties) {
        super(properties, MANHOLE);
    }
}
