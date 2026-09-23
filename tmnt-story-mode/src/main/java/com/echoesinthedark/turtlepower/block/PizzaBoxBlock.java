package com.echoesinthedark.turtlepower.block;

import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Open pizza box with up to 8 slices. Right click to take a slice. Empty boxes slowly refill
 * (Mikey keeps ordering more from Antonio's).
 */
public class PizzaBoxBlock extends HorizontalDirectionalBlock {
    public static final IntegerProperty SLICES = IntegerProperty.create("slices", 0, 8);
    private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 3, 15);

    public PizzaBoxBlock(Properties properties) {
        super(properties.randomTicks());
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(SLICES, 8));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, SLICES);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState().setValue(FACING, ctx.getHorizontalDirection().getOpposite());
    }

    @Override
    public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    @Override
    @SuppressWarnings("deprecation")
    public InteractionResult use(BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
        int slices = state.getValue(SLICES);
        if (slices <= 0) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.literal("Empty... Mikey, did you eat ALL of it again?!"), true);
            }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        if (!level.isClientSide) {
            ItemStack slice = new ItemStack(ModItems.PIZZA_SLICE.get());
            if (!player.getInventory().add(slice)) {
                player.drop(slice, false);
            }
            level.setBlock(pos, state.setValue(SLICES, slices - 1), 3);
            level.playSound(null, pos, SoundEvents.WOOL_BREAK, SoundSource.BLOCKS, 0.7F, 1.4F);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        int slices = state.getValue(SLICES);
        if (slices < 8) {
            level.setBlock(pos, state.setValue(SLICES, Math.min(8, slices + 2)), 3);
        }
    }
}
