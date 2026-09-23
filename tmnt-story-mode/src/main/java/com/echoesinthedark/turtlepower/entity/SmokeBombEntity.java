package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;

/** Ninja smoke bomb: blinds and confuses enemies, and hides whoever threw it. */
public class SmokeBombEntity extends ThrowableItemProjectile {
    public SmokeBombEntity(EntityType<? extends SmokeBombEntity> type, Level level) {
        super(type, level);
    }

    public SmokeBombEntity(Level level, LivingEntity thrower) {
        super(ModEntities.SMOKE_BOMB.get(), thrower, level);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.SMOKE_BOMB.get();
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        level.sendParticles(ParticleTypes.CAMPFIRE_SIGNAL_SMOKE, getX(), getY() + 0.5, getZ(), 40, 1.5, 0.8, 1.5, 0.01);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.5, getZ(), 80, 2.0, 1.0, 2.0, 0.02);
        level.playSound(null, getX(), getY(), getZ(), SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 1.2F, 0.8F);

        for (Mob mob : level.getEntitiesOfClass(Mob.class, getBoundingBox().inflate(5.0), m -> m instanceof Enemy)) {
            mob.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 100, 0));
            mob.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 80, 2));
            mob.setTarget(null);
        }
        Entity owner = getOwner();
        if (owner instanceof LivingEntity thrower && thrower.distanceToSqr(this) < 7 * 7) {
            thrower.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 120, 0));
            thrower.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 120, 1));
        }
        discard();
    }
}
