package com.echoesinthedark.echostrike.registry;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.item.ArmorPlateItem;
import com.echoesinthedark.echostrike.item.CombatKnifeItem;
import com.echoesinthedark.echostrike.item.GrenadeItem;
import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.item.MedkitItem;
import com.echoesinthedark.echostrike.item.StrikeArmorMaterial;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModItems {
    private ModItems() {}

    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, EchoStrike.MODID);

    // ---- Guns ----
    public static final RegistryObject<Item> G18 = gun(GunType.G18, Rarity.COMMON);
    public static final RegistryObject<Item> DEAGLE = gun(GunType.DEAGLE, Rarity.UNCOMMON);
    public static final RegistryObject<Item> MP5 = gun(GunType.MP5, Rarity.UNCOMMON);
    public static final RegistryObject<Item> UMP45 = gun(GunType.UMP45, Rarity.UNCOMMON);
    public static final RegistryObject<Item> VECTOR = gun(GunType.VECTOR, Rarity.UNCOMMON);
    public static final RegistryObject<Item> AK47 = gun(GunType.AK47, Rarity.UNCOMMON);
    public static final RegistryObject<Item> M4A1 = gun(GunType.M4A1, Rarity.UNCOMMON);
    public static final RegistryObject<Item> M870 = gun(GunType.M870, Rarity.UNCOMMON);
    public static final RegistryObject<Item> AWM = gun(GunType.AWM, Rarity.RARE);
    public static final RegistryObject<Item> M249 = gun(GunType.M249, Rarity.RARE);
    public static final RegistryObject<Item> COMBAT_KNIFE = ITEMS.register("combat_knife", () -> new CombatKnifeItem(new Item.Properties()));

    // ---- Ammo ----
    public static final RegistryObject<Item> LIGHT_AMMO = ITEMS.register("light_ammo", () -> new Item(new Item.Properties().stacksTo(64)));
    public static final RegistryObject<Item> HEAVY_AMMO = ITEMS.register("heavy_ammo", () -> new Item(new Item.Properties().stacksTo(64)));
    public static final RegistryObject<Item> SHOTGUN_SHELLS = ITEMS.register("shotgun_shells", () -> new Item(new Item.Properties().stacksTo(64)));
    public static final RegistryObject<Item> SNIPER_ROUNDS = ITEMS.register("sniper_rounds", () -> new Item(new Item.Properties().stacksTo(64)));

    // ---- Gear ----
    public static final RegistryObject<Item> FRAG_GRENADE = ITEMS.register("frag_grenade", () -> new GrenadeItem(new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> MEDKIT = ITEMS.register("medkit", () -> new MedkitItem(new Item.Properties().stacksTo(8)));
    public static final RegistryObject<Item> ARMOR_PLATE = ITEMS.register("armor_plate", () -> new ArmorPlateItem(new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> STRIKE_HELMET = ITEMS.register("strike_helmet",
            () -> new ArmorItem(StrikeArmorMaterial.INSTANCE, ArmorItem.Type.HELMET, new Item.Properties()));
    public static final RegistryObject<Item> STRIKE_VEST = ITEMS.register("strike_vest",
            () -> new ArmorItem(StrikeArmorMaterial.INSTANCE, ArmorItem.Type.CHESTPLATE, new Item.Properties()));

    // ---- Spawn eggs ----
    public static final RegistryObject<Item> OPERATIVE_SPAWN_EGG = ITEMS.register("operative_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.OPERATIVE, 0x23262E, 0xE0202A, new Item.Properties()));

    private static RegistryObject<Item> gun(GunType type, Rarity rarity) {
        return ITEMS.register(type.id, () -> new GunItem(type, new Item.Properties().rarity(rarity)));
    }

    public static Item gunFor(GunType type) {
        return switch (type) {
            case G18 -> G18.get();
            case DEAGLE -> DEAGLE.get();
            case MP5 -> MP5.get();
            case UMP45 -> UMP45.get();
            case VECTOR -> VECTOR.get();
            case AK47 -> AK47.get();
            case M4A1 -> M4A1.get();
            case M870 -> M870.get();
            case AWM -> AWM.get();
            case M249 -> M249.get();
        };
    }
}
