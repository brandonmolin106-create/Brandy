package com.echoesinthedark.turtlepower.registry;

import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.item.KraangBlasterItem;
import com.echoesinthedark.turtlepower.item.MikeySpecialPizzaItem;
import com.echoesinthedark.turtlepower.item.MutagenCanisterItem;
import com.echoesinthedark.turtlepower.item.NinjaWeaponItem;
import com.echoesinthedark.turtlepower.item.RetroMutagenItem;
import com.echoesinthedark.turtlepower.item.ShurikenItem;
import com.echoesinthedark.turtlepower.item.SmokeBombItem;
import com.echoesinthedark.turtlepower.item.TPhoneItem;
import com.echoesinthedark.turtlepower.item.TurtleArmorItem;
import com.echoesinthedark.turtlepower.item.TurtleTiers;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModItems {
    private ModItems() {}

    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, TurtlePower.MODID);

    // ---- The four brothers' weapons ----
    public static final RegistryObject<Item> SAI = ITEMS.register("sai",
            () -> new NinjaWeaponItem(NinjaWeaponItem.Style.SAI, TurtleTiers.NINJA, 3, -2.0F, 0.0, new Item.Properties()));
    public static final RegistryObject<Item> KATANA = ITEMS.register("katana",
            () -> new NinjaWeaponItem(NinjaWeaponItem.Style.KATANA, TurtleTiers.NINJA, 4, -2.2F, 0.0, new Item.Properties()));
    public static final RegistryObject<Item> BO_STAFF = ITEMS.register("bo_staff",
            () -> new NinjaWeaponItem(NinjaWeaponItem.Style.BO_STAFF, TurtleTiers.NINJA, 2, -2.6F, 1.5, new Item.Properties()));
    public static final RegistryObject<Item> NUNCHUCKS = ITEMS.register("nunchucks",
            () -> new NinjaWeaponItem(NinjaWeaponItem.Style.NUNCHUCKS, TurtleTiers.NINJA, 1, -1.4F, 0.0, new Item.Properties()));

    // ---- Ninja gear ----
    public static final RegistryObject<Item> SHURIKEN = ITEMS.register("shuriken",
            () -> new ShurikenItem(new Item.Properties().stacksTo(32)));
    public static final RegistryObject<Item> SMOKE_BOMB = ITEMS.register("smoke_bomb",
            () -> new SmokeBombItem(new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> T_PHONE = ITEMS.register("t_phone",
            () -> new TPhoneItem(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)));

    // ---- Mutagen ----
    public static final RegistryObject<Item> MUTAGEN_CANISTER = ITEMS.register("mutagen_canister",
            () -> new MutagenCanisterItem(new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON)));
    public static final RegistryObject<Item> RETRO_MUTAGEN = ITEMS.register("retro_mutagen",
            () -> new RetroMutagenItem(new Item.Properties().stacksTo(16).rarity(Rarity.RARE)));

    // ---- Pizza! ----
    public static final RegistryObject<Item> PIZZA_SLICE = ITEMS.register("pizza_slice",
            () -> new Item(new Item.Properties().food(new FoodProperties.Builder()
                    .nutrition(6).saturationMod(0.9F).fast().alwaysEat()
                    .effect(() -> new MobEffectInstance(MobEffects.REGENERATION, 100, 1), 1.0F).build())));
    public static final RegistryObject<Item> MIKEY_SPECIAL_PIZZA = ITEMS.register("mikey_special_pizza",
            () -> new MikeySpecialPizzaItem(new Item.Properties().rarity(Rarity.UNCOMMON).food(new FoodProperties.Builder()
                    .nutrition(8).saturationMod(1.0F).alwaysEat().build())));

    // ---- Kraang tech ----
    public static final RegistryObject<Item> KRAANG_BLASTER = ITEMS.register("kraang_blaster",
            () -> new KraangBlasterItem(new Item.Properties().durability(160).rarity(Rarity.UNCOMMON)));
    /** Only used to draw Kraang laser bolts in the world. */
    public static final RegistryObject<Item> KRAANG_BOLT = ITEMS.register("kraang_bolt",
            () -> new Item(new Item.Properties()));

    // ---- Raphael's gear ----
    public static final RegistryObject<Item> RAPH_MASK = ITEMS.register("raph_mask",
            () -> new TurtleArmorItem(TurtleTiers.TURTLE_ARMOR, ArmorItem.Type.HELMET, new Item.Properties()));
    public static final RegistryObject<Item> TURTLE_SHELL = ITEMS.register("turtle_shell",
            () -> new TurtleArmorItem(TurtleTiers.TURTLE_ARMOR, ArmorItem.Type.CHESTPLATE, new Item.Properties()));

    // ---- Blocks ----
    public static final RegistryObject<Item> MANHOLE_COVER = ITEMS.register("manhole_cover",
            () -> new BlockItem(ModBlocks.MANHOLE_COVER.get(), new Item.Properties()));
    public static final RegistryObject<Item> MUTAGEN_OOZE = ITEMS.register("mutagen_ooze",
            () -> new BlockItem(ModBlocks.MUTAGEN_OOZE.get(), new Item.Properties()));
    public static final RegistryObject<Item> MUTAGEN_TANK = ITEMS.register("mutagen_tank",
            () -> new BlockItem(ModBlocks.MUTAGEN_TANK.get(), new Item.Properties()));
    public static final RegistryObject<Item> KRAANG_PANEL = ITEMS.register("kraang_panel",
            () -> new BlockItem(ModBlocks.KRAANG_PANEL.get(), new Item.Properties()));
    public static final RegistryObject<Item> PIZZA_BOX = ITEMS.register("pizza_box",
            () -> new BlockItem(ModBlocks.PIZZA_BOX.get(), new Item.Properties()));

    // ---- Spawn eggs ----
    public static final RegistryObject<Item> LEONARDO_SPAWN_EGG = ITEMS.register("leonardo_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.LEONARDO, 0x3E8E3A, 0x1F4FD8, new Item.Properties()));
    public static final RegistryObject<Item> DONATELLO_SPAWN_EGG = ITEMS.register("donatello_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.DONATELLO, 0x4E9A3E, 0x7B2FBF, new Item.Properties()));
    public static final RegistryObject<Item> MICHELANGELO_SPAWN_EGG = ITEMS.register("michelangelo_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.MICHELANGELO, 0x5DAA44, 0xF08A1C, new Item.Properties()));
    public static final RegistryObject<Item> SPLINTER_SPAWN_EGG = ITEMS.register("splinter_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.SPLINTER, 0x6B4A32, 0x7A1F2B, new Item.Properties()));
    public static final RegistryObject<Item> APRIL_SPAWN_EGG = ITEMS.register("april_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.APRIL, 0xE0782E, 0xF2D13A, new Item.Properties()));
    public static final RegistryObject<Item> KRAANG_DROID_SPAWN_EGG = ITEMS.register("kraang_droid_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.KRAANG_DROID, 0xD9DDE3, 0xE56BB7, new Item.Properties()));
    public static final RegistryObject<Item> KRAANG_PRIME_SPAWN_EGG = ITEMS.register("kraang_prime_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.KRAANG_PRIME, 0x5B2A86, 0xE56BB7, new Item.Properties()));
    public static final RegistryObject<Item> FOOT_NINJA_SPAWN_EGG = ITEMS.register("foot_ninja_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.FOOT_NINJA, 0x1A1A1E, 0xB3161B, new Item.Properties()));
    public static final RegistryObject<Item> TRAINING_DUMMY_SPAWN_EGG = ITEMS.register("training_dummy_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.TRAINING_DUMMY, 0xC9A45C, 0x8A5A2B, new Item.Properties()));
}
