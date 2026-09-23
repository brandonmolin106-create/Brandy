package com.echoesinthedark.turtlepower.world;

import com.echoesinthedark.turtlepower.registry.ModBlocks;
import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.animal.Turtle;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CandleBlock;
import net.minecraft.world.level.block.ChainBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.LayeredCauldronBlock;
import net.minecraft.world.level.block.RailBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.RailShape;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.core.Direction.Axis;

/**
 * The turtles' lair: an abandoned subway station deep under the city, like in the 2012 show.
 *
 * <pre>
 *            x: -30        -11   -10              18  19  20        30
 *  z 29  +-------------+------------------------------+------------+
 *        |  GARAGE     |   ENTRANCE (stairs from the  |  DONNIE'S  |
 *        | Shellraiser |   sewer come in at x 10..12) |    LAB     |
 *  z 41  +-------------+                              |            |
 *        |             |        THE PIT (TVs,         +------------+ z 51
 *        |   DOJO      |        couch, arcade)        |  KITCHEN   |
 *        |  (big tree, |                              |            |
 *  z 64  |  dummies,   +------+-------+-------+-------+------------+
 *        |  weapons)   | LEO  | RAPH  | DONNIE| MIKEY              |
 *  z 77  +-------------+------+-------+-------+--------------------+
 * </pre>
 */
public final class LairBuilder {
    private LairBuilder() {}

    static final int X0 = -30, X1 = 30, Z0 = 29, Z1 = 77;

    private static final BlockState AIR = Blocks.AIR.defaultBlockState();
    private static final BlockState STONE = Blocks.STONE.defaultBlockState();
    private static final BlockState BRICK = Blocks.STONE_BRICKS.defaultBlockState();
    private static final BlockState TILE = Blocks.WHITE_TERRACOTTA.defaultBlockState();
    private static final BlockState STRIPE = Blocks.GREEN_TERRACOTTA.defaultBlockState();
    private static final BlockState BASE = Blocks.POLISHED_ANDESITE.defaultBlockState();
    private static final BlockState PILLAR = Blocks.QUARTZ_PILLAR.defaultBlockState();
    private static final BlockState LIGHT = Blocks.SEA_LANTERN.defaultBlockState();
    private static final BlockState SHOJI = Blocks.WHITE_CONCRETE.defaultBlockState();
    private static final BlockState SHOJI_FRAME = Blocks.STRIPPED_SPRUCE_LOG.defaultBlockState();

    private static Layout L;
    private static BuildQueue q;
    private static int lf, lw, lc;

    public static void build(BuildQueue queue, Layout layout) {
        q = queue;
        L = layout;
        lf = L.lf();
        lw = L.lw();
        lc = L.lc();

        shellAndHall();
        entranceStairs();
        garage();
        dojo();
        pit();
        lab();
        kitchen();
        bedrooms();
        secretExit();
        hiddenLights();

        L.poi("lair_hall", 4, lw, 40);
        L.poi("lair_entrance", 11, lw, 30);
        L.poi("lair_exit", 11, L.ys() + 1, 6);
        q = null;
        L = null;
    }

    private static void set(int dx, int y, int dz, BlockState s) {
        q.set(L.x(dx), y, L.z(dz), s);
    }

    private static void set(int dx, int y, int dz, Block b) {
        set(dx, y, dz, b.defaultBlockState());
    }

    private static void fill(int x1, int y1, int z1, int x2, int y2, int z2, BlockState s) {
        q.fill(L.x(x1), y1, L.z(z1), L.x(x2), y2, L.z(z2), s);
    }

    private static void fill(int x1, int y1, int z1, int x2, int y2, int z2, Block b) {
        fill(x1, y1, z1, x2, y2, z2, b.defaultBlockState());
    }

    /** Subway-station style wall: andesite base, white tiles with a green stripe, brick above. */
    private static void tiledWall(int x1, int z1, int x2, int z2) {
        fill(x1, lw, z1, x2, lw + 1, z2, BASE);
        fill(x1, lw + 2, z1, x2, lw + 5, z2, TILE);
        fill(x1, lw + 3, z1, x2, lw + 3, z2, STRIPE);
        fill(x1, lw + 6, z1, x2, lc, z2, BRICK);
    }

    private static void shojiWall(int x1, int z1, int x2, int z2) {
        fill(x1, lw, z1, x2, lc, z2, BRICK);
        fill(x1, lw, z1, x2, lw + 5, z2, SHOJI);
        fill(x1, lw + 6, z1, x2, lw + 6, z2, SHOJI_FRAME.setValue(net.minecraft.world.level.block.RotatedPillarBlock.AXIS, x1 == x2 ? Axis.Z : Axis.X));
        if (x1 == x2) {
            for (int z = Math.min(z1, z2); z <= Math.max(z1, z2); z += 4) fill(x1, lw, z, x1, lw + 5, z, SHOJI_FRAME);
        } else {
            for (int x = Math.min(x1, x2); x <= Math.max(x1, x2); x += 4) fill(x, lw, z1, x, lw + 5, z1, SHOJI_FRAME);
        }
    }

