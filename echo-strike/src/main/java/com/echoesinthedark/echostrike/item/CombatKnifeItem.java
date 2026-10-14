package com.echoesinthedark.echostrike.item;

import net.minecraft.world.item.Items;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;

/** Fast melee for when the mag runs dry. Swings quicker than a sword and hits like iron. */
public class CombatKnifeItem extends SwordItem {
    private static final Tier TIER = new Tier() {
        @Override public int getUses() { return 600; }
        @Override public float getSpeed() { return 6.0F; }
        @Override public float getAttackDamageBonus() { return 3.0F; }
        @Override public int getLevel() { return 2; }
        @Override public int getEnchantmentValue() { return 12; }
        @Override public Ingredient getRepairIngredient() { return Ingredient.of(Items.IRON_INGOT); }
    };

    public CombatKnifeItem(Properties props) {
        // Sword base is 3 + bonus; speed -2.0 makes it about 2 swings a second.
        super(TIER, 2, -2.0F, props);
    }
}
