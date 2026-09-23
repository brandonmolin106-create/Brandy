package com.echoesinthedark.turtlepower.world;

import com.echoesinthedark.turtlepower.TurtlePower;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.objects.ObjectIterator;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CrossCollisionBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * Places a {@link BuildQueue} into the world over many ticks, with a progress bar:
 * load chunks, flatten the area, place blocks, fix fence/pane connections, then fill chests and
 * spawn characters.
 */
public class BuildJob {
    private enum Phase { LOAD, CLEAR, PLACE, SHAPES, POST, DONE }

    private static final long BUDGET_NANOS = 30_000_000L; // 30ms of work per tick

    private final ServerLevel level;
    private final BuildQueue queue;
    private final Layout layout;
    private final Consumer<BuildJob> onDone;
    private final ServerBossEvent bar = new ServerBossEvent(Component.literal("Building New York City..."),
            BossEvent.BossBarColor.GREEN, BossEvent.BossBarOverlay.PROGRESS);

    private final List<ChunkPos> chunks = new ArrayList<>();
    private Phase phase = Phase.LOAD;
    private int chunkIndex;
    private int clearX, clearZ;
    private ObjectIterator<Long2ObjectMap.Entry<BlockState>> placeIter;
    private int placed;
    private final List<BlockPos> shapeFix = new ArrayList<>();
    private int shapeIndex;
    private int postIndex;

    public BuildJob(ServerLevel level, BuildQueue queue, Layout layout, Consumer<BuildJob> onDone) {
        this.level = level;
        this.queue = queue;
        this.layout = layout;
        this.onDone = onDone;
        int r = Layout.AREA + 2;
        for (int cx = (layout.ox - r) >> 4; cx <= (layout.ox + r) >> 4; cx++) {
            for (int cz = (layout.oz - r) >> 4; cz <= (layout.oz + r) >> 4; cz++) {
                chunks.add(new ChunkPos(cx, cz));
            }
        }
        clearX = -Layout.AREA;
        clearZ = -Layout.AREA;
    }

    public Layout layout() {
        return layout;
    }

    public ServerLevel level() {
        return level;
    }

    public boolean isDone() {
        return phase == Phase.DONE;
    }