    // ------------------------------------------------------------------ shell

    private static void shellAndHall() {
        // Solid rock box, then carve the whole inside.
        fill(X0 - 1, lf - 4, Z0 - 1, X1 + 1, lc + 1, Z1 + 1, STONE);
        fill(X0, lw, Z0, X1, lc, Z1, AIR);
        // Floors.
        fill(X0, lf, Z0, X1, lf, Z1, Blocks.POLISHED_ANDESITE);
        for (int x = -10; x <= 18; x++) {
            for (int z = Z0; z <= 63; z++) {
                boolean border = x == -10 || x == 18 || z == Z0 || z == 63;
                set(x, lf, z, border ? Blocks.POLISHED_DEEPSLATE.defaultBlockState()
                        : ((x + z) % 2 == 0 ? Blocks.GRAY_CONCRETE : Blocks.LIGHT_GRAY_CONCRETE).defaultBlockState());
            }
        }
        // Outer walls, tiled.
        tiledWall(X0 - 1, Z0 - 1, X1 + 1, Z0 - 1);
        tiledWall(X0 - 1, Z1 + 1, X1 + 1, Z1 + 1);
        tiledWall(X0 - 1, Z0 - 1, X0 - 1, Z1 + 1);
        tiledWall(X1 + 1, Z0 - 1, X1 + 1, Z1 + 1);
        // Ceiling with lights in a grid.
        fill(X0 - 1, lc + 1, Z0 - 1, X1 + 1, lc + 1, Z1 + 1, BRICK);
        for (int x = X0 + 2; x <= X1; x += 5) {
            for (int z = Z0 + 2; z <= Z1; z += 5) {
                set(x, lc + 1, z, LIGHT);
            }
        }
        // Subway pillars in the hall.
        for (int x : new int[]{-6, 16}) {
            for (int z = 33; z <= 61; z += 7) {
                fill(x, lw, z, x, lc, z, PILLAR);
                set(x, lw + 5, z, Blocks.CHISELED_QUARTZ_BLOCK);
            }
        }
        // Internal walls.
        tiledWall(-11, Z0, -11, Z1);          // west zones | hall
        tiledWall(X0, 41, -12, 41);           // garage | dojo
        tiledWall(19, Z0, 19, 63);            // hall | lab+kitchen
        tiledWall(20, 51, X1, 51);            // lab | kitchen
        tiledWall(-10, 64, X1, 64);           // bedrooms' north wall
        tiledWall(0, 65, 0, Z1);              // Leo | Raph
        tiledWall(10, 65, 10, Z1);            // Raph | Donnie
        tiledWall(20, 65, 20, Z1);            // Donnie | Mikey
        // Doorways.
        fill(-11, lw, 33, -11, lw + 4, 37, AIR);   // hall -> garage
        fill(-11, lw, 51, -11, lw + 4, 55, AIR);   // hall -> dojo
        fill(19, lw, 38, 19, lw + 3, 41, AIR);     // hall -> lab
        fill(19, lw, 56, 19, lw + 3, 58, AIR);     // hall -> kitchen
        for (int cx : new int[]{-5, 5, 15, 25}) {  // bedroom doors
            fill(cx - 1, lw, 64, cx, lw + 2, 64, AIR);
        }
        // Lights set into the hall walls.
        for (int z = 35; z <= 60; z += 8) {
            set(-11, lw + 4, z, LIGHT);
            set(19, lw + 4, z, LIGHT);
        }
        // Graffiti-style banner signs.
        q.wallSign(L.x(0), lw + 4, L.z(Z0), Blocks.SPRUCE_WALL_SIGN, Direction.SOUTH, DyeColor.LIME, true,
                "HOME SWEET", "HOME", "~ the lair ~", "");
    }

    // ------------------------------------------------------------------ way in from the sewer

