package com.echoesinthedark.turtlepower.world;

import com.echoesinthedark.turtlepower.registry.ModBlocks;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.world.BuildingBuilder.Spec;
import com.echoesinthedark.turtlepower.world.BuildingBuilder.Style;
import net.minecraft.core.Direction;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * TCRI (Techno Cosmic Research Institute): a shiny glass skyscraper that is secretly the Kraang's
 * headquarters. The two-storey lobby is a Kraang lab full of mutagen tanks with a portal at the back,
 * which is where you fight Kraang Prime.
 */
public final class TcriBuilder {
    private TcriBuilder() {}

    public static void build(BuildQueue q, Layout L, int x1, int z1, int x2, int z2) {
        Spec s = new Spec(x1, z1, x2, z2, 16).style(Style.GLASS).front(Direction.SOUTH).lobby(2);
        BuildingBuilder.build(q, L, s);
        int y0 = L.y0;
        int top = s.roofY(L);

        // Big purple letters near the top and over the entrance.
        BlockState ink = Blocks.PURPLE_CONCRETE.defaultBlockState();
        BuildingBuilder.frontLetters(q, L, s, "TCRI", top - 2, ink, Blocks.WHITE_CONCRETE.defaultBlockState());
        BuildingBuilder.frontLetters(q, L, s, "TCRI", y0 + 15, ink, Blocks.WHITE_CONCRETE.defaultBlockState());

        // Wide open entrance instead of the normal doors.
        int mid = BuildingBuilder.frontLength(s) / 2;
        for (int a = mid - 2; a <= mid + 1; a++) {
            int x = BuildingBuilder.frontX(s, a, 0), z = BuildingBuilder.frontZ(s, a, 0);
            q.air(L.x(x), y0 + 1, L.z(z), L.x(x), y0 + 4, L.z(z));
            int cx = BuildingBuilder.frontX(s, a, 1), cz = BuildingBuilder.frontZ(s, a, 1);
            q.set(L.x(cx), y0 + 4, L.z(cz), Blocks.AIR.defaultBlockState());
            q.set(L.x(cx), y0 + 3, L.z(cz), Blocks.AIR.defaultBlockState());
        }
        BuildingBuilder.frontSign(q, L, s, mid + 3, y0 + 3, DyeColor.PURPLE,
                "TCRI", "Techno Cosmic", "Research Inst.", "NO TURTLES");

        // --- The Kraang lab in the lobby ---
        int lx1 = x1 + 1, lx2 = x2 - 1, lz1 = z1 + 1, lz2 = z2 - 1;
        int cx = (x1 + x2) / 2;
        for (int x = lx1; x <= lx2; x++) {
            for (int z = lz1; z <= lz2; z++) {
                boolean grid = x % 4 == 0 || z % 4 == 0;
                q.set(L.x(x), y0, L.z(z), grid ? ModBlocks.KRAANG_PANEL.get().defaultBlockState() : Blocks.PURPLE_TERRACOTTA.defaultBlockState());
            }
        }
        // Rows of mutagen tanks along both side walls.
        for (int z = lz1 + 2; z <= lz2 - 4; z += 3) {
            for (int x : new int[]{lx1, lx2}) {
                q.set(L.x(x), y0 + 1, L.z(z), Blocks.IRON_BLOCK.defaultBlockState());
                q.set(L.x(x), y0 + 2, L.z(z), ModBlocks.MUTAGEN_TANK.get().defaultBlockState());
                q.set(L.x(x), y0 + 3, L.z(z), ModBlocks.MUTAGEN_TANK.get().defaultBlockState());
                q.set(L.x(x), y0 + 4, L.z(z), ModBlocks.MUTAGEN_TANK.get().defaultBlockState());
                q.set(L.x(x), y0 + 5, L.z(z), Blocks.IRON_BLOCK.defaultBlockState());
            }
        }
        // Kraang wall panels up the back wall.
        q.fill(L.x(x1 + 3), y0 + 1, L.z(lz1), L.x(lx2), y0 + 7, L.z(lz1), ModBlocks.KRAANG_PANEL.get().defaultBlockState());
        // The portal at the back.
        int pz = lz1 + 1;
        for (int x = cx - 3; x <= cx + 3; x++) {
            for (int y = y0 + 1; y <= y0 + 7; y++) {
                boolean frame = x == cx - 3 || x == cx + 3 || y == y0 + 1 || y == y0 + 7;
                q.set(L.x(x), y, L.z(pz), frame ? Blocks.CRYING_OBSIDIAN.defaultBlockState() : Blocks.PURPLE_STAINED_GLASS.defaultBlockState());
            }
        }
        q.set(L.x(cx - 4), y0 + 1, L.z(pz), Blocks.END_ROD.defaultBlockState());
        q.set(L.x(cx + 4), y0 + 1, L.z(pz), Blocks.END_ROD.defaultBlockState());
        // Mutagen spills on the floor.
        for (int k = 0; k < 10; k++) {
            int x = lx1 + 2 + q.random.nextInt(lx2 - lx1 - 3), z = lz1 + 4 + q.random.nextInt(lz2 - lz1 - 8);
            q.set(L.x(x), y0 + 1, L.z(z), ModBlocks.MUTAGEN_OOZE.get().defaultBlockState());
        }
        // Kraang consoles.
        for (int x = cx - 6; x <= cx + 6; x += 12) {
            q.set(L.x(x), y0 + 1, L.z(lz1 + 5), ModBlocks.KRAANG_PANEL.get().defaultBlockState());
            q.set(L.x(x), y0 + 2, L.z(lz1 + 5), Blocks.MAGENTA_STAINED_GLASS.defaultBlockState());
        }
        // Loot: Kraang crates with mutagen.
        q.chest(L.x(lx1 + 1), y0 + 1, L.z(lz1 + 1), Direction.SOUTH, "Kraang Crate",
                new ItemStack(ModItems.MUTAGEN_CANISTER.get(), 3), new ItemStack(ModItems.KRAANG_BLASTER.get()));
        q.chest(L.x(lx2 - 1), y0 + 1, L.z(lz1 + 1), Direction.SOUTH, "Kraang Crate",
                new ItemStack(ModItems.MUTAGEN_CANISTER.get(), 3), new ItemStack(ModItems.SMOKE_BOMB.get(), 4));
        // Satellite dish on the roof.
        int dishX = cx, dishZ = (z1 + z2) / 2;
        q.fill(L.x(dishX), top + 1, L.z(dishZ), L.x(dishX), top + 5, L.z(dishZ), Blocks.IRON_BARS);
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                if (dx * dx + dz * dz <= 5) {
                    q.set(L.x(dishX + dx), top + 6, L.z(dishZ + dz), ModBlocks.KRAANG_PANEL.get().defaultBlockState());
                }
            }
        }
        q.set(L.x(dishX), top + 7, L.z(dishZ), Blocks.END_ROD.defaultBlockState());

        L.poi("tcri_door", cx, y0 + 1, z2 + 2);
        L.poi("tcri_boss", cx, y0 + 1, (z1 + z2) / 2);
        L.poi("tcri_portal", cx, y0 + 1, pz + 2);
    }
}
