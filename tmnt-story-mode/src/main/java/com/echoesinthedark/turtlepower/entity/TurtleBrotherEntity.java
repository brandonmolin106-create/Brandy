package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.entity.ai.AssistOwnerGoal;
import com.echoesinthedark.turtlepower.entity.ai.BrotherMeleeGoal;
import com.echoesinthedark.turtlepower.entity.ai.DefendOwnerGoal;
import com.echoesinthedark.turtlepower.entity.ai.FollowBrotherGoal;
import com.echoesinthedark.turtlepower.story.Dialogue;
import com.echoesinthedark.turtlepower.story.StoryManager;
import com.echoesinthedark.turtlepower.Config;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import org.jetbrains.annotations.Nullable;

import java.util.Optional;
import java.util.UUID;

/**
 * Leonardo, Donatello or Michelangelo. Once they have an owner (you, Raphael) they:
 * <ul>
 *   <li>stay close to you and ninja-teleport back to you if they get left behind (ladders, manholes...)</li>
 *   <li>attack anything that is trying to attack you, anything that hurt you and anything you hit</li>
 *   <li>go after Kraang and Foot ninjas on sight</li>
 *   <li>never hurt you and can't really be killed: they get "shell-shocked" and bounce back</li>
 * </ul>
 */
public class TurtleBrotherEntity extends PathfinderMob {
    private static final EntityDataAccessor<Optional<UUID>> OWNER = SynchedEntityData.defineId(TurtleBrotherEntity.class, EntityDataSerializers.OPTIONAL_UUID);

    private int battleCryCooldown = 0;
    private int chatterTimer = 2400 + (int) (Math.random() * 2400);
    private int ownerMissingTicks = 0;
    private int stuckTicks = 0;
    private int regenTimer = 0;

