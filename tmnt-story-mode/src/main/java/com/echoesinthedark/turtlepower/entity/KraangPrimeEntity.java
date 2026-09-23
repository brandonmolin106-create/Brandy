package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.Dialogue;
import com.echoesinthedark.turtlepower.story.Speaker;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * The final boss: a giant Kraang battle droid. Fires laser spreads, calls in more droids, and slams
 * the ground when you get close.
 */
public class KraangPrimeEntity extends KraangDroidEntity {
    private final ServerBossEvent bossEvent = (ServerBossEvent) new ServerBossEvent(
            Component.literal("Kraang Prime"), BossEvent.BossBarColor.PINK, BossEvent.BossBarOverlay.NOTCHED_10)
            .setDarkenScreen(true);

    private int summonTimer = 160;
    private int slamTimer = 60;
    private int barrageTimer = 300;
    private boolean saidHalf;
    private boolean saidLow;

    public KraangPrimeEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        xpReward = 150;
        setPersistenceRequired();
        setCustomName(Component.literal("Kraang Prime"));
    }

    public static AttributeSupplier.Builder createPrimeAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 320.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.9)
                .add(Attributes.ATTACK_DAMAGE, 8.0);
    }

    @Override
    protected float boltDamage() {
        return 6.0F;
    }

    @Override
    public void performRangedAttack(LivingEntity target, float power) {
        // Three-way spread.
        for (int i = -1; i <= 1; i++) {
            KraangBoltEntity bolt = new KraangBoltEntity(level(), this);
            bolt.setDamage(boltDamage());
            Vec3 dir = new Vec3(target.getX() - getX(), target.getY(0.45) - bolt.getY(), target.getZ() - getZ());
            Vec3 side = dir.yRot((float) Math.toRadians(12 * i));
            bolt.shoot(side.x, side.y, side.z, 1.8F, 2.0F);
            level().addFreshEntity(bolt);
        }
        playSound(SoundEvents.BEACON_DEACTIVATE, 1.0F, 1.2F);
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        bossEvent.setProgress(getHealth() / getMaxHealth());
        LivingEntity target = getTarget();
        if (target == null) {
            return;
        }
        ServerLevel level = (ServerLevel) level();

        if (--summonTimer <= 0) {
            summonTimer = 400;
            List<KraangDroidEntity> helpers = level.getEntitiesOfClass(KraangDroidEntity.class, getBoundingBox().inflate(32),
                    e -> !(e instanceof KraangPrimeEntity));
            if (helpers.size() < 5) {
                for (int i = 0; i < 2; i++) {
                    KraangDroidEntity droid = ModEntities.KRAANG_DROID.get().create(level);
                    if (droid != null) {
                        BlockPos p = blockPosition().offset(random.nextInt(9) - 4, 0, random.nextInt(9) - 4);
                        droid.moveTo(p.getX() + 0.5, p.getY(), p.getZ() + 0.5, random.nextFloat() * 360, 0);
                        droid.finalizeSpawn(level, level.getCurrentDifficultyAt(p), MobSpawnType.REINFORCEMENT, null, null);
                        droid.setTarget(target);
                        level.addFreshEntity(droid);
                        level.sendParticles(ParticleTypes.PORTAL, droid.getX(), droid.getY() + 1, droid.getZ(), 40, 0.5, 1, 0.5, 0.5);
                    }
                }
                speak("Kraang, come to the place where Kraang Prime is, which is here!", "prime_summon", 300);
            }
        }

        if (--slamTimer <= 0 && distanceToSqr(target) < 5 * 5) {
            slamTimer = 90;
            level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 0.2, getZ(), 6, 1.5, 0.1, 1.5, 0.0);
            playSound(SoundEvents.GENERIC_EXPLODE, 1.0F, 0.7F);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(5.0),
                    e -> e != this && !(e instanceof KraangDroidEntity))) {
                e.hurt(damageSources().mobAttack(this), 6.0F);
                Vec3 push = e.position().subtract(position()).normalize().scale(1.4);
                e.push(push.x, 0.55, push.z);
                e.hurtMarked = true;
            }
        }

        if (getHealth() < getMaxHealth() * 0.5F && --barrageTimer <= 0) {
            barrageTimer = 260;
            speak("Kraang Prime will now do the thing of raining lasers, which rains.", "prime_barrage", 400);
            for (Player p : level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(24))) {
                for (int i = 0; i < 4; i++) {
                    KraangBoltEntity bolt = new KraangBoltEntity(level, this);
                    bolt.setDamage(4.0F);
                    bolt.setPos(p.getX() + random.nextGaussian() * 2, p.getY() + 9, p.getZ() + random.nextGaussian() * 2);
                    bolt.shoot(0, -1, 0, 1.2F, 0);
                    level.addFreshEntity(bolt);
                }
            }
        }

        if (!saidHalf && getHealth() < getMaxHealth() * 0.5F) {
            saidHalf = true;
            speak("This body of Kraang Prime is being damaged by the turtles who damage!", "prime_half", 20);
        }
        if (!saidLow && getHealth() < getMaxHealth() * 0.2F) {
            saidLow = true;
            speak("Kraang Prime... must... calculate... a new plan!", "prime_low", 20);
        }
    }

    @Override
    protected void speak(String text, String key, int cooldown) {
        Dialogue.sayNearby((ServerLevel) level(), position(), 48.0, Speaker.KRAANG_PRIME, text, Dialogue.Kind.STORY, key, cooldown);
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean recentlyHit) {
        spawnAtLocation(new ItemStack(ModItems.KRAANG_BLASTER.get()));
        spawnAtLocation(new ItemStack(ModItems.MUTAGEN_CANISTER.get(), 6));
        spawnAtLocation(new ItemStack(ModItems.RETRO_MUTAGEN.get(), 2));
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        bossEvent.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossEvent.removePlayer(player);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (hasCustomName()) {
            bossEvent.setName(getDisplayName());
        }
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean canChangeDimensions() {
        return false;
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return false;
    }
}
