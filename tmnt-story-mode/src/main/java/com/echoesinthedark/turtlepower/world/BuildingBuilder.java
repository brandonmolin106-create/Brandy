package com.echoesinthedark.turtlepower.world;

import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * New York buildings: brick walk-ups with fire escapes and water towers, brownstones, glass offices,
 * art deco towers and warehouses. Every building is hollow with lit floors, a ladder inside that goes
 * up to a roof hatch, and a door on its front.
 */
public final class BuildingBuilder {
    private BuildingBuilder() {}

    public enum Style {
        BRICK(Blocks.BRICKS, Blocks.STONE_BRICKS, Blocks.GLASS_PANE, Blocks.STONE_BRICKS),
        BROWNSTONE(Blocks.MUD_BRICKS, Blocks.DARK_OAK_PLANKS, Blocks.GLASS_PANE, Blocks.PACKED_MUD),
        OFFICE(Blocks.LIGHT_GRAY_CONCRETE, Blocks.SMOOTH_STONE, Blocks.LIGHT_BLUE_STAINED_GLASS_PANE, Blocks.SMOOTH_STONE),
        DECO(Blocks.SMOOTH_SANDSTONE, Blocks.CUT_SANDSTONE, Blocks.GRAY_STAINED_GLASS_PANE, Blocks.CHISELED_SANDSTONE),
        WAREHOUSE(Blocks.RED_TERRACOTTA, Blocks.POLISHED_ANDESITE, Blocks.IRON_BARS, Blocks.POLISHED_ANDESITE),
        GLASS(Blocks.WHITE_CONCRETE, Blocks.SMOOTH_QUARTZ, Blocks.LIGHT_BLUE_STAINED_GLASS_PANE, Blocks.SMOOTH_QUARTZ);

        final Block wall, trim, window, parapet;

        Style(Block wall, Block trim, Block window, Block parapet) {
            this.wall = wall;
            this.trim = trim;
            this.window = window;
            this.parapet = parapet;
        }
    }

    /** Everything needed to build one building. Coordinates are relative to the layout origin. */
    public static class Spec {
        int x1, z1, x2, z2, floors;
        Style style = Style.BRICK;
        Direction front = Direction.SOUTH;
        boolean fireEscape;
        boolean waterTower;
        boolean shopFront;
        /** Number of floors (from the bottom) that are merged into one tall lobby. */
        int lobbyFloors = 1;
        boolean spire;

        public Spec(int x1, int z1, int x2, int z2, int floors) {
            this.x1 = x1;
            this.z1 = z1;
            this.x2 = x2;
            this.z2 = z2;
            this.floors = floors;
        }

        public Spec style(Style s) { style = s; return this; }
        public Spec front(Direction d) { front = d; return this; }
        public Spec fireEscape() { fireEscape = true; return this; }
        public Spec waterTower() { waterTower = true; return this; }
        public Spec shop() { shopFront = true; return this; }
        public Spec lobby(int n) { lobbyFloors = n; return this; }
        public Spec spire() { spire = true; return this; }

        public int roofY(Layout L) { return L.y0 + floors * 4; }
    }

