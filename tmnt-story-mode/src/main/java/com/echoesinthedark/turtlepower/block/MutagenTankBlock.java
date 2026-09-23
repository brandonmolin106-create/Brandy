package com.echoesinthedark.turtlepower.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Glowing glass tank full of mutagen. Pure decoration for Donnie's lab and the Kraang HQ. */
public class MutagenTankBlock extends Block {
    public MutagenTankBlock(Properties properties) {
        super(properties);
    }

    @Override
    public boolean skipRendering(BlockState state, BlockState neighbor, Direction dir) {
        return neighbor.is(this) || super.skipRendering(state, neighbor, dir);
    }

    @Override
    public float getShadeBrightness(BlockState state, BlockGetter level, BlockPos pos) {
        return 1.0F;
    }

    @Override
    public boolean propagatesSkylightDown(BlockState state, BlockGetter level, BlockPos pos) {
        return true;
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(4) == 0) {
            level.addParticle(MutagenOozeBlock.GLOW, pos.getX() + 0.2 + random.nextDouble() * 0.6,
                    pos.getY() + random.nextDouble(), pos.getZ() + 0.2 + random.nextDouble() * 0.6, 0, 0.03, 0);
        }
        if (random.nextInt(10) == 0) {
            level.addParticle(ParticleTypes.BUBBLE_POP, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 0, 0.02, 0);
        }
    }
}
