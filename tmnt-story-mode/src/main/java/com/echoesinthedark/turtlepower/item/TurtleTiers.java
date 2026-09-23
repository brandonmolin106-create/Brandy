package com.echoesinthedark.turtlepower.item;

import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;

public final class TurtleTiers {
    private TurtleTiers() {}

    /** Ninja steel: a bit better than iron, tougher than it looks. */
    public static final Tier NINJA = new Tier() {
        @Override public int getUses() { return 1500; }
        @Override public float getSpeed() { return 7.0F; }
        @Override public float getAttackDamageBonus() { return 3.0F; }
        @Override public int getLevel() { return 2; }
        @Override public int getEnchantmentValue() { return 18; }
        @Override public Ingredient getRepairIngredient() { return Ingredient.of(Items.IRON_INGOT); }
    };

    public static final ArmorMaterial TURTLE_ARMOR = new ArmorMaterial() {
        @Override public int getDurabilityForType(ArmorItem.Type type) {
            return type == ArmorItem.Type.HELMET ? 300 : 480;
        }
        @Override public int getDefenseForType(ArmorItem.Type type) {
            return switch (type) {
                case HELMET -> 2;
                case CHESTPLATE -> 7;
                case LEGGINGS -> 5;
                case BOOTS -> 2;
            };
        }
        @Override public int getEnchantmentValue() { return 15; }
        @Override public SoundEvent getEquipSound() { return SoundEvents.ARMOR_EQUIP_TURTLE; }
        @Override public Ingredient getRepairIngredient() { return Ingredient.of(Items.SCUTE); }
        @Override public String getName() { return "turtlepower:turtle"; }
        @Override public float getToughness() { return 1.5F; }
        @Override public float getKnockbackResistance() { return 0.1F; }
    };
}