    public static void build(BuildQueue q, Layout L, Spec s) {
        int y0 = L.y0;
        int top = s.roofY(L);
        BlockState wall = s.style.wall.defaultBlockState();
        BlockState trim = s.style.trim.defaultBlockState();
        BlockState window = s.style.window.defaultBlockState();

        // Clear the volume and lay the ground floor.
        q.air(L.x(s.x1), y0 + 1, L.z(s.z1), L.x(s.x2), top, L.z(s.z2));
        q.fill(L.x(s.x1), y0, L.z(s.z1), L.x(s.x2), y0, L.z(s.z2), Blocks.POLISHED_ANDESITE);

        // Outer walls with window grid.
        for (int x = s.x1; x <= s.x2; x++) {
            for (int z = s.z1; z <= s.z2; z++) {
                boolean edgeX = x == s.x1 || x == s.x2;
                boolean edgeZ = z == s.z1 || z == s.z2;
                if (!edgeX && !edgeZ) continue;
                boolean corner = edgeX && edgeZ;
                int t = edgeZ ? x - s.x1 : z - s.z1;
                boolean pillar = corner || t % 3 == 0;
                for (int y = y0 + 1; y <= top; y++) {
                    int row = (y - y0 - 1) % 4; // 0 = sill, 1-2 = window, 3 = floor band
                    int floor = (y - y0 - 1) / 4;
                    BlockState b;
                    if (pillar) {
                        b = trim;
                    } else if (row == 3) {
                        b = trim;
                    } else if (row == 0 && !(floor == 0 && s.shopFront)) {
                        b = wall;
                    } else {
                        b = window;
                    }
                    q.set(L.x(x), y, L.z(z), b);
                }
                // Parapet around the roof.
                q.set(L.x(x), top + 1, L.z(z), s.style.parapet.defaultBlockState());
            }
        }

        // Floors with lights, and the roof.
        for (int k = 1; k <= s.floors; k++) {
            if (k < s.lobbyFloors) continue;
            int y = y0 + 4 * k;
            q.fill(L.x(s.x1 + 1), y, L.z(s.z1 + 1), L.x(s.x2 - 1), y, L.z(s.z2 - 1),
                    k == s.floors ? Blocks.SMOOTH_STONE : Blocks.SPRUCE_PLANKS);
            for (int x = s.x1 + 3; x < s.x2 - 1; x += 6) {
                for (int z = s.z1 + 3; z < s.z2 - 1; z += 6) {
                    q.set(L.x(x), y, L.z(z), Blocks.SEA_LANTERN.defaultBlockState());
                }
            }
        }
        // Ground floor lights (in the lobby ceiling if it is tall).
        int lobbyCeil = y0 + 4 * s.lobbyFloors;
        for (int x = s.x1 + 3; x < s.x2 - 1; x += 6) {
            for (int z = s.z1 + 3; z < s.z2 - 1; z += 6) {
                q.set(L.x(x), lobbyCeil, L.z(z), Blocks.SEA_LANTERN.defaultBlockState());
            }
        }

        // Ladder inside, up to a roof hatch.
        int lx = s.x1 + 2, lz = s.z1 + 1;
        q.fill(L.x(lx - 1), y0 + 1, L.z(lz), L.x(lx - 1), top - 1, L.z(lz), trim);
        q.ladder(L.x(lx), y0 + 1, top - 1, L.z(lz), Direction.EAST);
        q.set(L.x(lx), top, L.z(lz), q.trapdoor(Blocks.SPRUCE_TRAPDOOR, Direction.EAST, true, false));

        // Front door.
        door(q, L, s);

        if (s.fireEscape) fireEscape(q, L, s);
        if (s.waterTower) waterTower(q, L, s.x2 - 5, s.z2 - 5, top + 1);
        roofStuff(q, L, s, top + 1);
        if (s.spire) spire(q, L, s, top + 1);
    }

    /** Local frame for the front face: returns world x/z for (along a, outward d). */
    private static int fx(Spec s, int a, int d) {
        return switch (s.front) {
            case NORTH -> s.x1 + a;
            case SOUTH -> s.x1 + a;
            case WEST -> s.x1 - d;
            default -> s.x2 + d; // EAST
        };
    }

    private static int fz(Spec s, int a, int d) {
        return switch (s.front) {
            case NORTH -> s.z1 - d;
            case SOUTH -> s.z2 + d;
            default -> s.z1 + a; // EAST / WEST
        };
    }

    private static int faceLength(Spec s) {
        return (s.front.getAxis() == Direction.Axis.Z ? s.x2 - s.x1 : s.z2 - s.z1) + 1;
    }

    /** Along-face direction as a world direction (increasing a). */
    private static Direction along(Spec s) {
        return s.front.getAxis() == Direction.Axis.Z ? Direction.EAST : Direction.SOUTH;
    }

