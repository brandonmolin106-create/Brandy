package com.echoesinthedark.turtlepower.world;

import it.unimi.dsi.fastutil.longs.Long2ObjectLinkedOpenHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Container;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.LadderBlock;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.WallSignBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.entity.SignBlockEntity;
import net.minecraft.world.level.block.entity.SignText;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.DoorHingeSide;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.block.state.properties.Half;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * A big list of "put this block here" plus things to do afterwards (fill chests, write signs, spawn
 * people). Later writes to the same spot win. {@link BuildJob} places everything a few thousand blocks
 * per tick so the game doesn't freeze.
 */
public class BuildQueue {
    final Long2ObjectLinkedOpenHashMap<BlockState> blocks = new Long2ObjectLinkedOpenHashMap<>();
    final List<Consumer<ServerLevel>> post = new ArrayList<>();
    public final RandomSource random;

    public BuildQueue(long seed) {
        this.random = RandomSource.create(seed);
    }

    public int size() {
        return blocks.size();
    }

    // ------------------------------------------------------------------ single blocks

    public void set(int x, int y, int z, BlockState state) {
        blocks.put(BlockPos.asLong(x, y, z), state);
    }

    public void set(int x, int y, int z, Block block) {
        set(x, y, z, block.defaultBlockState());
    }

    public void set(BlockPos p, BlockState state) {
        set(p.getX(), p.getY(), p.getZ(), state);
    }

    public BlockState get(int x, int y, int z) {
        return blocks.get(BlockPos.asLong(x, y, z));
    }

    /** Only place if nothing has been planned here yet. */
    public void setIfEmpty(int x, int y, int z, BlockState state) {
        blocks.putIfAbsent(BlockPos.asLong(x, y, z), state);
    }

    // ------------------------------------------------------------------ shapes

    public void fill(int x1, int y1, int z1, int x2, int y2, int z2, BlockState state) {
        for (int x = Math.min(x1, x2); x <= Math.max(x1, x2); x++)
            for (int y = Math.min(y1, y2); y <= Math.max(y1, y2); y++)
                for (int z = Math.min(z1, z2); z <= Math.max(z1, z2); z++)
                    set(x, y, z, state);
    }

    public void fill(int x1, int y1, int z1, int x2, int y2, int z2, Block block) {
        fill(x1, y1, z1, x2, y2, z2, block.defaultBlockState());
    }

    public void air(int x1, int y1, int z1, int x2, int y2, int z2) {
        fill(x1, y1, z1, x2, y2, z2, Blocks.AIR.defaultBlockState());
    }

    /** Four walls (no floor or roof). */
    public void walls(int x1, int y1, int z1, int x2, int y2, int z2, BlockState state) {
        int ax = Math.min(x1, x2), bx = Math.max(x1, x2), az = Math.min(z1, z2), bz = Math.max(z1, z2);
        fill(ax, y1, az, bx, y2, az, state);
        fill(ax, y1, bz, bx, y2, bz, state);
        fill(ax, y1, az, ax, y2, bz, state);
        fill(bx, y1, az, bx, y2, bz, state);
    }

    public void walls(int x1, int y1, int z1, int x2, int y2, int z2, Block block) {
        walls(x1, y1, z1, x2, y2, z2, block.defaultBlockState());
    }

    /** Fill with a random pick from a palette (for mossy/cracked stone brick walls etc). */
    public void fillMix(int x1, int y1, int z1, int x2, int y2, int z2, BlockState... palette) {
        for (int x = Math.min(x1, x2); x <= Math.max(x1, x2); x++)
            for (int y = Math.min(y1, y2); y <= Math.max(y1, y2); y++)
                for (int z = Math.min(z1, z2); z <= Math.max(z1, z2); z++)
                    set(x, y, z, palette[random.nextInt(palette.length)]);
    }

    public BlockState pick(BlockState... palette) {
        return palette[random.nextInt(palette.length)];
    }

    // ------------------------------------------------------------------ multi-block things

