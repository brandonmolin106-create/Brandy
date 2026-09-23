package com.echoesinthedark.turtlepower.block;

import com.echoesinthedark.turtlepower.entity.Mutation;
import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.joml.Vector3f;

public class MutagenOozeBlock extends Block {
    private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 1, 16);
    public static final DustParticleOptions GLOW = new DustParticleOptions(new Vector3f(0.35F, 1.0F, 0.2F), 1.2F);

    public MutagenOozeBlock(Properties properties) {
        super(properties);
    }

    @Override
    public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    @Override
    public boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        return !level.isEmptyBlock(pos.below());
    }

    @Override
    public BlockState updateShape(BlockState state, Direction dir, BlockState neighbor, LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        return !state.canSurvive(level, pos) ? Blocks.AIR.defaultBlockState() : super.updateShape(state, dir, neighbor, level, pos, neighborPos);
    }

    @Override
    public void stepOn(Level level, BlockPos pos, BlockState state, Entity entity) {
        if (!level.isClientSide && entity instanceof LivingEntity living && !(entity instanceof TurtleBrotherEntity)
                && level.getGameTime() % 20 == 0) {
            RandomSource r = level.getRandom();
            if (living instanceof Player) {
                // Mutagen on your shell tingles: a random short burst of weird powers.
                switch (r.nextInt(4)) {
                    case 0 -> living.addEffect(new MobEffectInstance(MobEffects.JUMP, 100, 2));
                    case 1 -> living.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 100, 1));
                    case 2 -> living.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 80, 0));
                    default -> living.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100, 0));
                }
            } else if (living instanceof Mob mob && r.nextInt(3) == 0) {
                Mutation.mutate((ServerLevel) level, mob, null);
            }
            ((ServerLevel) level).sendParticles(GLOW, entity.getX(), entity.getY() + 0.2, entity.getZ(), 6, 0.3, 0.1, 0.3, 0.0);
        }
        super.stepOn(level, pos, state, entity);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(3) == 0) {
            level.addParticle(GLOW, pos.getX() + random.nextDouble(), pos.getY() + 0.1, pos.getZ() + random.nextDouble(), 0, 0.02, 0);
        }
        if (random.nextInt(12) == 0) {
            level.addParticle(ParticleTypes.BUBBLE_POP, pos.getX() + random.nextDouble(), pos.getY() + 0.1, pos.getZ() + random.nextDouble(), 0, 0.05, 0);
        }
    }
}
