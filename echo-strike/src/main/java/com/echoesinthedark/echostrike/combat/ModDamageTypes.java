package com.echoesinthedark.echostrike.combat;

import com.echoesinthedark.echostrike.EchoStrike;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;

/** Damage types are data driven in 1.20: the JSON lives in data/echostrike/damage_type/. */
public final class ModDamageTypes {
    private ModDamageTypes() {}

    public static final ResourceKey<DamageType> BULLET = ResourceKey.create(Registries.DAMAGE_TYPE, EchoStrike.id("bullet"));
    public static final ResourceKey<DamageType> HEADSHOT = ResourceKey.create(Registries.DAMAGE_TYPE, EchoStrike.id("headshot"));

    public static DamageSource bullet(Level level, Entity shooter, boolean headshot) {
        Holder<DamageType> type = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE)
                .getHolderOrThrow(headshot ? HEADSHOT : BULLET);
        return new DamageSource(type, shooter, shooter);
    }
}
