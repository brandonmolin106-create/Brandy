package com.echoesinthedark.turtlepower.world;

import net.minecraft.core.Direction;
import net.minecraft.world.level.block.state.BlockState;

import java.util.HashMap;
import java.util.Map;

/** A tiny 3x5 pixel font so we can write big block letters on buildings ("PIZZA", "TCRI"...). */
public final class BlockFont {
    private BlockFont() {}

    private static final Map<Character, String[]> GLYPHS = new HashMap<>();

    static {
        g('A', "###", "#.#", "###", "#.#", "#.#");
        g('B', "##.", "#.#", "##.", "#.#", "##.");
        g('C', "###", "#..", "#..", "#..", "###");
        g('D', "##.", "#.#", "#.#", "#.#", "##.");
        g('E', "###", "#..", "##.", "#..", "###");
        g('F', "###", "#..", "##.", "#..", "#..");
        g('G', "###", "#..", "#.#", "#.#", "###");
        g('H', "#.#", "#.#", "###", "#.#", "#.#");
        g('I', "###", ".#.", ".#.", ".#.", "###");
        g('J', "..#", "..#", "..#", "#.#", "###");
        g('K', "#.#", "#.#", "##.", "#.#", "#.#");
        g('L', "#..", "#..", "#..", "#..", "###");
        g('M', "#.#", "###", "###", "#.#", "#.#");
        g('N', "##.", "#.#", "#.#", "#.#", "#.#");
        g('O', "###", "#.#", "#.#", "#.#", "###");
        g('P', "###", "#.#", "###", "#..", "#..");
        g('Q', "###", "#.#", "#.#", "###", "..#");
        g('R', "##.", "#.#", "##.", "#.#", "#.#");
        g('S', "###", "#..", "###", "..#", "###");
        g('T', "###", ".#.", ".#.", ".#.", ".#.");
        g('U', "#.#", "#.#", "#.#", "#.#", "###");
        g('V', "#.#", "#.#", "#.#", "#.#", ".#.");
        g('W', "#.#", "#.#", "###", "###", "#.#");
        g('X', "#.#", "#.#", ".#.", "#.#", "#.#");
        g('Y', "#.#", "#.#", ".#.", ".#.", ".#.");
        g('Z', "###", "..#", ".#.", "#..", "###");
        g('!', ".#.", ".#.", ".#.", "...", ".#.");
        g('\'', ".#.", ".#.", "...", "...", "...");
        g(' ', "...", "...", "...", "...", "...");
    }

    private static void g(char c, String... rows) {
        GLYPHS.put(c, rows);
    }

    /** Width in blocks of some text (3 per letter plus 1 gap). */
    public static int width(String text) {
        return text.length() * 4 - 1;
    }

    /**
     * Draw text on a wall. (x, yTop, z) is the top-left pixel; letters run toward {@code right}.
     */
    public static void draw(BuildQueue q, String text, int x, int yTop, int z, Direction right, BlockState ink) {
        int col = 0;
        for (char ch : text.toUpperCase().toCharArray()) {
            String[] rows = GLYPHS.getOrDefault(ch, GLYPHS.get(' '));
            for (int r = 0; r < 5; r++) {
                for (int c = 0; c < 3; c++) {
                    if (rows[r].charAt(c) == '#') {
                        int o = col + c;
                        q.set(x + right.getStepX() * o, yTop - r, z + right.getStepZ() * o, ink);
                    }
                }
            }
            col += 4;
        }
    }
}