    private static void door(BuildQueue q, Layout L, Spec s) {
        int mid = faceLength(s) / 2;
        int y0 = L.y0;
        for (int a = mid - 1; a <= mid; a++) {
            q.air(L.x(fx(s, a, 0)), y0 + 1, L.z(fz(s, a, 0)), L.x(fx(s, a, 0)), y0 + 3, L.z(fz(s, a, 0)));
        }
        Direction facing = s.front.getOpposite();
        q.door(L.x(fx(s, mid - 1, 0)), y0 + 1, L.z(fz(s, mid - 1, 0)), Blocks.SPRUCE_DOOR, facing, false);
        q.door(L.x(fx(s, mid, 0)), y0 + 1, L.z(fz(s, mid, 0)), Blocks.SPRUCE_DOOR, facing, true);
        q.set(L.x(fx(s, mid - 1, 0)), y0 + 3, L.z(fz(s, mid - 1, 0)), s.style.trim.defaultBlockState());
        q.set(L.x(fx(s, mid, 0)), y0 + 3, L.z(fz(s, mid, 0)), s.style.trim.defaultBlockState());
        // Little canopy with a lamp over the door.
        for (int a = mid - 1; a <= mid; a++) {
            q.set(L.x(fx(s, a, 1)), y0 + 4, L.z(fz(s, a, 1)), Blocks.SMOOTH_STONE_SLAB.defaultBlockState());
        }
        q.set(L.x(fx(s, mid, 1)), y0 + 3, L.z(fz(s, mid, 1)), Blocks.LANTERN.defaultBlockState()
                .setValue(net.minecraft.world.level.block.LanternBlock.HANGING, true));
    }

