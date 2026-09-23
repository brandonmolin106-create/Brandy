package com.echoesinthedark.turtlepower.world;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.levelgen.FlatLevelSource;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Plans the whole story world (city, sewers, lair) around a centre point and hands it to a
 * {@link BuildJob} to place.
 */
public final class StoryWorldBuilder {
    private StoryWorldBuilder() {}

    /** Work out the street level for a city centred at (x, z). */
    public static int pickStreetLevel(ServerLevel level, int x, int z) {
        level.getChunk(x >> 4, z >> 4);
        int surface = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
        int y0 = surface;
        // In normal worlds keep the streets above the ocean. Flat worlds report a sea level that
        // has nothing to do with their layers, so there we just trust the surface.
        if (!(level.getChunkSource().getGenerator() instanceof FlatLevelSource)) {
            y0 = Math.max(y0, level.getSeaLevel() + 2);
        }
        // Keep the lair above the bottom of the world and the tallest tower under the build limit.
        int min = level.getMinBuildHeight() + 36;
        int max = level.getMaxBuildHeight() - 100;
        return Math.max(min, Math.min(max, y0));
    }

    public static Layout plan(BuildQueue q, BlockPos centre) {
        Layout L = new Layout(centre.getX(), centre.getY(), centre.getZ());
        // Order matters: later pieces overwrite earlier ones where they touch.
        CityBuilder.build(q, L);
        SewerBuilder.build(q, L);
        LairBuilder.build(q, L);
        return L;
    }
}
