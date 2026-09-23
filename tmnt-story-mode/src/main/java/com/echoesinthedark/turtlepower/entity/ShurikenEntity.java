package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

public class ShurikenEntity extends ThrowableItemProjectile {
    public ShurikenEntity(EntityType<? extends ShurikenEntity> type, Level level) {
        super(type, level);
    }

    public ShurikenEntity(Level level, LivingEntity thrower) {
        super(ModEntities.SHURIKEN.get(), thrower, level);
    }

    @Override
    protected Item getDefaultItem() {
        return ModItems.SHURIKEN.get();
    }

    @Override
    protected float getGravity() {
        return 0.01F;
    }

    @Override
    protected void onHitEntity(EntityHitResult hit) {
        super.onHitEntity(hit);
        Entity target = hit.getEntity();
        Entity owner = getOwner();
        if (owner instanceof TurtleBrotherEntity || (target instanceof TurtleBrotherEntity b && b.isOwnedBy(owner))) {
            return;
        }
        float damage = owner instanceof Player ? 6.0F : 4.0F;
        target.hurt(damageSources().thrown(this, owner), damage);
    }

    @Override
    protected void onHitBlock(BlockHitResult hit) {
        super.onHitBlock(hit);
        if (!level().isClientSide && getOwner() instanceof Player p && !p.getAbilities().instabuild) {
            // Stuck in the wall: drop it so you can pick it back up.
            ItemEntity item = new ItemEntity(level(), getX(), getY(), getZ(), new ItemStack(ModItems.SHURIKEN.get()));
            item.setDeltaMovement(0, 0.1, 0);
            level().addFreshEntity(item);
        }
        playSound(SoundEvents.CHAIN_HIT, 0.6F, 1.6F);
    }

    @Override
    protected void onHit(HitResult result) {
        super.onHit(result);
        if (!level().isClientSide) {
            ((ServerLevel) level()).sendParticles(new ItemParticleOption(ParticleTypes.ITEM, getItem()),
                    getX(), getY(), getZ(), 4, 0.1, 0.1, 0.1, 0.05);
            discard();
        }
    }
}