    /** Run one tick worth of work. */
    public void tick() {
        long start = System.nanoTime();
        for (ServerPlayer p : level.players()) {
            if (!bar.getPlayers().contains(p)) bar.addPlayer(p);
            if (p.tickCount % 40 == 0) {
                p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 60, 4, false, false));
                p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0, false, false));
            }
        }
        while (System.nanoTime() - start < BUDGET_NANOS && phase != Phase.DONE) {
            step();
        }
        updateBar();
    }

    private void step() {
        switch (phase) {
            case LOAD -> {
                if (chunkIndex < chunks.size()) {
                    ChunkPos c = chunks.get(chunkIndex++);
                    level.setChunkForced(c.x, c.z, true);
                    level.getChunk(c.x, c.z);
                } else {
                    phase = Phase.CLEAR;
                }
            }
            case CLEAR -> {
                // Knock down hills/trees/water above street level so the city sits on flat ground.
                for (int n = 0; n < 32 && phase == Phase.CLEAR; n++) {
                    clearColumn(layout.ox + clearX, layout.oz + clearZ, clearX, clearZ);
                    if (++clearZ > Layout.AREA) {
                        clearZ = -Layout.AREA;
                        if (++clearX > Layout.AREA) {
                            phase = Phase.PLACE;
                            placeIter = queue.blocks.long2ObjectEntrySet().fastIterator();
                        }
                    }
                }
            }
            case PLACE -> {
                BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
                for (int n = 0; n < 512; n++) {
                    if (!placeIter.hasNext()) {
                        phase = Phase.SHAPES;
                        return;
                    }
                    Long2ObjectMap.Entry<BlockState> e = placeIter.next();
                    pos.set(BlockPos.getX(e.getLongKey()), BlockPos.getY(e.getLongKey()), BlockPos.getZ(e.getLongKey()));
                    BlockState s = e.getValue();
                    level.setBlock(pos, s, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
                    placed++;
                    Block b = s.getBlock();
                    if (b instanceof CrossCollisionBlock || b instanceof WallBlock || b instanceof StairBlock || b instanceof FenceGateBlock) {
                        shapeFix.add(pos.immutable());
                    }
                }
            }
            case SHAPES -> {
                for (int n = 0; n < 512; n++) {
                    if (shapeIndex >= shapeFix.size()) {
                        phase = Phase.POST;
                        return;
                    }
                    BlockPos p = shapeFix.get(shapeIndex++);
                    BlockState s = level.getBlockState(p);
                    BlockState fixed = Block.updateFromNeighbourShapes(s, level, p);
                    if (fixed != s) {
                        level.setBlock(p, fixed, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
                    }
                }
            }
            case POST -> {
                if (postIndex < queue.post.size()) {
                    try {
                        queue.post.get(postIndex).accept(level);
                    } catch (Exception ex) {
                        TurtlePower.LOGGER.warn("Story build step failed", ex);
                    }
                    postIndex++;
                } else {
                    finish();
                }
            }
            default -> { }
        }
    }

    private void clearColumn(int x, int z, int dx, int dz) {
        int y0 = layout.y0;
        int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        BlockState air = Blocks.AIR.defaultBlockState();
        for (int y = y0 + 1; y < top; y++) {
            p.set(x, y, z);
            if (!level.getBlockState(p).isAir()) {
                level.setBlock(p, air, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
            }
        }
        int ax = Math.abs(dx), az = Math.abs(dz);
        // Under the city, plug caves, ravines and ocean so nothing is left floating.
        if (ax <= Layout.EDGE && az <= Layout.EDGE) {
            for (int y = y0 - 5; y > y0 - 40 && y > level.getMinBuildHeight(); y--) {
                p.set(x, y, z);
                BlockState cur = level.getBlockState(p);
                if (!cur.isAir() && cur.getFluidState().isEmpty()) break;
                level.setBlock(p, Blocks.STONE.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
            }
        }
        // Outside the seawall make a strip of harbour water so the city is an island.
        if (ax > Layout.EDGE || az > Layout.EDGE) {
            boolean outerRim = ax == Layout.AREA || az == Layout.AREA;
            if (outerRim) {
                // No need for a retaining wall if the city is already sitting in the ocean.
                BlockPos outside = new BlockPos(x + Integer.signum(dx), y0 - 1, z + Integer.signum(dz));
                outerRim = level.getFluidState(outside).isEmpty();
            }
            for (int y = y0 - 3; y <= y0 - 1; y++) {
                p.set(x, y, z);
                level.setBlock(p, (outerRim ? Blocks.STONE_BRICKS : Blocks.WATER).defaultBlockState(), Block.UPDATE_CLIENTS);
            }
            p.set(x, y0 - 4, z);
            if (level.getBlockState(p).isAir() || !level.getFluidState(p).isEmpty()) {
                level.setBlock(p, Blocks.STONE.defaultBlockState(), Block.UPDATE_CLIENTS);
            }
        }
    }

    private void finish() {
        for (ChunkPos c : chunks) {
            level.setChunkForced(c.x, c.z, false);
        }
        bar.removeAllPlayers();
        phase = Phase.DONE;
        TurtlePower.LOGGER.info("TMNT story world built: {} blocks around {} {} {}", placed, layout.ox, layout.y0, layout.oz);
        onDone.accept(this);
    }

    private void updateBar() {
        float progress;
        String label;
        switch (phase) {
            case LOAD -> {
                progress = 0.1F * chunkIndex / Math.max(1, chunks.size());
                label = "Finding a spot for New York...";
            }
            case CLEAR -> {
                progress = 0.1F + 0.1F * (clearX + Layout.AREA) / (2F * Layout.AREA);
                label = "Clearing the ground...";
            }
            case PLACE -> {
                progress = 0.2F + 0.7F * placed / Math.max(1, queue.size());
                label = placed < queue.size() / 3 ? "Building the streets and buildings..."
                        : placed < queue.size() * 2 / 3 ? "Digging the sewers..." : "Setting up the lair...";
            }
            case SHAPES -> {
                progress = 0.9F + 0.05F * shapeIndex / Math.max(1, shapeFix.size());
                label = "Fixing fences and windows...";
            }
            default -> {
                progress = 0.97F;
                label = "Waking up your brothers...";
            }
        }
        bar.setProgress(Math.max(0F, Math.min(1F, progress)));
        bar.setName(Component.literal("TMNT Story Mode: " + label + " " + (int) (progress * 100) + "%"));
    }
}
