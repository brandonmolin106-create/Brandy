package com.echoesinthedark.echostrike.game;

import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;

/** Drops a chest full of Echo Strike loot on the ground, with a beacon-ish marker so you can spot it. */
public final class LootCrates {
    private LootCrates() {}

    public static void place(ServerLevel level, BlockPos where, RandomSource rand) {
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, where.getX(), where.getZ());
        BlockPos pos = new BlockPos(where.getX(), y, where.getZ());
        if (!level.getBlockState(pos).isAir() && !level.getBlockState(pos).canBeReplaced()) {
            pos = pos.above();
        }
        level.setBlock(pos, Blocks.CHEST.defaultBlockState(), 3);
        // A little red lamp pillar on top so crates are visible from a distance.
        level.setBlock(pos.above(), Blocks.REDSTONE_LAMP.defaultBlockState().setValue(net.minecraft.world.level.block.RedstoneLampBlock.LIT, true), 3);
        BlockEntity be = level.getBlockEntity(pos);
        if (!(be instanceof ChestBlockEntity chest)) return;
        fill(chest, rand);
    }

    public static void fill(ChestBlockEntity chest, RandomSource rand) {
        GunType[] guns = GunType.values();
        int slots = chest.getContainerSize();
        int gunCount = 1 + rand.nextInt(2);
        for (int i = 0; i < gunCount; i++) {
            GunType g = guns[rand.nextInt(guns.length)];
            if (g == GunType.AWM && rand.nextBoolean()) g = GunType.M4A1; // the AWM is a little rarer
            chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.gunFor(g)));
            chest.setItem(rand.nextInt(slots), new ItemStack(g.ammo.get(), 20 + rand.nextInt(30)));
        }
        chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.LIGHT_AMMO.get(), 12 + rand.nextInt(24)));
        if (rand.nextFloat() < 0.6F) chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.MEDKIT.get(), 1 + rand.nextInt(2)));
        if (rand.nextFloat() < 0.6F) chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.ARMOR_PLATE.get(), 1 + rand.nextInt(3)));
        if (rand.nextFloat() < 0.4F) chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.FRAG_GRENADE.get(), 1 + rand.nextInt(3)));
        if (rand.nextFloat() < 0.25F) chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.STRIKE_VEST.get()));
        if (rand.nextFloat() < 0.2F) chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.STRIKE_HELMET.get()));
        if (rand.nextFloat() < 0.3F) chest.setItem(rand.nextInt(slots), new ItemStack(ModItems.COMBAT_KNIFE.get()));
        chest.setChanged();
    }
}
