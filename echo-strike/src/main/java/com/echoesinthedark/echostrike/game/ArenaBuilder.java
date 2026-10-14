package com.echoesinthedark.echostrike.game;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Builds a small arena around a point: a flat floor, a wall around it, crates and low walls for
 * cover, two sniper towers and a raised middle. Good for waves and for a quick deathmatch.
 */
public final class ArenaBuilder {
    private ArenaBuilder() {}

    public static final int HALF = 26;

    public static void build(ServerLevel level, BlockPos center, RandomSource rand) {
        int cx = center.getX(), cy = center.getY(), cz = center.getZ();
        BlockState floor = Blocks.POLISHED_ANDESITE.defaultBlockState();
        BlockState floor2 = Blocks.GRAY_CONCRETE.defaultBlockState();
        BlockState wall = Blocks.DEEPSLATE_BRICKS.defaultBlockState();
        BlockState wallTop = Blocks.DEEPSLATE_TILES.defaultBlockState();
        BlockState air = Blocks.AIR.defaultBlockState();

        // Clear the box and lay the floor.
        for (int x = -HALF; x <= HALF; x++) {
            for (int z = -HALF; z <= HALF; z++) {
                for (int y = 0; y <= 14; y++) {
                    level.setBlock(new BlockPos(cx + x, cy + y, cz + z), air, 2);
                }
                boolean stripe = ((x + HALF) / 4 + (z + HALF) / 4) % 2 == 0;
                level.setBlock(new BlockPos(cx + x, cy - 1, cz + z), stripe ? floor : floor2, 2);
                // Fill underneath so the arena never floats over a valley or a lake.
                for (int y = 2; y <= 8; y++) {
                    BlockPos under = new BlockPos(cx + x, cy - y, cz + z);
                    BlockState s = level.getBlockState(under);
                    if (s.isAir() || !s.getFluidState().isEmpty() || s.canBeReplaced()) {
                        level.setBlock(under, Blocks.STONE.defaultBlockState(), 2);
                    }
                }
            }
        }
        // Outer wall.
        for (int i = -HALF; i <= HALF; i++) {
            for (int y = 0; y < 5; y++) {
                BlockState s = y == 4 ? wallTop : wall;
                level.setBlock(new BlockPos(cx + i, cy + y, cz - HALF), s, 2);
                level.setBlock(new BlockPos(cx + i, cy + y, cz + HALF), s, 2);
                level.setBlock(new BlockPos(cx - HALF, cy + y, cz + i), s, 2);
                level.setBlock(new BlockPos(cx + HALF, cy + y, cz + i), s, 2);
            }
        }
        // Light it up so the arena works at night.
        for (int x = -HALF + 1; x < HALF; x += 6) {
            for (int z = -HALF + 1; z < HALF; z += 6) {
                level.setBlock(new BlockPos(cx + x, cy - 1, cz + z), Blocks.SEA_LANTERN.defaultBlockState(), 2);
            }
        }
        // Raised middle platform with stairs on each side.
        platform(level, cx, cy, cz, 5, 2, Blocks.STONE_BRICKS.defaultBlockState());
        for (int i = -2; i <= 2; i++) {
            level.setBlock(new BlockPos(cx + i, cy, cz + 6), Blocks.STONE_BRICK_STAIRS.defaultBlockState(), 2);
            level.setBlock(new BlockPos(cx + i, cy, cz - 6), Blocks.STONE_BRICK_STAIRS.defaultBlockState(), 2);
            level.setBlock(new BlockPos(cx + 6, cy, cz + i), Blocks.STONE_BRICK_STAIRS.defaultBlockState(), 2);
            level.setBlock(new BlockPos(cx - 6, cy, cz + i), Blocks.STONE_BRICK_STAIRS.defaultBlockState(), 2);
        }
        // Two sniper towers in opposite corners.
        tower(level, cx - HALF + 5, cy, cz - HALF + 5);
        tower(level, cx + HALF - 5, cy, cz + HALF - 5);
        // Cover: crates, low walls, barrels.
        Block[] crates = {Blocks.OAK_PLANKS, Blocks.SPRUCE_PLANKS, Blocks.IRON_BLOCK, Blocks.BARREL, Blocks.DARK_OAK_PLANKS};
        for (int n = 0; n < 34; n++) {
            int x = cx + rand.nextInt(HALF * 2 - 8) - HALF + 4;
            int z = cz + rand.nextInt(HALF * 2 - 8) - HALF + 4;
            if (Math.abs(x - cx) < 8 && Math.abs(z - cz) < 8) continue;
            int kind = rand.nextInt(3);
            if (kind == 0) {
                // stack of crates
                Block b = crates[rand.nextInt(crates.length)];
                int h = 1 + rand.nextInt(2);
                for (int y = 0; y < h; y++) {
                    level.setBlock(new BlockPos(x, cy + y, z), b.defaultBlockState(), 2);
                    if (rand.nextBoolean()) level.setBlock(new BlockPos(x + 1, cy + y, z), b.defaultBlockState(), 2);
                }
            } else if (kind == 1) {
                // low wall
                boolean alongX = rand.nextBoolean();
                int len = 3 + rand.nextInt(4);
                for (int i = 0; i < len; i++) {
                    BlockPos p = alongX ? new BlockPos(x + i, cy, z) : new BlockPos(x, cy, z + i);
                    level.setBlock(p, Blocks.STONE_BRICK_WALL.defaultBlockState(), 2);
                }
            } else {
                // concrete block cover
                level.setBlock(new BlockPos(x, cy, z), Blocks.RED_CONCRETE.defaultBlockState(), 2);
                level.setBlock(new BlockPos(x, cy + 1, z), Blocks.RED_CONCRETE.defaultBlockState(), 2);
                level.setBlock(new BlockPos(x + 1, cy, z), Blocks.RED_CONCRETE.defaultBlockState(), 2);
            }
        }
        // A sign of who built it.
        for (int i = 0; i < 4; i++) {
            level.setBlock(new BlockPos(cx - 1 + i, cy + 5, cz - HALF), Blocks.REDSTONE_BLOCK.defaultBlockState(), 2);
        }
    }

