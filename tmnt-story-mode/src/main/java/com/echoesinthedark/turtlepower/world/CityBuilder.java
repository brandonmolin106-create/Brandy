package com.echoesinthedark.turtlepower.world;

import com.echoesinthedark.turtlepower.registry.ModBlocks;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.world.BuildingBuilder.Spec;
import com.echoesinthedark.turtlepower.world.BuildingBuilder.Style;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;

import static com.echoesinthedark.turtlepower.world.Layout.CITY_HALF;
import static com.echoesinthedark.turtlepower.world.Layout.EDGE;
import static com.echoesinthedark.turtlepower.world.Layout.STREETS;

/**
 * A chunk of Manhattan: a 5x5 street grid with crosswalks, taxis, lamps and hydrants, sixteen city
 * blocks of buildings, Antonio's Pizza, Murakami's noodle shop, the TCRI tower (Kraang HQ), a Times
 * Square style plaza and a little Central Park, all surrounded by a harbour seawall.
 */
public final class CityBuilder {
    private CityBuilder() {}

    private static final BlockState ASPHALT = Blocks.GRAY_CONCRETE.defaultBlockState();
    private static final BlockState LINE = Blocks.YELLOW_CONCRETE.defaultBlockState();
    private static final BlockState CROSSWALK = Blocks.WHITE_CONCRETE.defaultBlockState();
    private static final BlockState SIDEWALK = Blocks.SMOOTH_STONE.defaultBlockState();
    private static final BlockState CURB = Blocks.POLISHED_ANDESITE.defaultBlockState();
    private static final BlockState STONE = Blocks.STONE.defaultBlockState();

