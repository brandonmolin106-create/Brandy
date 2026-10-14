package com.echoesinthedark.echostrike.registry;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.entity.GrenadeEntity;
import com.echoesinthedark.echostrike.entity.OperativeEntity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod.EventBusSubscriber(modid = EchoStrike.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class ModEntities {
    private ModEntities() {}

    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, EchoStrike.MODID);

    /** Enemy soldier with a gun. Does not spawn naturally; game modes and the spawn egg make them. */
    public static final RegistryObject<EntityType<OperativeEntity>> OPERATIVE = ENTITY_TYPES.register("operative",
            () -> EntityType.Builder.<OperativeEntity>of(OperativeEntity::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.9F).clientTrackingRange(12).build("operative"));

    public static final RegistryObject<EntityType<GrenadeEntity>> FRAG_GRENADE = ENTITY_TYPES.register("frag_grenade",
            () -> EntityType.Builder.<GrenadeEntity>of(GrenadeEntity::new, MobCategory.MISC)
                    .sized(0.25F, 0.25F).clientTrackingRange(6).updateInterval(4).build("frag_grenade"));

    @SubscribeEvent
    public static void onAttributes(EntityAttributeCreationEvent event) {
        event.put(OPERATIVE.get(), OperativeEntity.createAttributes().build());
    }
}