    private static void entranceStairs() {
        int ys = L.ys();
        // Doorway through the south wall of the east-west sewer tunnel under the middle street (z = 0).
        fill(10, ys + 1, 5, 12, ys + 3, 5, AIR);
        // Landing.
        fill(9, ys - 1, 6, 13, ys + 5, 6, BRICK);
        fill(10, ys + 1, 6, 12, ys + 4, 6, AIR);
        fill(10, ys, 6, 12, ys, 6, BASE);
        // 18 steps down to the lair floor.
        for (int k = 1; k <= 18; k++) {
            int z = 6 + k;
            int stepY = ys - k;
            fill(9, stepY - 2, z, 13, stepY + 5, z, TILE);
            fill(9, stepY + 2, z, 9, stepY + 2, z, STRIPE);
            fill(13, stepY + 2, z, 13, stepY + 2, z, STRIPE);
            fill(10, stepY - 1, z, 12, stepY - 1, z, STONE);
            for (int x = 10; x <= 12; x++) {
                set(x, stepY, z, BuildQueue.stairs(Blocks.POLISHED_ANDESITE_STAIRS, Direction.NORTH, false));
            }
            fill(10, stepY + 1, z, 12, stepY + 4, z, AIR);
            if (k % 4 == 0) set(11, stepY + 5, z, LIGHT);
        }
        // Flat tunnel into the lair, with turnstiles.
        for (int z = 25; z <= 28; z++) {
            fill(9, lf - 1, z, 13, lw + 4, z, TILE);
            fill(10, lf, z, 12, lf, z, BASE);
            fill(10, lw, z, 12, lw + 3, z, AIR);
        }
        set(11, lw + 4, 26, LIGHT);
        // Turnstiles just inside.
        for (int x : new int[]{9, 11, 13}) {
            set(x, lw, 31, Blocks.ANDESITE_WALL);
        }
        set(10, lw, 31, q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.EAST, false, true));
        set(12, lw, 31, q.trapdoor(Blocks.IRON_TRAPDOOR, Direction.EAST, false, true));
        q.wallSign(L.x(8), lw + 2, L.z(29), Blocks.SPRUCE_WALL_SIGN, Direction.SOUTH, DyeColor.WHITE, false,
                "DOWNTOWN", "trains: none", "since 1987", "");
    }

    // ------------------------------------------------------------------ garage

    private static void garage() {
        // Tracks.
        for (int x = X0; x <= -12; x++) {
            for (int z : new int[]{33, 37}) {
                set(x, lf, z, Blocks.GRAVEL);
                set(x, lw, z, Blocks.RAIL.defaultBlockState().setValue(RailBlock.SHAPE, RailShape.EAST_WEST));
            }
            set(x, lf, 35, Blocks.YELLOW_CONCRETE);
        }
        // The Shellraiser: an armoured subway car sitting on the far track.
        int y = lw;
        for (int x = -28; x <= -14; x++) {
            for (int z = 36; z <= 38; z++) {
                boolean end = x == -28 || x == -14;
                set(x, y, z, end ? Blocks.IRON_BLOCK : Blocks.GREEN_CONCRETE);
                set(x, y + 1, z, z == 37 && !end ? Blocks.LIME_CONCRETE
                        : (x % 3 == 0 ? Blocks.BLACK_STAINED_GLASS : Blocks.GREEN_CONCRETE));
                set(x, y + 2, z, (x % 3 == 0 && z != 37) ? Blocks.BLACK_STAINED_GLASS : Blocks.GREEN_CONCRETE);
                set(x, y + 3, z, Blocks.GRAY_CONCRETE);
            }
        }
        fill(-27, y + 1, 36, -15, y + 2, 38, Blocks.GREEN_CONCRETE);
        for (int x = -27; x <= -15; x += 3) {
            set(x, y + 2, 36, Blocks.BLACK_STAINED_GLASS);
            set(x, y + 2, 38, Blocks.BLACK_STAINED_GLASS);
        }
        set(-13, y + 1, 37, Blocks.IRON_BARS);
        // Turret on top launches manhole covers!
        set(-21, y + 4, 37, Blocks.IRON_BLOCK);
        set(-21, y + 5, 37, q.trapdoor(ModBlocks.MANHOLE_COVER.get(), Direction.EAST, false, false));
        q.wallSign(L.x(-21), y + 2, L.z(35), Blocks.OAK_WALL_SIGN, Direction.NORTH, DyeColor.LIME, true,
                "THE", "SHELLRAISER", "Donnie's ride", "");
        // Workbench & tools corner.
        set(-29, lw, 30, Blocks.CRAFTING_TABLE);
        set(-28, lw, 30, Blocks.ANVIL);
        set(-27, lw, 30, Blocks.GRINDSTONE);
        set(-26, lw, 30, Blocks.SMITHING_TABLE);
        q.chest(L.x(-25), lw, L.z(30), Direction.SOUTH, "Garage Parts",
                new ItemStack(Items.IRON_INGOT, 16), new ItemStack(Items.REDSTONE, 16), new ItemStack(Items.RAIL, 16),
                new ItemStack(Items.MINECART));
    }

    // ------------------------------------------------------------------ dojo

    private static void dojo() {
        int x0 = X0, x1 = -12, z0 = 42, z1 = Z1;
        // Floor: bamboo mats with a border.
        for (int x = x0; x <= x1; x++) {
            for (int z = z0; z <= z1; z++) {
                boolean border = x == x0 || x == x1 || z == z0 || z == z1;
                set(x, lf, z, border ? Blocks.BAMBOO_MOSAIC : Blocks.BAMBOO_PLANKS);
            }
        }
        // Paper walls on the inside of the dojo.
        shojiWall(x0 - 1, z0, x0 - 1, z1);
        shojiWall(x0, z1 + 1, x1, z1 + 1);
        shojiWall(x0, z0 - 1, x1, z0 - 1);
        fill(-11, lw, 51, -11, lw + 4, 55, AIR);

        // The great tree in the middle of the dojo.
        int tx = -21, tz = 57;
        fill(tx - 2, lf, tz - 2, tx + 2, lf, tz + 2, Blocks.MOSS_BLOCK);
        set(tx, lf, tz, Blocks.ROOTED_DIRT);
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                if ((Math.abs(dx) == 3 || Math.abs(dz) == 3) && Math.abs(dx) + Math.abs(dz) < 6) {
                    set(tx + dx, lf, tz + dz, Blocks.MOSSY_COBBLESTONE);
                }
            }
        }
        fill(tx, lw, tz, tx, lw + 7, tz, Blocks.CHERRY_LOG);
        set(tx + 1, lw + 5, tz, Blocks.CHERRY_LOG.defaultBlockState().setValue(net.minecraft.world.level.block.RotatedPillarBlock.AXIS, Axis.X));
        set(tx - 1, lw + 6, tz, Blocks.CHERRY_LOG.defaultBlockState().setValue(net.minecraft.world.level.block.RotatedPillarBlock.AXIS, Axis.X));
        set(tx, lw + 4, tz + 1, Blocks.CHERRY_LOG.defaultBlockState().setValue(net.minecraft.world.level.block.RotatedPillarBlock.AXIS, Axis.Z));
        BlockState leaves = BuildQueue.leaves(Blocks.CHERRY_LEAVES);
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                for (int dy = 5; dy <= 10; dy++) {
                    double d = Math.sqrt(dx * dx + dz * dz * 1.0 + (dy - 8) * (dy - 8) * 2.2);
                    if (d <= 5.2 && q.random.nextInt(9) != 0 && lw + dy <= lc) {
                        BlockState cur = q.get(L.x(tx + dx), lw + dy, L.z(tz + dz));
                        if (cur == null || cur.isAir()) {
                            set(tx + dx, lw + dy, tz + dz, leaves);
                        }
                    }
                }
            }
        }
        for (int i = 0; i < 18; i++) {
            int dx = q.random.nextInt(7) - 3, dz = q.random.nextInt(7) - 3;
            if (dx != 0 || dz != 0) set(tx + dx, lw, tz + dz, Blocks.PINK_PETALS);
        }

        // Weapon rack on the west wall.
        Item[] rack = {ModItems.KATANA.get(), ModItems.BO_STAFF.get(), ModItems.SAI.get(), ModItems.NUNCHUCKS.get(), ModItems.SHURIKEN.get()};
        for (int i = 0; i < rack.length; i++) {
            q.itemFrame(L.x(x0), lw + 2, L.z(54 + i * 2), Direction.EAST, new ItemStack(rack[i]));
        }
        fill(x0, lw + 3, 53, x0, lw + 3, 63, Blocks.SPRUCE_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.BOTTOM));
        q.chest(L.x(x0), lw, L.z(58), Direction.EAST, "Raph's Weapon Rack",
                new ItemStack(ModItems.SAI.get()), new ItemStack(ModItems.SHURIKEN.get(), 16),
                new ItemStack(ModItems.SMOKE_BOMB.get(), 4), new ItemStack(ModItems.PIZZA_SLICE.get(), 2));
        L.poi("weapon_rack", x0, lw, 58);
        q.wallSign(L.x(x0), lw + 1, L.z(56), Blocks.SPRUCE_WALL_SIGN, Direction.EAST, DyeColor.RED, true,
                "RAPH'S", "weapons", "hands off", "Mikey!!");

        // Training dummies along the east side.
        for (int dz : new int[]{47, 58, 69}) {
            L.poiAdd("dummies", -15, lw, dz);
            set(-15, lf, dz, Blocks.HAY_BLOCK);
        }
        L.poi("dojo", -18, lw, 58);

        // Candles and lanterns.
        for (int z = z0 + 2; z <= z1 - 2; z += 6) {
            set(x1, lw + 5, z, Blocks.LANTERN.defaultBlockState());
            set(x0, lw + 5, z, Blocks.LANTERN.defaultBlockState());
        }

        // Master Splinter's room in the south-west corner.
        shojiWall(-22, 70, -22, z1);
        shojiWall(x0, 69, -22, 69);
        fill(-26, lw, 69, -25, lw + 2, 69, AIR);
        fill(x0, lf, 70, -23, lf, z1, Blocks.STRIPPED_BAMBOO_BLOCK);
        fill(-29, lw, 75, -27, lw, 76, Blocks.BROWN_CARPET);
        set(-24, lw, 76, Blocks.LECTERN);
        for (int[] c : new int[][]{{-29, 71}, {-23, 71}, {-29, 73}}) {
            set(c[0], lw, c[1], Blocks.CANDLE.defaultBlockState().setValue(CandleBlock.CANDLES, 3).setValue(CandleBlock.LIT, true));
        }
        set(-26, lw, 77, Blocks.FLOWER_POT);
        set(-25, lw, 77, Blocks.POTTED_CHERRY_SAPLING);
        L.poi("splinter", -21, lw, 51);

        // Master Splinter himself, and the dummies (spawned once the blocks are in place).
        spawn(ModEntities.SPLINTER.get(), -21, lw, 51, 180F);
        for (int dz : new int[]{47, 58, 69}) {
            spawn(ModEntities.TRAINING_DUMMY.get(), -15, lw, dz, 90F);
        }
    }

    // ------------------------------------------------------------------ the pit (living room)

    private static void pit() {
        int px0 = 0, px1 = 10, pz0 = 47, pz1 = 57;
        // Sunken floor, 2 deep, with a rug.
        fill(px0, lf - 2, pz0, px1, lf, pz1, AIR);
        fill(px0 - 1, lf - 3, pz0 - 1, px1 + 1, lf - 3, pz1 + 1, STONE);
        fill(px0, lf - 2, pz0, px1, lf - 2, pz1, Blocks.SPRUCE_PLANKS);
        fill(px0 + 2, lf - 1, pz0 + 2, px1 - 2, lf - 1, pz1 - 2, Blocks.RED_CARPET);
        fill(px0 + 3, lf - 1, pz0 + 3, px1 - 3, lf - 1, pz1 - 3, Blocks.ORANGE_CARPET);
        for (int x = px0 - 1; x <= px1 + 1; x++) {
            set(x, lf, pz0 - 1, Blocks.POLISHED_DEEPSLATE);
            set(x, lf, pz1 + 1, Blocks.POLISHED_DEEPSLATE);
        }
        // Steps down on the east side.
        for (int z = 51; z <= 53; z++) {
            set(px1, lf - 1, z, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.EAST, false));
            set(px1 + 1, lf, z, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.EAST, false));
        }
        // Couch facing the TVs (backrest to the south).
        for (int x = px0 + 1; x <= px1 - 2; x++) {
            set(x, lf - 1, pz1, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.SOUTH, false));
        }
        set(px0, lf - 1, pz1, Blocks.SPRUCE_SLAB);
        set(px1 - 1, lf - 1, pz1, Blocks.SPRUCE_SLAB);
        // Coffee table with pizza.
        set(5, lf - 1, 53, Blocks.SPRUCE_FENCE);
        set(5, lf, 53, ModBlocks.PIZZA_BOX.get().defaultBlockState());
        // Wall of old TVs behind the pit's north edge.
        for (int x = -2; x <= 12; x++) {
            for (int y = lw; y <= lw + 6; y++) {
                set(x, y, 45, Blocks.BLACK_CONCRETE);
            }
        }
        int[][] screens = {{-1, 1, 3, 3}, {3, 1, 7, 4}, {9, 1, 11, 3}, {-1, 5, 1, 6}, {8, 5, 11, 6}, {2, 6, 6, 6}};
        for (int[] s : screens) {
            for (int x = s[0]; x <= s[2]; x++) {
                for (int dy = s[1]; dy <= s[3]; dy++) {
                    set(x, lw + dy, 45, (x + dy) % 3 == 0 ? Blocks.LIGHT_BLUE_STAINED_GLASS : Blocks.SEA_LANTERN);
                }
            }
        }
        set(5, lw, 46, Blocks.JUKEBOX);
        set(4, lw, 46, Blocks.NOTE_BLOCK);
        // Mikey's arcade corner on the west wall of the hall.
        for (int z = 43; z <= 55; z += 3) {
            set(-10, lw, z, Blocks.BLACK_CONCRETE);
            set(-10, lw + 1, z, (z / 3) % 2 == 0 ? Blocks.PEARLESCENT_FROGLIGHT : Blocks.OCHRE_FROGLIGHT);
            set(-10, lw + 2, z, Blocks.BLACK_CONCRETE);
        }
        q.wallSign(L.x(-10), lw + 3, L.z(49), Blocks.SPRUCE_WALL_SIGN, Direction.EAST, DyeColor.ORANGE, true,
                "MIKEY'S", "ARCADE", "high score:", "MIKEY 99999");
        // A second pizza table near the entrance.
        set(14, lw, 35, Blocks.SPRUCE_FENCE);
        set(14, lw + 1, 35, ModBlocks.PIZZA_BOX.get().defaultBlockState());
        set(13, lw, 35, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.WEST, false));
        set(15, lw, 35, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.EAST, false));
    }

    // ------------------------------------------------------------------ Donnie's lab

    private static void lab() {
        int x0 = 20, x1 = X1, z0 = Z0, z1 = 50;
        for (int x = x0; x <= x1; x++) {
            for (int z = z0; z <= z1; z++) {
                set(x, lf, z, (x + z) % 2 == 0 ? Blocks.WHITE_CONCRETE : Blocks.LIGHT_GRAY_CONCRETE);
            }
        }
        // Mutagen tanks along the east wall.
        for (int z = z0 + 1; z <= z1 - 1; z += 3) {
            set(x1, lw, z, Blocks.IRON_BLOCK);
            set(x1, lw + 1, z, ModBlocks.MUTAGEN_TANK.get());
            set(x1, lw + 2, z, ModBlocks.MUTAGEN_TANK.get());
            set(x1, lw + 3, z, Blocks.IRON_BLOCK);
        }
        // Computer desk on the north wall: monitors glow green.
        for (int x = 22; x <= 28; x++) {
            set(x, lw, z0, Blocks.POLISHED_ANDESITE_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.TOP));
            set(x, lw + 1, z0, x % 2 == 0 ? Blocks.VERDANT_FROGLIGHT : Blocks.BLACK_STAINED_GLASS);
            set(x, lw + 2, z0, Blocks.BLACK_CONCRETE);
            set(x, lw + 3, z0, x % 3 == 0 ? Blocks.VERDANT_FROGLIGHT : Blocks.BLACK_CONCRETE);
        }
        set(25, lw, z0 + 1, BuildQueue.stairs(Blocks.DARK_OAK_STAIRS, Direction.SOUTH, false));
        // Lab benches.
        for (int z : new int[]{36, 43}) {
            for (int x = 22; x <= 27; x++) {
                set(x, lw, z, Blocks.IRON_BLOCK);
            }
            set(22, lw + 1, z, Blocks.BREWING_STAND);
            set(24, lw + 1, z, Blocks.WATER_CAULDRON.defaultBlockState().setValue(LayeredCauldronBlock.LEVEL, 3));
            set(26, lw + 1, z, ModBlocks.MUTAGEN_TANK.get());
            set(27, lw + 1, z, Blocks.LIGHTNING_ROD);
        }
        set(21, lw, z1, Blocks.CRAFTING_TABLE);
        set(22, lw, z1, Blocks.SMITHING_TABLE);
        set(23, lw, z1, Blocks.CARTOGRAPHY_TABLE);
        set(24, lw, z1, Blocks.BOOKSHELF);
        set(25, lw, z1, Blocks.BOOKSHELF);
        set(20, lw, 30, Blocks.TARGET);
        q.chest(L.x(28), lw, L.z(z1), Direction.NORTH, "Donnie's Supplies",
                new ItemStack(ModItems.SMOKE_BOMB.get(), 8), new ItemStack(ModItems.SHURIKEN.get(), 16),
                new ItemStack(Items.IRON_INGOT, 8), new ItemStack(Items.REDSTONE, 32), new ItemStack(Items.GLASS_BOTTLE, 6));
        q.wallSign(L.x(21), lw + 3, L.z(z0), Blocks.OAK_WALL_SIGN, Direction.SOUTH, DyeColor.PURPLE, true,
                "DONNIE'S LAB", "do not touch", "ANYTHING", "(looking at you Mikey)");
        L.poi("lab", 25, lw, 40);
        // Glowing lights on the lab ceiling are brighter.
        for (int x = 22; x <= 28; x += 3) {
            for (int z = 32; z <= 48; z += 4) {
                set(x, lc + 1, z, Blocks.VERDANT_FROGLIGHT);
            }
        }
    }

    // ------------------------------------------------------------------ kitchen

    private static void kitchen() {
        int x0 = 20, x1 = X1, z0 = 52, z1 = 63;
        for (int x = x0; x <= x1; x++) {
            for (int z = z0; z <= z1; z++) {
                set(x, lf, z, (x + z) % 2 == 0 ? Blocks.WHITE_CONCRETE : Blocks.BLACK_CONCRETE);
            }
        }
        // Counter with a stove along the east wall.
        for (int z = z0; z <= z1; z++) {
            set(x1, lw, z, Blocks.BARREL);
            set(x1, lw + 1, z, Blocks.AIR);
        }
        set(x1, lw, 55, Blocks.SMOKER.defaultBlockState().setValue(net.minecraft.world.level.block.AbstractFurnaceBlock.FACING, Direction.WEST));
        set(x1, lw, 56, Blocks.FURNACE.defaultBlockState().setValue(net.minecraft.world.level.block.AbstractFurnaceBlock.FACING, Direction.WEST));
        set(x1, lw, 58, Blocks.WATER_CAULDRON.defaultBlockState().setValue(LayeredCauldronBlock.LEVEL, 3));
        // Fridge.
        set(x1, lw, 61, Blocks.IRON_BLOCK);
        set(x1, lw + 1, 61, Blocks.IRON_BLOCK);
        q.chest(L.x(x1), lw, L.z(62), Direction.WEST, "Fridge",
                new ItemStack(ModItems.PIZZA_SLICE.get(), 12), new ItemStack(ModItems.MIKEY_SPECIAL_PIZZA.get(), 2),
                new ItemStack(Items.MILK_BUCKET), new ItemStack(Items.APPLE, 6));
        // Table and chairs with pizza boxes.
        for (int x = 23; x <= 26; x++) {
            set(x, lw, 57, Blocks.SPRUCE_FENCE);
            set(x, lw + 1, 57, x % 2 == 0 ? ModBlocks.PIZZA_BOX.get().defaultBlockState() : Blocks.SPRUCE_PRESSURE_PLATE.defaultBlockState());
            set(x, lw, 56, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.NORTH, false));
            set(x, lw, 58, BuildQueue.stairs(Blocks.SPRUCE_STAIRS, Direction.SOUTH, false));
        }
        // Stack of pizza boxes on the counter.
        set(x1, lw + 1, 53, ModBlocks.PIZZA_BOX.get().defaultBlockState());
        L.poi("kitchen", 24, lw, 57);
        L.poi("pizza_box", 24, lw + 1, 57);
        q.wallSign(L.x(x1 - 1), lw + 3, L.z(z1), Blocks.OAK_WALL_SIGN, Direction.NORTH, DyeColor.ORANGE, true,
                "KITCHEN RULES", "1. pizza", "2. more pizza", "3. no cooking Mikey");
    }

    // ------------------------------------------------------------------ bedrooms

    private static void bedrooms() {
        room(-10, -1, Blocks.BLUE_BED, Blocks.BLUE_CONCRETE, Blocks.BLUE_CARPET, "LEO", DyeColor.BLUE);
        room(1, 9, Blocks.RED_BED, Blocks.RED_CONCRETE, Blocks.RED_CARPET, "RAPH", DyeColor.RED);
        room(11, 19, Blocks.PURPLE_BED, Blocks.PURPLE_CONCRETE, Blocks.PURPLE_CARPET, "DONNIE", DyeColor.PURPLE);
        room(21, 30, Blocks.ORANGE_BED, Blocks.ORANGE_CONCRETE, Blocks.ORANGE_CARPET, "MIKEY", DyeColor.ORANGE);

        // Leo: meditation candles, a lectern and his favourite show on the wall.
        set(-8, lw, 66, Blocks.LECTERN);
        for (int[] c : new int[][]{{-3, 66}, {-2, 70}, {-9, 72}}) {
            set(c[0], lw, c[1], Blocks.BLUE_CANDLE.defaultBlockState().setValue(CandleBlock.CANDLES, 4).setValue(CandleBlock.LIT, true));
        }
        q.wallSign(L.x(-5), lw + 3, L.z(Z1), Blocks.SPRUCE_WALL_SIGN, Direction.NORTH, DyeColor.BLUE, true,
                "SPACE HEROES", "\"Engage the", "hyperdrive!\"", "- Capt. Ryan");
        q.chest(L.x(-2), lw, L.z(76), Direction.WEST, "Leo's Stuff",
                new ItemStack(ModItems.KATANA.get()), new ItemStack(Items.BOOK, 3));

        // Raph: punching bag, weights, and Spike the turtle.
        fill(7, lw + 3, 70, 7, lc, 70, Blocks.CHAIN.defaultBlockState().setValue(ChainBlock.AXIS, Axis.Y));
        fill(7, lw + 1, 70, 7, lw + 2, 70, Blocks.RED_WOOL);
        set(8, lw, 76, Blocks.ANVIL);
        set(7, lw, 76, Blocks.CHIPPED_ANVIL);
        // Spike's tank.
        for (int x = 1; x <= 3; x++) {
            for (int z = 66; z <= 68; z++) {
                boolean edge = x != 2 || z != 67;
                set(x, lw, z, edge ? Blocks.GLASS.defaultBlockState() : Blocks.WATER.defaultBlockState());
                set(x, lw + 1, z, edge ? Blocks.GLASS.defaultBlockState() : AIR);
                set(x, lf, z, Blocks.SAND);
            }
        }
        set(2, lw + 1, 67, Blocks.LILY_PAD);
        q.chest(L.x(9), lw, L.z(73), Direction.WEST, "Raph's Stuff",
                new ItemStack(ModItems.PIZZA_SLICE.get(), 3), new ItemStack(ModItems.SMOKE_BOMB.get(), 2),
                new ItemStack(Items.IRON_SWORD));
        L.poi("raph_room", 4, lw, 73);
        BlockPos spikePos = L.rel(2, lw, 67);
        q.post(level -> {
            Turtle spike = EntityType.TURTLE.create(level);
            if (spike != null) {
                spike.moveTo(spikePos.getX() + 0.5, spikePos.getY(), spikePos.getZ() + 0.5, 0, 0);
                spike.setAge(-2_000_000);
                spike.setCustomName(Component.literal("Spike"));
                spike.setPersistenceRequired();
                level.addFreshEntity(spike);
            }
        });

        // Donnie: gadgets everywhere.
        set(12, lw, 76, Blocks.CRAFTING_TABLE);
        set(13, lw, 76, Blocks.DISPENSER);
        set(14, lw, 76, Blocks.OBSERVER);
        set(15, lw, 76, Blocks.PISTON);
        set(12, lw, 66, Blocks.REDSTONE_LAMP);
        set(18, lw, 66, Blocks.BOOKSHELF);
        set(18, lw + 1, 66, Blocks.BOOKSHELF);
        q.chest(L.x(18), lw, L.z(70), Direction.WEST, "Donnie's Stuff",
                new ItemStack(ModItems.BO_STAFF.get()), new ItemStack(Items.REDSTONE, 16), new ItemStack(Items.COMPASS));

        // Mikey: comics, games and pizza.
        set(22, lw, 66, Blocks.JUKEBOX);
        set(29, lw, 66, Blocks.CHISELED_BOOKSHELF);
        set(29, lw + 1, 66, Blocks.CHISELED_BOOKSHELF);
        set(25, lw, 70, ModBlocks.PIZZA_BOX.get().defaultBlockState());
        set(26, lw, 71, ModBlocks.PIZZA_BOX.get().defaultBlockState());
        set(22, lw, 76, Blocks.BLACK_CONCRETE);
        set(22, lw + 1, 76, Blocks.OCHRE_FROGLIGHT);
        q.chest(L.x(30), lw, L.z(73), Direction.WEST, "Mikey's Stuff",
                new ItemStack(ModItems.NUNCHUCKS.get()), new ItemStack(ModItems.MIKEY_SPECIAL_PIZZA.get(), 3),
                new ItemStack(Items.COOKIE, 16));
    }

    private static void room(int x0, int x1, Block bed, Block accent, Block carpet, String name, DyeColor color) {
        int z0 = 65, z1 = Z1;
        fill(x0, lf, z0, x1, lf, z1, Blocks.SPRUCE_PLANKS);
        int mid = (x0 + x1) / 2;
        fill(mid - 1, lf, z0 + 3, mid + 1, lf, z0 + 6, Blocks.SPRUCE_PLANKS);
        fill(mid - 1, lw, z0 + 3, mid + 1, lw, z0 + 6, carpet);
        // accent stripe on the walls
        fill(x0, lw + 3, z1 + 1, x1, lw + 3, z1 + 1, accent);
        q.bed(L.x(x0 + 1), lw, L.z(z1 - 1), bed, Direction.SOUTH);
        set(x0 + 2, lw, z1, Blocks.LANTERN);
        q.wallSign(L.x(mid), lw + 3, L.z(z0 - 2), Blocks.SPRUCE_WALL_SIGN, Direction.NORTH, color, true,
                name + "'S", "ROOM", "", "knock first!");
    }

    // ------------------------------------------------------------------ back door

    private static void secretExit() {
        // A long ladder from the garage corner straight up into the back of Murakami's shop.
        int x = -30, z = 29;
        fill(x - 1, lc, z - 1, x + 1, L.y0 - 1, z + 1, BRICK);
        q.ladder(L.x(x), lw, L.y0 - 1, L.z(z), Direction.EAST);
        set(x, L.y0, z, q.trapdoor(ModBlocks.MANHOLE_COVER.get(), Direction.EAST, true, false));
        q.wallSign(L.x(-28), lw + 2, L.z(29), Blocks.SPRUCE_WALL_SIGN, Direction.SOUTH, DyeColor.WHITE, false,
                "BACK DOOR", "to Murakami's", "noodle shop", "");
        // make the ladder's wall solid all the way up
        fill(x - 1, lw, z, x - 1, L.y0 - 1, z, BRICK);
        L.poi("secret_exit", x, L.y0, z);
    }

    /**
     * Invisible light blocks in every open space of the lair (monsters spawn in total darkness,
     * and nobody wants a zombie in the kitchen).
     */
    private static void hiddenLights() {
        BlockState light = Blocks.LIGHT.defaultBlockState().setValue(net.minecraft.world.level.block.LightBlock.LEVEL, 15);
        for (int x = X0 + 1; x <= X1; x += 5) {
            for (int z = Z0 + 1; z <= Z1; z += 5) {
                for (int y : new int[]{lf - 1, lw + 2, lw + 8}) {
                    BlockState cur = q.get(L.x(x), y, L.z(z));
                    if (cur != null && cur.isAir()) {
                        set(x, y, z, light);
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------ helpers

    private static void spawn(EntityType<? extends Mob> type, int dx, int y, int dz, float yaw) {
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
}
