package com.echoesinthedark.turtlepower.world;

import com.echoesinthedark.turtlepower.registry.ModBlocks;
import net.minecraft.core.Direction;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;

import static com.echoesinthedark.turtlepower.world.Layout.CITY_HALF;
import static com.echoesinthedark.turtlepower.world.Layout.STREETS;

/**
 * The sewer network: an arched brick tunnel under every street, with walkways on both sides of a
 * water channel, hanging lanterns, copper pipes, grates you can cross on, and ladders up to manhole
 * covers in the road.
 *
 * Cross section (u = distance from the street's centre line):
 * <pre>
 *   u: -5 -4 -3 -2 -1  0 +1 +2 +3 +4 +5
 *  ys+6 ###############################   ceiling
 *  ys+5 #  \                       /  #   arch corners, lanterns
 *  ys+1 #   walkway      channel   walk#
 *  ys   # [walk ][walk]  (air)  [walk]#   walkways (you walk on top)
 *  ys-1 #####  ~~water~~   #############
 *  ys-2 ###############################   floor
 * </pre>
 */
public final class SewerBuilder {
    private SewerBuilder() {}

    private static final BlockState BRICK = Blocks.STONE_BRICKS.defaultBlockState();
    private static final BlockState MOSSY = Blocks.MOSSY_STONE_BRICKS.defaultBlockState();
    private static final BlockState CRACKED = Blocks.CRACKED_STONE_BRICKS.defaultBlockState();
    private static final BlockState WALK = Blocks.POLISHED_ANDESITE.defaultBlockState();
    private static final BlockState WATER = Blocks.WATER.defaultBlockState();
    private static final BlockState AIR = Blocks.AIR.defaultBlockState();

    public static void build(BuildQueue q, Layout L) {
        int ys = L.ys();
        // Pass 1: solid shells for every tunnel.
        for (int c : STREETS) {
            for (int a = -CITY_HALF - 1; a <= CITY_HALF + 1; a++) {
                for (int u = -5; u <= 5; u++) {
                    for (int y = ys - 2; y <= ys + 6; y++) {
                        BlockState s = q.pick(BRICK, BRICK, BRICK, MOSSY, CRACKED);
                        q.set(L.x(c + u), y, L.z(a), s);   // north-south tunnel under x = c
                        q.set(L.x(a), y, L.z(c + u), s);   // east-west tunnel under z = c
                    }
                }
            }
        }
        // Pass 2: hollow them out.
        for (int c : STREETS) {
            for (int a = -CITY_HALF; a <= CITY_HALF; a++) {
                carveSlice(q, L, true, c, a);
                carveSlice(q, L, false, c, a);
            }
        }
        // Pass 3: details, but not inside the junctions.
        for (int c : STREETS) {
            for (int a = -CITY_HALF; a <= CITY_HALF; a++) {
                if (nearCrossing(a)) continue;
                detailSlice(q, L, true, c, a);
                detailSlice(q, L, false, c, a);
            }
        }
        // Pass 4: junction chambers.
        for (int cx : STREETS) {
            for (int cz : STREETS) {
                junction(q, L, cx, cz);
            }
        }
        // Pass 5: manholes. East-west tunnels get them near the south wall, north-south near the west wall.
        int[] spots = {-64, -24, 16, 56};
        for (int c : STREETS) {
            for (int m : spots) {
                manholeEW(q, L, m, c);
                manholeNS(q, L, c, m + 4);
            }
        }
        L.poi("main_manhole", 16, L.y0, 4);
        L.poi("sewer_exit_ladder", 16, ys + 1, 3);

        // Signs down in the sewer so you can find your way.
        q.wallSign(L.x(15), ys + 3, L.z(4), Blocks.SPRUCE_WALL_SIGN, Direction.NORTH, DyeColor.LIME, true,
                "EXIT", "^ ^ ^", "Topside", "(ladder)");
        q.wallSign(L.x(9), ys + 3, L.z(4), Blocks.SPRUCE_WALL_SIGN, Direction.NORTH, DyeColor.ORANGE, true,
                "TURTLE LAIR", "keep out!!", "(Mikey made", "this sign)");
    }

    private static boolean nearCrossing(int a) {
        for (int s : STREETS) {
            if (Math.abs(a - s) <= 5) return true;
        }
        return false;
    }

    /** (along, across) to world x/z for either direction. */
    private static int wx(Layout L, boolean ns, int c, int a, int u) {
        return ns ? L.x(c + u) : L.x(a);
    }

    private static int wz(Layout L, boolean ns, int c, int a, int u) {
        return ns ? L.z(a) : L.z(c + u);
    }