    public TurtleBrotherEntity(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
        setPersistenceRequired();
        setMaxUpStep(1.0F);
        setPathfindingMalus(BlockPathTypes.WATER, 0.0F);
        setPathfindingMalus(BlockPathTypes.WATER_BORDER, 0.0F);
        if (getNavigation() instanceof GroundPathNavigation nav) {
            nav.setCanOpenDoors(true);
            nav.setCanFloat(true);
        }
        Brother b = brother();
        setCustomName(Component.literal(b.displayName).withStyle(b.color));
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.MOVEMENT_SPEED, 0.33)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.ATTACK_KNOCKBACK, 0.6)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.3);
    }

    public Brother brother() {
        return Brother.of(getType());
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        entityData.define(OWNER, Optional.empty());
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new BrotherMeleeGoal(this, 1.35));
        goalSelector.addGoal(2, new FollowBrotherGoal(this, 1.3, 4.5F, 2.5F));
        goalSelector.addGoal(3, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(4, new RandomLookAroundGoal(this));

        targetSelector.addGoal(1, new DefendOwnerGoal(this));
        targetSelector.addGoal(2, new AssistOwnerGoal(this));
        targetSelector.addGoal(3, new HurtByTargetGoal(this, TurtleBrotherEntity.class, Player.class));
        targetSelector.addGoal(4, new NearestAttackableTargetGoal<>(this, Mob.class, 10, true, false, TurtleBrotherEntity::isSwornEnemy));
    }

    /** Things the brothers attack on sight. */
    public static boolean isSwornEnemy(LivingEntity e) {
        return e instanceof KraangDroidEntity || e instanceof FootNinjaEntity
                || (e instanceof Mob m && Mutation.isMutant(m) && m instanceof net.minecraft.world.entity.monster.Enemy);
    }

    /** Things the brothers must never attack, even if you do. */
    public boolean isFriendly(LivingEntity e) {
        if (e == null) return true;
        if (e instanceof TurtleBrotherEntity || e instanceof StoryNpcEntity || e instanceof TrainingDummyEntity) return true;
        if (e instanceof Player) return true;
        if (e instanceof AbstractVillager || e instanceof IronGolem) return true;
        if (e instanceof net.minecraft.world.entity.TamableAnimal t && t.isTame()) return true;
        return false;
    }

    @Override
    public boolean canAttack(LivingEntity target) {
        return !isFriendly(target) && super.canAttack(target);
    }

    // ------------------------------------------------------------------ owner

    public Optional<UUID> getOwnerUUID() {
        return entityData.get(OWNER);
    }

    public void setOwner(@Nullable Player player) {
        entityData.set(OWNER, player == null ? Optional.empty() : Optional.of(player.getUUID()));
    }

    @Nullable
    public Player getOwner() {
        return getOwnerUUID().map(level()::getPlayerByUUID).orElse(null);
    }

    public boolean isOwnedBy(Entity e) {
        return e != null && getOwnerUUID().map(u -> u.equals(e.getUUID())).orElse(false);
    }

    // ------------------------------------------------------------------ spawning

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data, tag);
        equipWeapon();
        return result;
    }

    public void equipWeapon() {
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(brother().weapon()));
        setDropChance(EquipmentSlot.MAINHAND, 0.0F);
    }

    // ------------------------------------------------------------------ interaction

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (level().isClientSide) {
            return InteractionResult.SUCCESS;
        }
        ServerPlayer sp = (ServerPlayer) player;
        if (getOwnerUUID().isEmpty()) {
            setOwner(player);
            if (getMainHandItem().isEmpty()) equipWeapon();
            StoryManager.adoptBrother(sp, this);
            Dialogue.say(sp, brother().speaker, "Raph! Good to see you, bro. I'm with you.");
            return InteractionResult.SUCCESS;
        }
        if (isOwnedBy(player)) {
            StoryManager.brotherHint(sp, this);
            return InteractionResult.SUCCESS;
        }
        return InteractionResult.PASS;
    }

    // ------------------------------------------------------------------ combat

    @Override
    public void setTarget(@Nullable LivingEntity target) {
        LivingEntity old = getTarget();
        super.setTarget(target);
        if (target != null && target != old && !level().isClientSide && battleCryCooldown <= 0 && random.nextInt(3) == 0) {
            battleCryCooldown = 200 + random.nextInt(200);
            Player owner = getOwner();
            if (owner instanceof ServerPlayer sp && distanceToSqr(owner) < 32 * 32
                    && Dialogue.ready(sp, "battlecry", 100)) {
                Brother b = brother();
                Dialogue.say(sp, b.speaker, b.battleCries[random.nextInt(b.battleCries.length)], Dialogue.Kind.COMBAT);
            }
        }
    }

    @Override
    public boolean doHurtTarget(Entity target) {
        boolean hit = super.doHurtTarget(target);
        if (hit && onGround() && random.nextInt(5) == 0) {
            // Ninja flip!
            setDeltaMovement(getDeltaMovement().add(0, 0.42, 0));
        }
        return hit;
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        Entity attacker = source.getEntity();
        if (attacker != null && (isOwnedBy(attacker) || attacker instanceof TurtleBrotherEntity)) {
            return false;
        }
        if (attacker instanceof Player p && !p.isCreative() && getOwnerUUID().isPresent()) {
            return false;
        }
        return super.hurt(source, amount);
    }

    @Override
    public void die(DamageSource source) {
        if (level().isClientSide || source.is(DamageTypes.GENERIC_KILL)) {
            super.die(source);
            return;
        }
        // Brothers don't die. They get shell-shocked, shake it off and come back.
        setHealth(getMaxHealth() * 0.5F);
        addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 100, 3));
        addEffect(new MobEffectInstance(MobEffects.REGENERATION, 160, 1));
        setTarget(null);
        Player owner = getOwner();
        if (owner instanceof ServerPlayer sp) {
            Brother b = brother();
            Dialogue.say(sp, b.speaker, b.knockedOut[random.nextInt(b.knockedOut.length)], Dialogue.Kind.COMBAT);
            teleportToOwner(owner, true);
        }
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return false; // ninjas land on their feet
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true; // they're turtles
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.TURTLE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.TURTLE_DEATH;
    }

    @Override
    protected float getSoundVolume() {
        return 0.7F;
    }

    // ------------------------------------------------------------------ ticking

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide) {
            return;
        }
        if (battleCryCooldown > 0) battleCryCooldown--;

        Optional<UUID> ownerId = getOwnerUUID();
        if (ownerId.isEmpty()) {
            return;
        }
        Player owner = getOwner();
        if (owner == null || owner.isSpectator()) {
            // Owner is offline or in another dimension. The story manager will bring us back next to them.
            if (++ownerMissingTicks > 100) {
                discard();
            }
            return;
        }
        ownerMissingTicks = 0;

        if (!StoryManager.isCurrentBrother(owner, this)) {
            // An older copy of this brother that was replaced while its chunk was unloaded.
            discard();
            return;
        }

        if (tickCount % 10 == 0) {
            double dist = distanceToSqr(owner);
            if (dist > 20 * 20 && getTarget() != null) {
                setTarget(null); // don't chase enemies too far away from Raph
            }
            if (dist > 14 * 14) {
                teleportToOwner(owner, false);
            } else if (dist > 5 * 5 && getTarget() == null && getNavigation().isDone()) {
                if (++stuckTicks > 4) { // about two seconds without being able to walk to Raph
                    teleportToOwner(owner, false);
                }
            } else {
                stuckTicks = 0;
            }
        }

        if (getTarget() == null && ++regenTimer >= 40) {
            regenTimer = 0;
            if (getHealth() < getMaxHealth()) heal(1.0F);
        }

        if (getTarget() == null && Config.IDLE_CHATTER.get() && --chatterTimer <= 0) {
            chatterTimer = 3600 + random.nextInt(3600);
            if (owner instanceof ServerPlayer sp && distanceToSqr(owner) < 10 * 10 && Dialogue.ready(sp, "chatter", 1800)) {
                Brother b = brother();
                Dialogue.say(sp, b.speaker, b.chatter[random.nextInt(b.chatter.length)], Dialogue.Kind.CHATTER);
            }
        }
    }

    /** Ninja-vanish over to Raph. Returns true if we found a safe spot. */
    public boolean teleportToOwner(Player owner, boolean anywhere) {
        if (owner.level() != level()) {
            return false;
        }
        BlockPos base = owner.blockPosition();
        for (int i = 0; i < 16; i++) {
            int dx = random.nextInt(7) - 3;
            int dz = random.nextInt(7) - 3;
            int dy = random.nextInt(3) - 1;
            if (Math.abs(dx) < 1 && Math.abs(dz) < 1) continue;
            BlockPos p = base.offset(dx, dy, dz);
            if (canStandAt(p)) {
                poof();
                moveTo(p.getX() + 0.5, p.getY(), p.getZ() + 0.5, getYRot(), getXRot());
                getNavigation().stop();
                stuckTicks = 0;
                poof();
                return true;
            }
        }
        if (anywhere) {
            poof();
            moveTo(owner.getX(), owner.getY(), owner.getZ(), getYRot(), getXRot());
            getNavigation().stop();
            return true;
        }
        return false;
    }

    private boolean canStandAt(BlockPos p) {
        BlockPathTypes type = WalkNodeEvaluator.getBlockPathTypeStatic(level(), p.mutable());
        if (type != BlockPathTypes.WALKABLE) {
            return false;
        }
        return level().noCollision(this, getBoundingBox().move(p.getX() + 0.5 - getX(), p.getY() - getY(), p.getZ() + 0.5 - getZ()));
    }

    private void poof() {
        if (level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), getY() + 0.8, getZ(), 6, 0.3, 0.5, 0.3, 0.01);
        }
    }

    // ------------------------------------------------------------------ save data

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        getOwnerUUID().ifPresent(u -> tag.putUUID("Owner", u));
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Owner")) {
            entityData.set(OWNER, Optional.of(tag.getUUID("Owner")));
        }
    }
}
