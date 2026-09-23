package com.echoesinthedark.turtlepower.registry;

import com.echoesinthedark.turtlepower.TurtlePower;
import com.echoesinthedark.turtlepower.entity.FootNinjaEntity;
import com.echoesinthedark.turtlepower.entity.KraangBoltEntity;
import com.echoesinthedark.turtlepower.entity.KraangDroidEntity;
import com.echoesinthedark.turtlepower.entity.KraangPrimeEntity;
import com.echoesinthedark.turtlepower.entity.ShurikenEntity;
import com.echoesinthedark.turtlepower.entity.SmokeBombEntity;
import com.echoesinthedark.turtlepower.entity.StoryNpcEntity;
import com.echoesinthedark.turtlepower.entity.TrainingDummyEntity;
import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod.EventBusSubscriber(modid = TurtlePower.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class ModEntities {
    private ModEntities() {}

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, TurtlePower.MODID);

    // ---- Your brothers ----
    public static final RegistryObject<EntityType<TurtleBrotherEntity>> LEONARDO = brother("leonardo", 0.95F);
    public static final RegistryObject<EntityType<TurtleBrotherEntity>> DONATELLO = brother("donatello", 1.0F);
    public static final RegistryObject<EntityType<TurtleBrotherEntity>> MICHELANGELO = brother("michelangelo", 0.9F);

    // ---- Friends ----
    public static final RegistryObject<EntityType<StoryNpcEntity>> SPLINTER = ENTITY_TYPES.register("splinter",
            () -> EntityType.Builder.of(StoryNpcEntity::new, MobCategory.MISC).sized(0.6F, 1.9F).clientTrackingRange(10).build("splinter"));
    public static final RegistryObject<EntityType<StoryNpcEntity>> APRIL = ENTITY_TYPES.register("april",
            () -> EntityType.Builder.of(StoryNpcEntity::new, MobCategory.MISC).sized(0.6F, 1.8F).clientTrackingRange(10).build("april"));
    public static final RegistryObject<EntityType<TrainingDummyEntity>> TRAINING_DUMMY = ENTITY_TYPES.register("training_dummy",
            () -> EntityType.Builder.of(TrainingDummyEntity::new, MobCategory.MISC).sized(0.6F, 1.9F).clientTrackingRange(8).build("training_dummy"));

    // ---- Enemies ----
    public static final RegistryObject<EntityType<KraangDroidEntity>> KRAANG_DROID = ENTITY_TYPES.register("kraang_droid",
            () -> EntityType.Builder.<KraangDroidEntity>of(KraangDroidEntity::new, MobCategory.MONSTER).sized(0.6F, 1.95F).clientTrackingRange(10).build("kraang_droid"));
    public static final RegistryObject<EntityType<KraangPrimeEntity>> KRAANG_PRIME = ENTITY_TYPES.register("kraang_prime",
            () -> EntityType.Builder.<KraangPrimeEntity>of(KraangPrimeEntity::new, MobCategory.MONSTER).sized(1.1F, 3.5F).fireImmune().clientTrackingRange(12).build("kraang_prime"));
    public static final RegistryObject<EntityType<FootNinjaEntity>> FOOT_NINJA = ENTITY_TYPES.register("foot_ninja",
            () -> EntityType.Builder.of(FootNinjaEntity::new, MobCategory.MONSTER).sized(0.6F, 1.9F).clientTrackingRange(10).build("foot_ninja"));

    // ---- Projectiles ----
    public static final RegistryObject<EntityType<ShurikenEntity>> SHURIKEN = ENTITY_TYPES.register("shuriken",
            () -> EntityType.Builder.<ShurikenEntity>of(ShurikenEntity::new, MobCategory.MISC).sized(0.3F, 0.3F).clientTrackingRange(4).updateInterval(10).build("shuriken"));
    public static final RegistryObject<EntityType<SmokeBombEntity>> SMOKE_BOMB = ENTITY_TYPES.register("smoke_bomb",
            () -> EntityType.Builder.<SmokeBombEntity>of(SmokeBombEntity::new, MobCategory.MISC).sized(0.25F, 0.25F).clientTrackingRange(4).updateInterval(10).build("smoke_bomb"));
    public static final RegistryObject<EntityType<KraangBoltEntity>> KRAANG_BOLT = ENTITY_TYPES.register("kraang_bolt",
            () -> EntityType.Builder.<KraangBoltEntity>of(KraangBoltEntity::new, MobCategory.MISC).sized(0.3F, 0.3F).clientTrackingRange(6).updateInterval(2).build("kraang_bolt"));

    private static RegistryObject<EntityType<TurtleBrotherEntity>> brother(String name, float height) {
        return ENTITY_TYPES.register(name, () -> EntityType.Builder.of(TurtleBrotherEntity::new, MobCategory.MISC)
                .sized(0.65F, 1.85F * height).clientTrackingRange(10).build(name));
    }

    @SubscribeEvent
    public static void onSpawnPlacements(SpawnPlacementRegisterEvent event) {
        event.register(KRAANG_DROID.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Monster::checkMonsterSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(FOOT_NINJA.get(), SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Monster::checkMonsterSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
    }

    @SubscribeEvent
    public static void onAttributes(EntityAttributeCreationEvent event) {
        event.put(LEONARDO.get(), TurtleBrotherEntity.createAttributes().build());
        event.put(DONATELLO.get(), TurtleBrotherEntity.createAttributes().build());
        event.put(MICHELANGELO.get(), TurtleBrotherEntity.createAttributes().build());
        event.put(SPLINTER.get(), StoryNpcEntity.createAttributes().build());
        event.put(APRIL.get(), StoryNpcEntity.createAttributes().build());
        event.put(TRAINING_DUMMY.get(), TrainingDummyEntity.createAttributes().build());
        event.put(KRAANG_DROID.get(), KraangDroidEntity.createAttributes().build());
        event.put(KRAANG_PRIME.get(), KraangPrimeEntity.createPrimeAttributes().build());
        event.put(FOOT_NINJA.get(), FootNinjaEntity.createAttributes().build());
    }
}