    private static void carveSlice(BuildQueue q, Layout L, boolean ns, int c, int a) {
        int ys = L.ys();
        for (int u = -4; u <= 4; u++) {
            int x = wx(L, ns, c, a, u), z = wz(L, ns, c, a, u);
            for (int y = ys + 1; y <= ys + 5; y++) q.set(x, y, z, AIR);
            if (Math.abs(u) <= 1) {
                q.set(x, ys, z, AIR);
                q.set(x, ys - 1, z, WATER);
            } else {
                q.set(x, ys, z, Math.abs(u) == 2 ? BRICK : WALK);
            }
        }
    }

    private static void detailSlice(BuildQueue q, Layout L, boolean ns, int c, int a) {
        int ys = L.ys();
        // Rounded arch corners.
        Direction plus = ns ? Direction.EAST : Direction.SOUTH;
        q.set(wx(L, ns, c, a, 4), ys + 5, wz(L, ns, c, a, 4), BuildQueue.stairs(Blocks.STONE_BRICK_STAIRS, plus, true));
        q.set(wx(L, ns, c, a, -4), ys + 5, wz(L, ns, c, a, -4), BuildQueue.stairs(Blocks.STONE_BRICK_STAIRS, plus.getOpposite(), true));
        // Old copper pipe running along one wall.
        q.set(wx(L, ns, c, a, -4), ys + 3, wz(L, ns, c, a, -4),
                Blocks.WAXED_OXIDIZED_CUT_COPPER_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.TOP));
        // Lanterns every 8 blocks, alternating sides.
        int m = Math.floorMod(a, 16);
        if (m == 0 || m == 8) {
            int u = m == 0 ? 3 : -3;
            q.set(wx(L, ns, c, a, u), ys + 5, wz(L, ns, c, a, u), Blocks.LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, true));
        }
        // Hidden light over the channel between lanterns so nothing spawns in the dark stretches.
        if (m == 4 || m == 12) {
            q.set(wx(L, ns, c, a, 0), ys + 3, wz(L, ns, c, a, 0),
                    Blocks.LIGHT.defaultBlockState().setValue(net.minecraft.world.level.block.LightBlock.LEVEL, 15));
        }
        // Grates to cross the channel.
        if (Math.floorMod(a, 24) == 12) {
            for (int u = -1; u <= 1; u++) {
                q.set(wx(L, ns, c, a, u), ys, wz(L, ns, c, a, u), q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.NORTH, true, false));
            }
        }
        // Spilled mutagen here and there.
        if (q.random.nextInt(70) == 0) {
            int u = q.random.nextBoolean() ? 3 : -3;
            q.set(wx(L, ns, c, a, u), ys + 1, wz(L, ns, c, a, u), ModBlocks.MUTAGEN_OOZE.get().defaultBlockState());
        }
        // A few cobwebs up in the arches.
        if (q.random.nextInt(45) == 0) {
            int u = q.random.nextBoolean() ? 3 : -3;
            q.set(wx(L, ns, c, a, u), ys + 5, wz(L, ns, c, a, u), Blocks.COBWEB.defaultBlockState());
        }
    }

    private static void junction(BuildQueue q, Layout L, int cx, int cz) {
        int ys = L.ys();
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                int x = L.x(cx + dx), z = L.z(cz + dz);
                for (int y = ys + 1; y <= ys + 5; y++) q.set(x, y, z, AIR);
                if (Math.abs(dx) <= 1 || Math.abs(dz) <= 1) {
                    q.set(x, ys - 1, z, WATER);
                    q.set(x, ys, z, q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.NORTH, true, false));
                } else {
                    q.set(x, ys, z, WALK);
                }
            }
        }
        q.set(L.x(cx), ys + 5, L.z(cz), Blocks.LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, true));
        for (int[] d : new int[][]{{3, 3}, {-3, 3}, {3, -3}, {-3, -3}}) {
            q.set(L.x(cx + d[0]), ys + 6, L.z(cz + d[1]), Blocks.SEA_LANTERN.defaultBlockState());
        }
    }

    /** Manhole in an east-west street at x = m, next to the south wall of the tunnel. */
    private static void manholeEW(BuildQueue q, Layout L, int m, int c) {
        int x = L.x(m), z = L.z(c + 4);
        q.ladder(x, L.ys() + 1, L.y0 - 1, z, Direction.NORTH);
        q.set(x, L.y0, z, q.trapdoor(ModBlocks.MANHOLE_COVER.get(), Direction.NORTH, true, false));
        L.poiAdd("manholes", m, L.y0, c + 4);
    }

    /** Manhole in a north-south street at z = m, next to the west wall of the tunnel. */
    private static void manholeNS(BuildQueue q, Layout L, int c, int m) {
        int x = L.x(c - 4), z = L.z(m);
        q.ladder(x, L.ys() + 1, L.y0 - 1, z, Direction.EAST);
        q.set(x, L.y0, z, q.trapdoor(ModBlocks.MANHOLE_COVER.get(), Direction.EAST, true, false));
        L.poiAdd("manholes", c - 4, L.y0, m);
    }
}
