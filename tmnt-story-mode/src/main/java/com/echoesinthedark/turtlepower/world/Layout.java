package com.echoesinthedark.turtlepower.world;

import net.minecraft.core.BlockPos;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Where everything goes, relative to the story origin (the middle of the city, at street level).
 *
 * <pre>
 *  Streets (roads 9 wide) run north-south at x = -80, -40, 0, 40, 80 and east-west at the same z.
 *  Between them are 16 city blocks ("lots") 31x31, each with a 3 wide sidewalk ring.
 *
 *  y0      street surface. You walk at y0 + 1.
 *  y0 - 8  sewer walkway blocks (you walk at y0 - 7). Tunnels run under every street.
 *  y0 - 26 lair floor (you walk at y0 - 25). The lair is under the south-middle of the city.
 * </pre>
 */
public class Layout {
    public static final int[] STREETS = {-80, -40, 0, 40, 80};
    public static final int ROAD_HALF = 4;
    public static final int CITY_HALF = 84;
    public static final int EDGE = 90;
    public static final int AREA = 97;

    public final int ox;
    public final int oz;
    public final int y0;

    private final Map<String, BlockPos> pois = new HashMap<>();
    private final Map<String, List<BlockPos>> poiLists = new HashMap<>();

    public Layout(int ox, int y0, int oz) {
        this.ox = ox;
        this.oz = oz;
        this.y0 = y0;
    }

    public int x(int dx) { return ox + dx; }
    public int z(int dz) { return oz + dz; }

    /** Sewer walkway block level. */
    public int ys() { return y0 - 8; }
    /** Lair floor block level. */
    public int lf() { return y0 - 26; }
    /** Lair walk level. */
    public int lw() { return y0 - 25; }
    /** Lair ceiling (last air block). */
    public int lc() { return y0 - 13; }

    /** First x (relative) of lot column i (0..3), including its sidewalk. */
    public static int lotMin(int i) { return -80 + 40 * i + 5; }
    public static int lotMax(int i) { return lotMin(i) + 30; }
    /** Building area inside the sidewalk ring. */
    public static int buildMin(int i) { return lotMin(i) + 3; }
    public static int buildMax(int i) { return lotMax(i) - 3; }

    public BlockPos rel(int dx, int y, int dz) {
        return new BlockPos(x(dx), y, z(dz));
    }

    public void poi(String key, int dx, int y, int dz) {
        pois.put(key, rel(dx, y, dz));
    }

    public void poiAdd(String key, int dx, int y, int dz) {
        poiLists.computeIfAbsent(key, k -> new ArrayList<>()).add(rel(dx, y, dz));
    }

    public Map<String, BlockPos> pois() {
        return pois;
    }

    public Map<String, List<BlockPos>> poiLists() {
        return poiLists;
    }
}