    public void door(int x, int y, int z, Block door, Direction facing, boolean rightHinge) {
        BlockState s = door.defaultBlockState().setValue(DoorBlock.FACING, facing)
                .setValue(DoorBlock.HINGE, rightHinge ? DoorHingeSide.RIGHT : DoorHingeSide.LEFT);
        set(x, y, z, s.setValue(DoorBlock.HALF, DoubleBlockHalf.LOWER));
        set(x, y + 1, z, s.setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER));
    }

    /** Bed with its foot at (x,y,z) and its head one block toward {@code facing}. */
    public void bed(int x, int y, int z, Block bed, Direction facing) {
        BlockState s = bed.defaultBlockState().setValue(BedBlock.FACING, facing);
        set(x, y, z, s.setValue(BedBlock.PART, BedPart.FOOT));
        set(x + facing.getStepX(), y, z + facing.getStepZ(), s.setValue(BedBlock.PART, BedPart.HEAD));
    }

    /** A column of ladders from y1 to y2 facing away from the wall they hang on. */
    public void ladder(int x, int y1, int y2, int z, Direction facing) {
        BlockState s = Blocks.LADDER.defaultBlockState().setValue(LadderBlock.FACING, facing);
        for (int y = y1; y <= y2; y++) set(x, y, z, s);
    }

    public BlockState trapdoor(Block block, Direction facing, boolean top, boolean open) {
        return block.defaultBlockState().setValue(TrapDoorBlock.FACING, facing)
                .setValue(TrapDoorBlock.HALF, top ? Half.TOP : Half.BOTTOM).setValue(TrapDoorBlock.OPEN, open);
    }

    public static BlockState stairs(Block block, Direction facing, boolean upsideDown) {
        return block.defaultBlockState().setValue(StairBlock.FACING, facing)
                .setValue(StairBlock.HALF, upsideDown ? Half.TOP : Half.BOTTOM);
    }

    public static BlockState leaves(Block block) {
        return block.defaultBlockState().setValue(LeavesBlock.PERSISTENT, true);
    }

    // ------------------------------------------------------------------ block entities & entities

    public void chest(int x, int y, int z, Direction facing, String name, ItemStack... items) {
        BlockPos pos = new BlockPos(x, y, z);
        set(pos, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, facing));
        post.add(level -> {
            BlockEntity be = level.getBlockEntity(pos);
            if (be instanceof ChestBlockEntity chest) {
                if (name != null) chest.setCustomName(Component.literal(name));
                Container c = chest;
                for (int i = 0; i < items.length && i < c.getContainerSize(); i++) {
                    c.setItem(i, items[i].copy());
                }
                chest.setChanged();
            }
        });
    }

    public void wallSign(int x, int y, int z, Block sign, Direction facing, DyeColor color, boolean glow, String... lines) {
        BlockPos pos = new BlockPos(x, y, z);
        set(pos, sign.defaultBlockState().setValue(WallSignBlock.FACING, facing));
        post.add(level -> writeSign(level, pos, color, glow, lines));
    }

    public void standingSign(int x, int y, int z, BlockState state, DyeColor color, boolean glow, String... lines) {
        BlockPos pos = new BlockPos(x, y, z);
        set(pos, state);
        post.add(level -> writeSign(level, pos, color, glow, lines));
    }

    private static void writeSign(ServerLevel level, BlockPos pos, DyeColor color, boolean glow, String[] lines) {
        if (level.getBlockEntity(pos) instanceof SignBlockEntity sign) {
            SignText text = new SignText();
            for (int i = 0; i < 4 && i < lines.length; i++) {
                text = text.setMessage(i, Component.literal(lines[i]));
            }
            text = text.setColor(color).setHasGlowingText(glow);
            sign.setText(text, true);
            sign.setWaxed(true);
            sign.setChanged();
            BlockState s = level.getBlockState(pos);
            level.sendBlockUpdated(pos, s, s, Block.UPDATE_ALL);
        }
    }

    /** Item frame hanging on the wall block behind it, showing an item. */
    public void itemFrame(int x, int y, int z, Direction facing, ItemStack item) {
        BlockPos pos = new BlockPos(x, y, z);
        post.add(level -> {
            ItemFrame frame = new ItemFrame(level, pos, facing);
            frame.setItem(item.copy(), false);
            frame.setInvulnerable(true);
            if (frame.survives()) {
                level.addFreshEntity(frame);
            }
        });
    }

    public void entity(Consumer<ServerLevel> spawner) {
        post.add(spawner);
    }

    public void post(Consumer<ServerLevel> action) {
        post.add(action);
    }
}