    public static void build(BuildQueue q, Layout L) {
        ground(q, L);
        streetFurniture(q, L);
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 4; j++) {
                lot(q, L, i, j);
            }
        }
        kraangCrates(q, L);
    }

    // ------------------------------------------------------------------ ground, roads, sidewalks

    static boolean isRoad(int dx, int dz) {
        if (Math.abs(dx) > CITY_HALF || Math.abs(dz) > CITY_HALF) return false;
        for (int c : STREETS) {
            if (Math.abs(dx - c) <= 4 || Math.abs(dz - c) <= 4) return true;
        }
        return false;
    }

    private static int nearestStreet(int v) {
        int best = STREETS[0];
        for (int c : STREETS) if (Math.abs(v - c) < Math.abs(v - best)) best = c;
        return best;
    }

    private static void ground(BuildQueue q, Layout L) {
        int y0 = L.y0;
        for (int dx = -EDGE; dx <= EDGE; dx++) {
            for (int dz = -EDGE; dz <= EDGE; dz++) {
                int x = L.x(dx), z = L.z(dz);
                for (int y = y0 - 4; y < y0; y++) q.set(x, y, z, STONE);
                int ax = Math.abs(dx), az = Math.abs(dz);
                if (ax > 88 || az > 88) {
                    // Seawall.
                    for (int y = y0 - 8; y <= y0; y++) q.set(x, y, z, Blocks.STONE_BRICKS.defaultBlockState());
                    if (ax == 89 || az == 89) {
                        q.set(x, y0 + 1, z, Blocks.STONE_BRICK_WALL.defaultBlockState());
                    }
                    continue;
                }
                if (ax > CITY_HALF || az > CITY_HALF) {
                    // Harbour promenade.
                    q.set(x, y0, z, (dx + dz) % 4 == 0 ? Blocks.POLISHED_ANDESITE.defaultBlockState() : SIDEWALK);
                    continue;
                }
                if (isRoad(dx, dz)) {
                    q.set(x, y0, z, roadSurface(dx, dz));
                } else {
                    // Inside a lot: sidewalk ring (with a curb line) or lot floor.
                    int cx = nearestStreet(dx), cz = nearestStreet(dz);
                    int fromX = Math.abs(dx - cx), fromZ = Math.abs(dz - cz);
                    boolean ring = fromX <= 7 || fromZ <= 7;
                    boolean curb = fromX == 5 || fromZ == 5;
                    q.set(x, y0, z, ring ? (curb ? CURB : SIDEWALK) : STONE);
                }
            }
        }
    }

    private static BlockState roadSurface(int dx, int dz) {
        boolean ns = false, ew = false;
        int cns = 0, cew = 0;
        for (int c : STREETS) {
            if (Math.abs(dx - c) <= 4) { ns = true; cns = c; }
            if (Math.abs(dz - c) <= 4) { ew = true; cew = c; }
        }
        if (ns && ew) {
            return ASPHALT; // intersection
        }
        if (ns) {
            int dzStreet = Math.abs(dz - nearestStreet(dz));
            if (dzStreet >= 5 && dzStreet <= 7) return (dx - cns) % 2 == 0 ? CROSSWALK : ASPHALT;
            return dx == cns ? LINE : ASPHALT;
        }
        int dxStreet = Math.abs(dx - nearestStreet(dx));
        if (dxStreet >= 5 && dxStreet <= 7) return (dz - cew) % 2 == 0 ? CROSSWALK : ASPHALT;
        return dz == cew ? LINE : ASPHALT;
    }

    // ------------------------------------------------------------------ lamps, hydrants, taxis

    private static void streetFurniture(BuildQueue q, Layout L) {
        int y0 = L.y0;
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 4; j++) {
                int x1 = Layout.lotMin(i) + 1, x2 = Layout.lotMax(i) - 1;
                int z1 = Layout.lotMin(j) + 1, z2 = Layout.lotMax(j) - 1;
                // Lamps every 10 blocks along each side, just inside the curb.
                for (int t = 4; t <= 26; t += 11) {
                    lamp(q, L, Layout.lotMin(i) + t, y0 + 1, z1);
                    lamp(q, L, Layout.lotMin(i) + t, y0 + 1, z2);
                    lamp(q, L, x1, y0 + 1, Layout.lotMin(j) + t);
                    lamp(q, L, x2, y0 + 1, Layout.lotMin(j) + t);
                }
                // Traffic lights on two corners.
                trafficLight(q, L, x1, y0 + 1, z1);
                trafficLight(q, L, x2, y0 + 1, z2);
                // A fire hydrant.
                q.set(L.x(x1 + 8), y0 + 1, L.z(z2), Blocks.RED_NETHER_BRICK_WALL.defaultBlockState());
                q.set(L.x(x1 + 8), y0 + 2, L.z(z2), Blocks.RED_CARPET.defaultBlockState());
                // Trash can.
                q.set(L.x(x2), y0 + 1, L.z(z1 + 9), Blocks.CAULDRON.defaultBlockState());
            }
        }
        // Parked yellow taxis along the curbs.
        for (int c : STREETS) {
            for (int s = 0; s < 4; s++) {
                int segStart = STREETS[s] + 8;
                if (q.random.nextInt(3) != 0) {
                    taxi(q, L, c + 2, segStart + 4 + q.random.nextInt(18), true);
                }
                if (q.random.nextInt(3) != 0) {
                    taxi(q, L, segStart + 4 + q.random.nextInt(18), c - 3, false);
                }
            }
        }
    }

    private static void lamp(BuildQueue q, Layout L, int dx, int y, int dz) {
        q.fill(L.x(dx), y, L.z(dz), L.x(dx), y + 2, L.z(dz), Blocks.COBBLED_DEEPSLATE_WALL);
        q.set(L.x(dx), y + 3, L.z(dz), Blocks.LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, false));
    }

    private static void trafficLight(BuildQueue q, Layout L, int dx, int y, int dz) {
        q.fill(L.x(dx), y, L.z(dz), L.x(dx), y + 3, L.z(dz), Blocks.POLISHED_BLACKSTONE_WALL);
        q.set(L.x(dx), y + 4, L.z(dz), Blocks.LIME_STAINED_GLASS.defaultBlockState());
        q.set(L.x(dx), y + 5, L.z(dz), Blocks.YELLOW_STAINED_GLASS.defaultBlockState());
        q.set(L.x(dx), y + 6, L.z(dz), Blocks.RED_STAINED_GLASS.defaultBlockState());
        q.set(L.x(dx), y + 7, L.z(dz), Blocks.BLACK_CONCRETE.defaultBlockState());
    }

    /** A 2x4 yellow cab. {@code alongZ} = pointing north-south. (dx,dz) is one corner. */
    private static void taxi(BuildQueue q, Layout L, int dx, int dz, boolean alongZ) {
        int y = L.y0 + 1;
        for (int a = 0; a < 4; a++) {
            for (int b = 0; b < 2; b++) {
                int x = L.x(alongZ ? dx + b : dx + a);
                int z = L.z(alongZ ? dz + a : dz + b);
                boolean cabin = a == 1 || a == 2;
                q.set(x, y, z, Blocks.YELLOW_CONCRETE.defaultBlockState());
                q.set(x, y + 1, z, cabin ? Blocks.BLACK_STAINED_GLASS.defaultBlockState()
                        : Blocks.YELLOW_CONCRETE.defaultBlockState());
                if (cabin) {
                    q.set(x, y + 2, z, Blocks.YELLOW_CARPET.defaultBlockState());
                }
            }
        }
        // Headlights & the TAXI light on the roof.
        int rx = L.x(alongZ ? dx : dx + 1), rz = L.z(alongZ ? dz + 1 : dz);
        q.set(rx, y + 2, rz, Blocks.WHITE_CARPET.defaultBlockState());
    }

    // ------------------------------------------------------------------ lots

    private static void lot(BuildQueue q, Layout L, int i, int j) {
        int bx1 = Layout.buildMin(i), bx2 = Layout.buildMax(i);
        int bz1 = Layout.buildMin(j), bz2 = Layout.buildMax(j);
        Direction front = j < 2 ? Direction.SOUTH : Direction.NORTH;

        if (i == 1 && j == 1) { antonios(q, L, bx1, bz1, bx2, bz2); return; }
        if (i == 1 && j == 2) { murakamis(q, L, bx1, bz1, bx2, bz2); return; }
        if (i == 3 && j == 0) { TcriBuilder.build(q, L, bx1, bz1, bx2, bz2); return; }
        if (i == 2 && j == 2) { timesSquare(q, L, bx1, bz1, bx2, bz2); return; }
        if (i == 0 && j == 3) { centralPark(q, L, bx1, bz1, bx2, bz2); return; }
        if (i == 2 && j == 1) {
            BuildingBuilder.build(q, L, new Spec(bx1, bz1, bx2, bz2, 13).style(Style.OFFICE).front(front));
            return;
        }

        int kind = q.random.nextInt(5);
        switch (kind) {
            case 0 -> BuildingBuilder.build(q, L, new Spec(bx1, bz1, bx2, bz2, 5 + q.random.nextInt(4))
                    .style(Style.BRICK).front(front).fireEscape().waterTower());
            case 1 -> {
                // Two brownstones with an alley between them.
                int mid = bx1 + 11;
                BuildingBuilder.build(q, L, new Spec(bx1, bz1, mid, bz2, 4 + q.random.nextInt(2))
                        .style(Style.BROWNSTONE).front(front).fireEscape());
                BuildingBuilder.build(q, L, new Spec(mid + 2, bz1, bx2, bz2, 5 + q.random.nextInt(3))
                        .style(q.random.nextBoolean() ? Style.BRICK : Style.BROWNSTONE).front(front).waterTower());
                q.set(L.x(mid + 1), L.y0 + 1, L.z((bz1 + bz2) / 2), Blocks.COMPOSTER.defaultBlockState());
            }
            case 2 -> BuildingBuilder.build(q, L, new Spec(bx1, bz1, bx2, bz2, 10 + q.random.nextInt(5))
                    .style(Style.OFFICE).front(front));
            case 3 -> BuildingBuilder.build(q, L, new Spec(bx1, bz1, bx2, bz2, 9 + q.random.nextInt(3))
                    .style(Style.DECO).front(front).spire());
            default -> BuildingBuilder.build(q, L, new Spec(bx1, bz1, bx2, bz2, 3)
                    .style(Style.WAREHOUSE).front(front).fireEscape().waterTower());
        }
    }

    // ------------------------------------------------------------------ Antonio's Pizza

    private static void antonios(BuildQueue q, Layout L, int x1, int z1, int x2, int z2) {
        Spec s = new Spec(x1, z1, x2, z2, 5).style(Style.BRICK).front(Direction.SOUTH).fireEscape().waterTower().shop();
        BuildingBuilder.build(q, L, s);
        int y0 = L.y0;
        // Big PIZZA sign across the second floor, and a striped awning.
        BuildingBuilder.frontLetters(q, L, s, "PIZZA", y0 + 9, Blocks.RED_CONCRETE.defaultBlockState(), Blocks.WHITE_CONCRETE.defaultBlockState());
        for (int a = 1; a < BuildingBuilder.frontLength(s) - 1; a++) {
            int x = BuildingBuilder.frontX(s, a, 1), z = BuildingBuilder.frontZ(s, a, 1);
            q.set(L.x(x), y0 + 4, L.z(z), (a % 2 == 0 ? Blocks.RED_WOOL : Blocks.WHITE_WOOL).defaultBlockState());
        }
        BuildingBuilder.frontSign(q, L, s, 9, y0 + 3, DyeColor.RED, "ANTONIO'S", "PIZZA", "since 1984", "OPEN LATE");
        // Inside: counter, ovens, tables.
        int cz = z2 - 6;
        for (int x = x1 + 3; x <= x2 - 3; x++) {
            q.set(L.x(x), y0 + 1, L.z(cz), Blocks.BARREL.defaultBlockState());
            q.set(L.x(x), y0 + 2, L.z(cz), Blocks.SMOOTH_QUARTZ_SLAB.defaultBlockState());
        }
        q.set(L.x(x1 + 12), y0 + 1, L.z(cz), Blocks.AIR.defaultBlockState());
        q.set(L.x(x1 + 12), y0 + 2, L.z(cz), Blocks.AIR.defaultBlockState());
        for (int x = x1 + 4; x <= x2 - 4; x += 4) {
            q.set(L.x(x), y0 + 2, L.z(cz), ModBlocks.PIZZA_BOX.get().defaultBlockState());
        }
        for (int x = x1 + 3; x <= x2 - 3; x += 2) {
            q.set(L.x(x), y0 + 1, L.z(z1 + 1), Blocks.SMOKER.defaultBlockState()
                    .setValue(net.minecraft.world.level.block.AbstractFurnaceBlock.FACING, Direction.SOUTH));
            q.set(L.x(x), y0 + 2, L.z(z1 + 1), Blocks.BRICKS.defaultBlockState());
        }
        for (int x = x1 + 3; x <= x2 - 3; x += 5) {
            for (int zz : new int[]{z2 - 3}) {
                q.set(L.x(x), y0 + 1, L.z(zz), Blocks.SPRUCE_FENCE.defaultBlockState());
                q.set(L.x(x), y0 + 2, L.z(zz), (x % 2 == 0 ? Blocks.RED_CARPET : Blocks.WHITE_CARPET).defaultBlockState());
                q.set(L.x(x - 1), y0 + 1, L.z(zz), BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.WEST, false));
                q.set(L.x(x + 1), y0 + 1, L.z(zz), BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.EAST, false));
            }
        }
        q.chest(L.x(x1 + 6), y0 + 1, L.z(cz - 2), Direction.SOUTH, "Antonio's Kitchen",
                new ItemStack(ModItems.PIZZA_SLICE.get(), 16), new ItemStack(ModItems.MIKEY_SPECIAL_PIZZA.get(), 2));
        int ax = (x1 + x2) / 2;
        L.poi("antonios", ax, y0 + 1, z2 + 2);
        L.poi("april", ax, y0 + 1, z2 - 5);
        spawn(q, L, ModEntities.APRIL.get(), ax, y0 + 1, z2 - 5, 0F);
        L.poi("fire_escape_main", BuildingBuilder.frontX(s, 15, 1), y0 + 1, BuildingBuilder.frontZ(s, 15, 1));
    }

    // ------------------------------------------------------------------ Murakami's

    private static void murakamis(BuildQueue q, Layout L, int x1, int z1, int x2, int z2) {
        Spec s = new Spec(x1, z1, x2, z2, 4).style(Style.BROWNSTONE).front(Direction.NORTH).fireEscape().shop();
        BuildingBuilder.build(q, L, s);
        int y0 = L.y0;
        BuildingBuilder.frontLetters(q, L, s, "RAMEN", y0 + 9, Blocks.RED_CONCRETE.defaultBlockState(), Blocks.BLACK_CONCRETE.defaultBlockState());
        BuildingBuilder.frontSign(q, L, s, 9, y0 + 3, DyeColor.WHITE, "MURAKAMI'S", "noodles &", "pizza gyoza", "");
        for (int a = 1; a < BuildingBuilder.frontLength(s) - 1; a++) {
            int x = BuildingBuilder.frontX(s, a, 1), z = BuildingBuilder.frontZ(s, a, 1);
            q.set(L.x(x), y0 + 4, L.z(z), Blocks.RED_WOOL.defaultBlockState());
        }
        // Noodle bar with stools.
        int bz = z1 + 6;
        for (int x = x1 + 4; x <= x2 - 4; x++) {
            q.set(L.x(x), y0 + 1, L.z(bz), Blocks.STRIPPED_BAMBOO_BLOCK.defaultBlockState());
            if (x % 2 == 0) {
                q.set(L.x(x), y0 + 1, L.z(bz - 2), Blocks.BAMBOO_FENCE.defaultBlockState());
                q.set(L.x(x), y0 + 2, L.z(bz - 2), Blocks.BAMBOO_PRESSURE_PLATE.defaultBlockState());
            }
        }
        q.set(L.x(x1 + 8), y0 + 1, L.z(bz + 3), Blocks.CAMPFIRE.defaultBlockState());
        q.set(L.x(x1 + 12), y0 + 1, L.z(bz + 3), Blocks.SMOKER.defaultBlockState());
        for (int x = x1 + 4; x <= x2 - 4; x += 4) {
            q.set(L.x(x), y0 + 3, L.z(bz), Blocks.LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, true));
        }
    }

    // ------------------------------------------------------------------ Times Square

    private static void timesSquare(BuildQueue q, Layout L, int x1, int z1, int x2, int z2) {
        int y0 = L.y0;
        for (int x = x1; x <= x2; x++) {
            for (int z = z1; z <= z2; z++) {
                boolean stripe = (x + z) % 6 == 0;
                q.set(L.x(x), y0, L.z(z), (stripe ? Blocks.POLISHED_DIORITE : Blocks.POLISHED_ANDESITE).defaultBlockState());
            }
        }
        // Red steps in the middle (like the famous red staircase).
        for (int r = 0; r < 4; r++) {
            for (int x = x1 + 8; x <= x2 - 8; x++) {
                q.set(L.x(x), y0 + 1 + r, L.z(z2 - 2 - r), BuildQueue.stairs(Blocks.RED_NETHER_BRICK_STAIRS, Direction.NORTH, false));
                for (int y = y0 + 1; y < y0 + 1 + r; y++) q.set(L.x(x), y, L.z(z2 - 2 - r), Blocks.RED_NETHER_BRICKS.defaultBlockState());
            }
        }
        // Giant glowing billboards.
        billboard(q, L, x1 + 1, z1, Direction.SOUTH, "PIZZA", Blocks.OCHRE_FROGLIGHT);
        billboard(q, L, x2, z1 + 4, Direction.WEST, "NYC", Blocks.PEARLESCENT_FROGLIGHT);
        billboard(q, L, x1, z2 - 4, Direction.EAST, "COMIX", Blocks.VERDANT_FROGLIGHT);
        // Lamps around the plaza.
        for (int t = 4; t <= 20; t += 8) {
            lamp(q, L, x1 + t, y0 + 1, z1 + 6);
        }
        int cx = (x1 + x2) / 2, cz = (z1 + z2) / 2;
        L.poi("times_square", cx, y0 + 1, cz);
        // A circle on the ground where the Kraang portal will open.
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                int d = dx * dx + dz * dz;
                if (d >= 7 && d <= 10) q.set(L.x(cx + dx), y0, L.z(cz + dz), Blocks.PURPLE_TERRACOTTA.defaultBlockState());
            }
        }
    }

    private static void billboard(BuildQueue q, Layout L, int dx, int dz, Direction facing, String word, Block glow) {
        int y0 = L.y0;
        int w = BlockFont.width(word) + 2;
        // For a board facing south you read it looking north: right-hand side is east.
        Direction right = switch (facing) {
            case SOUTH -> Direction.EAST;
            case NORTH -> Direction.WEST;
            case EAST -> Direction.NORTH;
            default -> Direction.SOUTH;
        };
        int bottom = y0 + 6, topY = bottom + 6;
        // Two legs.
        for (int leg : new int[]{1, w - 2}) {
            int lx = dx + right.getStepX() * leg, lz = dz + right.getStepZ() * leg;
            q.fill(L.x(lx), y0 + 1, L.z(lz), L.x(lx), bottom - 1, L.z(lz), Blocks.IRON_BARS);
        }
        for (int a = 0; a < w; a++) {
            for (int y = bottom; y <= topY; y++) {
                int x = dx + right.getStepX() * a, z = dz + right.getStepZ() * a;
                boolean frame = a == 0 || a == w - 1 || y == bottom || y == topY;
                q.set(L.x(x), y, L.z(z), (frame ? Blocks.IRON_BLOCK : Blocks.BLACK_CONCRETE).defaultBlockState());
                // solid back so the letters don't show through backwards
                q.set(L.x(x - facing.getStepX()), y, L.z(z - facing.getStepZ()), Blocks.GRAY_CONCRETE.defaultBlockState());
            }
        }
        BlockFont.draw(q, word, L.x(dx + right.getStepX()), topY - 1, L.z(dz + right.getStepZ()), right, glow.defaultBlockState());
    }

    // ------------------------------------------------------------------ Central Park

    private static void centralPark(BuildQueue q, Layout L, int x1, int z1, int x2, int z2) {
        int y0 = L.y0;
        int cx = (x1 + x2) / 2, cz = (z1 + z2) / 2;
        for (int x = x1; x <= x2; x++) {
            for (int z = z1; z <= z2; z++) {
                boolean path = Math.abs(x - cx) <= 1 || Math.abs(z - cz) <= 1
                        || Math.abs(Math.sqrt((x - cx) * (x - cx) + (z - cz) * (z - cz)) - 8) < 1.0;
                q.set(L.x(x), y0, L.z(z), (path ? Blocks.DIRT_PATH : Blocks.GRASS_BLOCK).defaultBlockState());
                q.set(L.x(x), y0 - 1, L.z(z), Blocks.DIRT.defaultBlockState());
            }
        }
        // Iron fence around the park, with gaps for the paths.
        for (int x = x1; x <= x2; x++) {
            for (int z : new int[]{z1, z2}) {
                if (Math.abs(x - cx) > 1) q.set(L.x(x), y0 + 1, L.z(z), Blocks.DARK_OAK_FENCE.defaultBlockState());
            }
        }
        for (int z = z1; z <= z2; z++) {
            for (int x : new int[]{x1, x2}) {
                if (Math.abs(z - cz) > 1) q.set(L.x(x), y0 + 1, L.z(z), Blocks.DARK_OAK_FENCE.defaultBlockState());
            }
        }
        // Pond in the north-west quarter.
        int px = x1 + 6, pz = z1 + 6;
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                if (dx * dx / 16.0 + dz * dz / 9.0 <= 1.0) {
                    q.set(L.x(px + dx), y0, L.z(pz + dz), Blocks.WATER.defaultBlockState());
                    q.set(L.x(px + dx), y0 - 1, L.z(pz + dz), Blocks.WATER.defaultBlockState());
                    q.set(L.x(px + dx), y0 - 2, L.z(pz + dz), Blocks.CLAY.defaultBlockState());
                    if (q.random.nextInt(6) == 0) q.set(L.x(px + dx), y0 + 1, L.z(pz + dz), Blocks.LILY_PAD.defaultBlockState());
                }
            }
        }
        // Trees.
        int[][] trees = {{x1 + 4, z2 - 4}, {x2 - 4, z1 + 4}, {x2 - 4, z2 - 4}, {x1 + 14, z1 + 3}, {x2 - 3, cz + 5},
                {x1 + 3, cz + 5}, {cx + 5, z2 - 3}, {cx - 6, z2 - 5}, {x2 - 8, z1 + 9}};
        for (int[] t : trees) {
            tree(q, L, t[0], y0 + 1, t[1], q.random.nextBoolean() ? Blocks.OAK_LOG : Blocks.BIRCH_LOG,
                    q.random.nextBoolean() ? Blocks.OAK_LEAVES : Blocks.BIRCH_LEAVES);
        }
        // Benches and flowers along the ring path.
        for (int k = 0; k < 8; k++) {
            double ang = k * Math.PI / 4 + 0.3;
            int bx = cx + (int) Math.round(Math.cos(ang) * 10), bz = cz + (int) Math.round(Math.sin(ang) * 10);
            q.set(L.x(bx), y0 + 1, L.z(bz), BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.NORTH, false));
        }
        for (int k = 0; k < 40; k++) {
            int fx = x1 + 1 + q.random.nextInt(x2 - x1 - 1), fz = z1 + 1 + q.random.nextInt(z2 - z1 - 1);
            BlockState cur = q.get(L.x(fx), y0, L.z(fz));
            if (cur != null && cur.is(Blocks.GRASS_BLOCK) && q.get(L.x(fx), y0 + 1, L.z(fz)) == null) {
                Block f = q.random.nextBoolean() ? Blocks.POPPY : (q.random.nextBoolean() ? Blocks.DANDELION : Blocks.CORNFLOWER);
                q.set(L.x(fx), y0 + 1, L.z(fz), f.defaultBlockState());
            }
        }
        for (int[] p : new int[][]{{cx + 3, cz + 3}, {cx - 3, cz - 3}, {cx + 3, cz - 3}, {cx - 3, cz + 3}}) {
            lamp(q, L, p[0], y0 + 1, p[1]);
        }
        q.standingSign(L.x(cx + 3), y0 + 1, L.z(z1 - 2), Blocks.OAK_SIGN.defaultBlockState()
                        .setValue(net.minecraft.world.level.block.StandingSignBlock.ROTATION, 8),
                DyeColor.GREEN, true, "CENTRAL", "PARK", "(the tiny part)", "");
        L.poi("park", cx, y0 + 1, cz);
    }

    private static void tree(BuildQueue q, Layout L, int dx, int y, int dz, Block log, Block leaves) {
        int h = 4 + q.random.nextInt(2);
        q.fill(L.x(dx), y, L.z(dz), L.x(dx), y + h - 1, L.z(dz), log);
        BlockState leaf = BuildQueue.leaves(leaves);
        for (int ox = -2; ox <= 2; ox++) {
            for (int oz = -2; oz <= 2; oz++) {
                for (int oy = h - 2; oy <= h + 1; oy++) {
                    int r = oy >= h ? 1 : 2;
                    if (Math.abs(ox) <= r && Math.abs(oz) <= r && !(Math.abs(ox) == 2 && Math.abs(oz) == 2)) {
                        if (!(ox == 0 && oz == 0 && oy < h)) {
                            q.set(L.x(dx + ox), y + oy, L.z(dz + oz), leaf);
                        }
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------ Kraang crates

    private static void kraangCrates(BuildQueue q, Layout L) {
        int y = L.y0 + 1;
        int[][] spots = {{55, -74}, {46, 12}, {-74, -28}};
        for (int[] s : spots) {
            int dx = s[0], dz = s[1];
            q.chest(L.x(dx), y, L.z(dz), Direction.SOUTH, "Kraang Crate",
                    new ItemStack(ModItems.MUTAGEN_CANISTER.get(), 2), new ItemStack(Items.IRON_INGOT, 3));
            q.set(L.x(dx - 1), y, L.z(dz), ModBlocks.KRAANG_PANEL.get().defaultBlockState());
            q.set(L.x(dx + 1), y, L.z(dz), ModBlocks.KRAANG_PANEL.get().defaultBlockState());
            q.set(L.x(dx - 1), y + 1, L.z(dz), ModBlocks.MUTAGEN_TANK.get().defaultBlockState());
            L.poiAdd("kraang_crates", dx, y, dz);
        }
    }

    // ------------------------------------------------------------------ helpers

    static void spawn(BuildQueue q, Layout L, net.minecraft.world.entity.EntityType<? extends Mob> type, int dx, int y, int dz, float yaw) {
        BlockPos p = L.rel(dx, y, dz);
        q.post(level -> {
            Mob m = type.create(level);
            if (m != null) {
                m.moveTo(p.getX() + 0.5, p.getY(), p.getZ() + 0.5, yaw, 0);
                m.setYHeadRot(yaw);
                m.finalizeSpawn(level, level.getCurrentDifficultyAt(p), MobSpawnType.STRUCTURE, null, null);
                m.setPersistenceRequired();
                level.addFreshEntity(m);
            }
        });
    }

    static BlockState topSlab(Block b) {
        return b.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.TOP);
    }
}
