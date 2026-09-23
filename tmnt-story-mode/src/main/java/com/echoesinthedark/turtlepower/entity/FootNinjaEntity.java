package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.Dialogue;
import com.echoesinthedark.turtlepower.story.Speaker;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import org.jetbrains.annotations.Nullable;

/** Shredder's Foot Clan. Fast, leaps at you, throws shuriken, and smoke-vanishes when hurt. */
public class FootNinjaEntity extends Monster {
    private static final String[] TAUNTS = {
            "For the Shredder!",
            "The Foot Clan will find your lair, turtle.",
            "Surrender, freak!",
    };

    private int shurikenCooldown = 60;
    private boolean vanished;

    public FootNinjaEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        xpReward = 8;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.MOVEMENT_SPEED, 0.33)
                .add(Attributes.FOLLOW_RANGE, 28.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new LeapAtTargetGoal(this, 0.45F));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, false));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.9));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        targetSelector.addGoal(1, new HurtByTargetGoal(this, FootNinjaEntity.class).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, TurtleBrotherEntity.class, true));
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data, tag);
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.KATANA.get()));
        setDropChance(EquipmentSlot.MAINHAND, 0.04F);
        return result;
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        LivingEntity target = getTarget();
        if (target == null) {
            return;
        }
        if (--shurikenCooldown <= 0) {
            double d = distanceToSqr(target);
            if (d > 5 * 5 && d < 16 * 16 && hasLineOfSight(target)) {
                shurikenCooldown = 50 + random.nextInt(40);
                ShurikenEntity star = new ShurikenEntity(level(), this);
                star.setItem(new ItemStack(ModItems.SHURIKEN.get()));
                double dx = target.getX() - getX();
                double dy = target.getY(0.5) - star.getY();
                double dz = target.getZ() - getZ();
                star.shoot(dx, dy + Math.sqrt(dx * dx + dz * dz) * 0.05, dz, 1.6F, 6.0F);
                level().addFreshEntity(star);
                playSound(SoundEvents.TRIDENT_THROW, 0.6F, 1.8F);
            } else {
                shurikenCooldown = 10;
            }
        }
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        LivingEntity old = getTarget();
        super.setTarget(target);
        if (target != null && old == null && !level().isClientSide && random.nextInt(3) == 0) {
            Dialogue.sayNearby((ServerLevel) level(), position(), 20, Speaker.FOOT, TAUNTS[random.nextInt(TAUNTS.length)],
                    Dialogue.Kind.COMBAT, "foot_taunt", 400);
        }
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean hurt = super.hurt(source, amount);
        if (hurt && !vanished && isAlive() && getHealth() < getMaxHealth() * 0.35F && level() instanceof ServerLevel sl) {
            vanished = true;
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1, getZ(), 40, 0.6, 0.8, 0.6, 0.02);
            playSound(SoundEvents.FIRE_EXTINGUISH, 1.0F, 1.2F);
            for (int i = 0; i < 12; i++) {
                BlockPos p = blockPosition().offset(random.nextInt(13) - 6, random.nextInt(3) - 1, random.nextInt(13) - 6);
                if (randomTeleport(p.getX() + 0.5, p.getY(), p.getZ() + 0.5, false)) {
                    break;
                }
            }
            addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 60, 0));
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1, getZ(), 20, 0.4, 0.6, 0.4, 0.02);
        }
        return hurt;
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean recentlyHit) {
        super.dropCustomDeathLoot(source, looting, recentlyHit);
        if (random.nextFloat() < 0.6F) {
            spawnAtLocation(new ItemStack(ModItems.SHURIKEN.get(), 1 + random.nextInt(3 + looting)));
        }
        if (random.nextFloat() < 0.25F + looting * 0.05F) {
            spawnAtLocation(new ItemStack(ModItems.SMOKE_BOMB.get()));
        }
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PLAYER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PLAYER_DEATH;
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return distance > 8 && super.causeFallDamage(distance - 5, multiplier, source);
    }
}