    private static void platform(ServerLevel level, int cx, int cy, int cz, int half, int height, BlockState block) {
        for (int x = -half; x <= half; x++) {
            for (int z = -half; z <= half; z++) {
                for (int y = 0; y < height; y++) {
                    level.setBlock(new BlockPos(cx + x, cy + y, cz + z), block, 2);
                }
            }
        }
        for (int i = -half; i <= half; i += half) {
            for (int j = -half; j <= half; j += half) {
                level.setBlock(new BlockPos(cx + i, cy + height, cz + j), Blocks.STONE_BRICK_WALL.defaultBlockState(), 2);
            }
        }
    }

    private static void tower(ServerLevel level, int x, int y, int z) {
        for (int h = 0; h < 7; h++) {
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    boolean edge = Math.abs(dx) == 1 || Math.abs(dz) == 1;
                    BlockState s = edge ? Blocks.DEEPSLATE_BRICKS.defaultBlockState() : Blocks.AIR.defaultBlockState();
                    if (h == 6) s = Blocks.DEEPSLATE_TILES.defaultBlockState();
                    level.setBlock(new BlockPos(x + dx, y + h, z + dz), s, 2);
                }
            }
            level.setBlock(new BlockPos(x, y + h, z), Blocks.LADDER.defaultBlockState(), 2);
        }
        // door hole
        level.setBlock(new BlockPos(x, y, z + 1), Blocks.AIR.defaultBlockState(), 2);
        level.setBlock(new BlockPos(x, y + 1, z + 1), Blocks.AIR.defaultBlockState(), 2);
        // parapet on top
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                boolean edge = Math.abs(dx) == 2 || Math.abs(dz) == 2;
                level.setBlock(new BlockPos(x + dx, y + 6, z + dz), Blocks.DEEPSLATE_TILES.defaultBlockState(), 2);
                if (edge) level.setBlock(new BlockPos(x + dx, y + 7, z + dz), Blocks.DEEPSLATE_TILE_WALL.defaultBlockState(), 2);
            }
        }
        level.setBlock(new BlockPos(x, y + 6, z), Blocks.AIR.defaultBlockState(), 2);
        level.setBlock(new BlockPos(x, y + 5, z), Blocks.LADDER.defaultBlockState(), 2);
    }
}
