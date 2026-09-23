package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.Dialogue;
import com.echoesinthedark.turtlepower.story.Speaker;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RangedAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;

/**
 * Kraang droid: a robot body with a pink alien brain riding in its belly. Shoots laser bolts and
 * talks in the famous confusing Kraang way.
 */
public class KraangDroidEntity extends Monster implements RangedAttackMob {
    public static final DustParticleOptions PINK = new DustParticleOptions(new Vector3f(1.0F, 0.45F, 0.8F), 1.0F);

    static final String[] SPOTTED = {
            "Kraang has detected the ones known as the turtles, which are turtles.",
            "Attention, Kraang. The turtles are here, in the place that is here.",
            "Kraang must stop the turtles from doing the thing they are doing.",
            "The one who is red, known as Raphael, is the one who is angry.",
            "Do not let the turtles take the mutagen that Kraang needs to take.",
    };
    static final String[] HURT = {
            "Kraang has been hit by the thing that hits.",
            "Kraang requires assistance from Kraang!",
            "This is not the outcome that Kraang has calculated.",
    };
    static final String[] DEATH = {
            "Kraang... must... retreat... to the place of retreating!",
            "Kraang's body of robot has been... broken.",
    };

    private int talkCooldown = 0;

    public KraangDroidEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        xpReward = 8;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new RangedAttackGoal(this, 1.0, 26, 42, 18.0F));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        targetSelector.addGoal(1, new HurtByTargetGoal(this, KraangDroidEntity.class).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, TurtleBrotherEntity.class, true));
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data, tag);
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.KRAANG_BLASTER.get()));
        setDropChance(EquipmentSlot.MAINHAND, 0.0F); // drops are handled in dropCustomDeathLoot
        return result;
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        KraangBoltEntity bolt = new KraangBoltEntity(level(), this);
        bolt.setDamage(boltDamage());
        double dx = target.getX() - getX();
        double dy = target.getY(0.45) - bolt.getY();
        double dz = target.getZ() - getZ();
        float inaccuracy = 10 - level().getDifficulty().getId() * 3;
        bolt.shoot(dx, dy, dz, 1.7F, inaccuracy);
        level().addFreshEntity(bolt);
        playSound(SoundEvents.BEACON_DEACTIVATE, 0.5F, 1.9F + random.nextFloat() * 0.2F);
        swing(net.minecraft.world.InteractionHand.MAIN_HAND);
    }

    protected float boltDamage() {
        return 4.0F;
    }

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        LivingEntity old = getTarget();
        super.setTarget(target);
        if (target != null && old == null && !level().isClientSide && talkCooldown <= 0) {
            talkCooldown = 400;
            speak(SPOTTED[random.nextInt(SPOTTED.length)], "kraang_spotted", 300);
        }
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        boolean hurt = super.hurt(source, amount);
        if (hurt && !level().isClientSide && isAlive() && random.nextInt(6) == 0) {
            speak(HURT[random.nextInt(HURT.length)], "kraang_hurt", 400);
        }
        return hurt;
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (!level().isClientSide && isDeadOrDying()) {
            speak(DEATH[random.nextInt(DEATH.length)], "kraang_death", 500);
            ((ServerLevel) level()).sendParticles(PINK, getX(), getY() + 1.0, getZ(), 30, 0.4, 0.6, 0.4, 0.0);
        }
    }

    protected void speak(String text, String key, int cooldown) {
        Dialogue.sayNearby((ServerLevel) level(), position(), 24.0, Speaker.KRAANG, text, Dialogue.Kind.COMBAT, key, cooldown);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (talkCooldown > 0) talkCooldown--;
        if (level().isClientSide && random.nextInt(8) == 0) {
            // the Kraang's brain glows in the robot's belly
            level().addParticle(PINK, getX() + (random.nextDouble() - 0.5) * 0.4, getY() + 1.0, getZ() + (random.nextDouble() - 0.5) * 0.4, 0, 0.02, 0);
        }
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean recentlyHit) {
        super.dropCustomDeathLoot(source, looting, recentlyHit);
        if (random.nextFloat() < 0.3F + looting * 0.1F) {
            spawnAtLocation(new ItemStack(ModItems.MUTAGEN_CANISTER.get()));
        }
        if (random.nextFloat() < 0.08F + looting * 0.03F) {
            spawnAtLocation(new ItemStack(ModItems.KRAANG_BLASTER.get()));
        }
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.BEACON_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.IRON_GOLEM_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 1.6F;
    }

    @Override
    protected float getSoundVolume() {
        return 0.6F;
    }

    @Override
    public void playAmbientSound() {
        SoundEvent s = getAmbientSound();
        if (s != null) {
            level().playSound(null, getX(), getY(), getZ(), s, SoundSource.HOSTILE, 0.25F, 2.0F);
        }
    }
}