    /** Zig-zag iron fire escape on the front of the building, climbable from the street to the roof. */
    private static void fireEscape(BuildQueue q, Layout L, Spec s) {
        int len = faceLength(s);
        int a0 = (len / 2) + 3;
        a0 = a0 - (a0 % 3); // start on a pillar column so the ladders have a solid wall behind them
        if (a0 + 4 >= len - 1) a0 = 3;
        int y0 = L.y0;
        BlockState grate = q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.NORTH, true, false);
        BlockState bars = Blocks.IRON_BARS.defaultBlockState();
        for (int k = 1; k < s.floors; k++) {
            int y = y0 + 4 * k;
            for (int a = a0; a <= a0 + 4; a++) {
                for (int d = 1; d <= 3; d++) {
                    boolean hole = a == a0 && d == 1;
                    q.set(L.x(fx(s, a, d)), y, L.z(fz(s, a, d)), hole ? Blocks.AIR.defaultBlockState() : grate);
                    boolean rail = d == 3 || a == a0 + 4 || (a == a0 && d > 1);
                    q.set(L.x(fx(s, a, d)), y + 1, L.z(fz(s, a, d)), rail ? bars : Blocks.AIR.defaultBlockState());
                    q.air(L.x(fx(s, a, d)), y + 2, L.z(fz(s, a, d)), L.x(fx(s, a, d)), y + 3, L.z(fz(s, a, d)));
                }
            }
        }
        // One long ladder column up the pillar, from the sidewalk to the parapet.
        q.fill(L.x(fx(s, a0, 0)), y0 + 1, L.z(fz(s, a0, 0)), L.x(fx(s, a0, 0)), s.roofY(L) + 1, L.z(fz(s, a0, 0)), s.style.trim);
        q.ladder(L.x(fx(s, a0, 1)), y0 + 1, s.roofY(L) + 1, L.z(fz(s, a0, 1)), s.front);
        L.poiAdd("fire_escapes", fx(s, a0, 1), y0 + 1, fz(s, a0, 1));
    }

    public static void waterTower(BuildQueue q, Layout L, int cx, int cz, int y) {
        BlockState fence = Blocks.SPRUCE_FENCE.defaultBlockState();
        for (int[] leg : new int[][]{{-1, -1}, {1, -1}, {-1, 1}, {1, 1}}) {
            q.fill(L.x(cx + leg[0]), y, L.z(cz + leg[1]), L.x(cx + leg[0]), y + 2, L.z(cz + leg[1]), fence);
        }
        for (int dy = 3; dy <= 7; dy++) {
            for (int dx = -2; dx <= 2; dx++) {
                for (int dz = -2; dz <= 2; dz++) {
                    if (dx * dx + dz * dz <= 5) {
                        Block b = dy == 5 ? Blocks.DARK_OAK_PLANKS : Blocks.SPRUCE_PLANKS;
                        q.set(L.x(cx + dx), y + dy, L.z(cz + dz), b.defaultBlockState());
                    }
                }
            }
        }
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                q.set(L.x(cx + dx), y + 8, L.z(cz + dz), Blocks.SPRUCE_SLAB.defaultBlockState());
            }
        }
        q.set(L.x(cx), y + 8, L.z(cz), Blocks.SPRUCE_PLANKS.defaultBlockState());
        q.set(L.x(cx), y + 9, L.z(cz), Blocks.SPRUCE_SLAB.defaultBlockState());
    }

    private static void roofStuff(BuildQueue q, Layout L, Spec s, int y) {
        // Air conditioning units and a vent.
        int ax = s.x1 + 4, az = s.z2 - 4;
        q.fill(L.x(ax), y, L.z(az), L.x(ax + 1), y, L.z(az + 1), Blocks.SMOOTH_STONE);
        q.set(L.x(ax), y + 1, L.z(az), q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.NORTH, false, false));
        q.set(L.x(ax + 1), y + 1, L.z(az + 1), q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.NORTH, false, false));
        q.set(L.x(s.x2 - 3), y, L.z(s.z1 + 3), Blocks.CAULDRON.defaultBlockState());
        q.set(L.x(s.x1 + 6), y, L.z(s.z1 + 6), Blocks.LIGHTNING_ROD.defaultBlockState());
        // Roof lights so the Kraang have to fight you in the light.
        q.set(L.x((s.x1 + s.x2) / 2), y - 1, L.z((s.z1 + s.z2) / 2), Blocks.SEA_LANTERN.defaultBlockState());
    }

    private static void spire(BuildQueue q, Layout L, Spec s, int y) {
        int cx = (s.x1 + s.x2) / 2, cz = (s.z1 + s.z2) / 2;
        // Two stepped setbacks and a needle.
        for (int step = 0; step < 3; step++) {
            int r = 8 - step * 3;
            int h = 5;
            for (int dy = 0; dy < h; dy++) {
                int yy = y + step * h + dy;
                for (int dx = -r; dx <= r; dx++) {
                    for (int dz = -r; dz <= r; dz++) {
                        boolean edge = Math.abs(dx) == r || Math.abs(dz) == r;
                        if (edge) {
                            boolean win = (dx + dz) % 2 == 0 && dy % 2 == 1;
                            q.set(L.x(cx + dx), yy, L.z(cz + dz), win ? s.style.window.defaultBlockState() : s.style.trim.defaultBlockState());
                        }
                    }
                }
            }
            q.fill(L.x(cx - r), y + step * h + h, L.z(cz - r), L.x(cx + r), y + step * h + h, L.z(cz + r), s.style.trim);
        }
        int needle = y + 15;
        q.fill(L.x(cx), needle + 1, L.z(cz), L.x(cx), needle + 8, L.z(cz), Blocks.IRON_BARS);
        q.set(L.x(cx), needle + 9, L.z(cz), Blocks.LIGHTNING_ROD.defaultBlockState());
        q.set(L.x(cx), needle, L.z(cz), Blocks.SEA_LANTERN.defaultBlockState());
    }

    /** A wall sign on the front face of the building at (along a, height y). */
    public static void frontSign(BuildQueue q, Layout L, Spec s, int a, int y, net.minecraft.world.item.DyeColor color, String... lines) {
        q.wallSign(L.x(fx(s, a, 1)), y, L.z(fz(s, a, 1)), Blocks.DARK_OAK_WALL_SIGN, s.front, color, true, lines);
    }

    /** Draw big block letters on the front face, centred. */
    public static void frontLetters(BuildQueue q, Layout L, Spec s, String text, int yTop, BlockState ink, BlockState background) {
        int len = faceLength(s);
        int w = BlockFont.width(text);
        int a0 = (len - w) / 2;
        Direction right = along(s);
        // When the front faces north or east, "along" runs right-to-left for someone looking at it.
        boolean flip = s.front == Direction.NORTH || s.front == Direction.EAST;
        if (background != null) {
            for (int a = a0 - 1; a <= a0 + w; a++) {
                for (int y = yTop - 5; y <= yTop + 1; y++) {
                    q.set(L.x(fx(s, a, 0)), y, L.z(fz(s, a, 0)), background);
                }
            }
        }
        if (flip) {
            int startA = a0 + w - 1;
            BlockFont.draw(q, text, L.x(fx(s, startA, 0)), yTop, L.z(fz(s, startA, 0)), right.getOpposite(), ink);
        } else {
            BlockFont.draw(q, text, L.x(fx(s, a0, 0)), yTop, L.z(fz(s, a0, 0)), right, ink);
        }
    }

    /** World (relative) x of a point on the front face. */
    public static int frontX(Spec s, int a, int d) {
        return fx(s, a, d);
    }

    public static int frontZ(Spec s, int a, int d) {
        return fz(s, a, d);
    }

    public static int frontLength(Spec s) {
        return faceLength(s);
    }
}
