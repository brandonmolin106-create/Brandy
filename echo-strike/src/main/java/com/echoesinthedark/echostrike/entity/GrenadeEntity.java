package com.echoesinthedark.echostrike.entity;

import com.echoesinthedark.echostrike.registry.ModEntities;
import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Thrown frag grenade. Bounces off blocks, blows up after the fuse. Never breaks blocks. */
public class GrenadeEntity extends ThrowableItemProjectile {
    public static final int FUSE = 40;
    public static final float POWER = 2.8F;

    private int fuse = FUSE;
    private boolean resting;

    public GrenadeEntity(EntityType<? extends GrenadeEntity> type, Level level) {
        super(type, level);
    }

    public GrenadeEntity(Level level, LivingEntity thrower) {
        super(ModEntities.FRAG_GRENADE.get(), thrower, level);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.FRAG_GRENADE.get();
    }

    @Override
    protected float getGravity() {
        return resting ? 0.0F : 0.05F;
    }

    @Override
    public void tick() {
        if (resting) {
            setDeltaMovement(Vec3.ZERO);
        }
        super.tick();
        if (level().isClientSide) {
            level().addParticle(ParticleTypes.SMOKE, getX(), getY() + 0.1, getZ(), 0, 0.02, 0);
            return;
        }
        if (--fuse <= 0) {
            explode();
        } else if (fuse % 10 == 0) {
            level().playSound(null, getX(), getY(), getZ(), SoundEvents.NOTE_BLOCK_HAT.get(), SoundSource.NEUTRAL, 0.5F, 1.8F);
        }
    }

    private void explode() {
        if (!(level() instanceof ServerLevel)) return;
        // ExplosionInteraction.NONE: full damage and knockback, zero block damage.
        level().explode(this, getX(), getY(), getZ(), POWER, Level.ExplosionInteraction.NONE);
        discard();
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        // Bonk, then keep going a bit slower. The explosion does the damage.
        Entity target = hit.getEntity();
        if (target == getOwner()) return;
        setDeltaMovement(getDeltaMovement().scale(-0.3));
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        Vec3 v = getDeltaMovement();
        Vec3 n = new Vec3(hit.getDirection().getStepX(), hit.getDirection().getStepY(), hit.getDirection().getStepZ());
        // Reflect the velocity on the face we hit and lose some energy.
        Vec3 reflected = v.subtract(n.scale(2 * v.dot(n))).scale(0.45);
        if (hit.getDirection().getStepY() > 0 && reflected.length() < 0.12) {
            resting = true;
            setDeltaMovement(Vec3.ZERO);
            setPos(getX(), hit.getLocation().y + 0.05, getZ());
        } else {
            setDeltaMovement(reflected);
            setPos(hit.getLocation().add(n.scale(0.1)));
        }
        level().playSound(null, getX(), getY(), getZ(), SoundEvents.METAL_HIT, SoundSource.NEUTRAL, 0.5F, 1.5F);
    }

    @Override
    protected void onHit(HitResult result) {
        // Don't discard on hit like a snowball would; onHitBlock / onHitEntity handle the bounce.
        if (result.getType() == HitResult.Type.ENTITY) {
            onHitEntity((EntityHitResult) result);
        } else if (result.getType() == HitResult.Type.BLOCK) {
            onHitBlock((BlockHitResult) result);
        }
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Fuse", fuse);
        tag.putBoolean("Resting", resting);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        fuse = tag.getInt("Fuse");
        resting = tag.getBoolean("Resting");
    }
}
