package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/** Pink Kraang laser bolt. Flies straight, fizzles after 3 seconds. */
public class KraangBoltEntity extends ThrowableItemProjectile {
    private float damage = 4.0F;

    public KraangBoltEntity(EntityType<? extends KraangBoltEntity> type, Level level) {
        super(type, level);
    }

    public KraangBoltEntity(Level level, LivingEntity shooter) {
        super(ModEntities.KRAANG_BOLT.get(), shooter, level);
    }

    public void setDamage(float damage) {
        this.damage = damage;
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.KRAANG_BOLT.get();
    }

    @Override
    protected float getGravity() {
        return 0.0F;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            level().addParticle(KraangDroidEntity.PINK, getX(), getY(), getZ(), 0, 0, 0);
        } else if (tickCount > 60) {
            discard();
        }
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        Entity target = hit.getEntity();
        Entity owner = getOwner();
        if (owner instanceof KraangDroidEntity && target instanceof KraangDroidEntity) {
            return; // Kraang does not shoot Kraang
        }
        target.hurt(damageSources().thrown(this, owner), damage);
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (level() instanceof ServerLevel sl) {
            sl.sendParticles(KraangDroidEntity.PINK, getX(), getY(), getZ(), 10, 0.15, 0.15, 0.15, 0.0);
            discard();
        }
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putFloat("Damage", damage);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        damage = tag.getFloat("Damage");
    }
}
