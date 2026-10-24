package com.echoesinthedark.echostrike.entity;

import com.echoesinthedark.echostrike.entity.ai.GunAttackGoal;
import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
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

/**
 * Enemy soldier. Picks a gun when it spawns, strafes, takes cover-ish, shoots in bursts.
 * Operatives on different teams fight each other too, which makes Battle Royale bots work.
 */
public class OperativeEntity extends Monster {
    private static final EntityDataAccessor<Integer> TEAM = SynchedEntityData.defineId(OperativeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> TIER = SynchedEntityData.defineId(OperativeEntity.class, EntityDataSerializers.INT);

    public OperativeEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        xpReward = 10;
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        entityData.define(TEAM, 0);
        entityData.define(TIER, 0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new GunAttackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, OperativeEntity.class, 10, true, false,
                e -> e instanceof OperativeEntity other && !sameTeam(other)));
    }

    // ---------------------------------------------------------------- teams and tiers

    public int getSquad() {
        return entityData.get(TEAM);
    }

    public void setSquad(int team) {
        entityData.set(TEAM, team);
    }

    public boolean sameTeam(OperativeEntity other) {
        return other.getSquad() == getSquad();
    }

    /** 0 = grunt with a pistol, higher tiers get better guns, more health and better aim. */
    public int getTier() {
        return entityData.get(TIER);
    }

    public void setTier(int tier) {
        tier = Math.max(0, Math.min(4, tier));
        entityData.set(TIER, tier);
        GunType gun = switch (tier) {
            case 0 -> pick(GunType.G18, GunType.MP5, GunType.VECTOR);
            case 1 -> pick(GunType.UMP45, GunType.M4A1, GunType.DEAGLE);
            case 2 -> pick(GunType.M870, GunType.AK47, GunType.M4A1);
            case 3 -> pick(GunType.AWM, GunType.M249, GunType.AK47);
            default -> pick(GunType.AWM, GunType.M249);
        };
        setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.gunFor(gun)));
        setDropChance(EquipmentSlot.MAINHAND, 0.35F);
        getAttribute(Attributes.MAX_HEALTH).setBaseValue(30.0 + tier * 8.0);
        getAttribute(Attributes.ARMOR).setBaseValue(4.0 + tier * 2.0);
        setHealth(getMaxHealth());
        if (tier >= 2) {
            setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.STRIKE_VEST.get()));
            setDropChance(EquipmentSlot.CHEST, 0.1F);
        }
        if (tier >= 3) {
            setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModItems.STRIKE_HELMET.get()));
            setDropChance(EquipmentSlot.HEAD, 0.1F);
        }
    }

    private GunType pick(GunType... options) {
        return options[random.nextInt(options.length)];
    }

    @Nullable
    public GunType heldGun() {
        return getMainHandItem().getItem() instanceof GunItem g ? g.type : null;
    }

    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, MobSpawnType reason,
                                        @Nullable SpawnGroupData data, @Nullable CompoundTag tag) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data, tag);
        if (heldGun() == null) {
            setTier(random.nextInt(2));
        }
        return result;
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean recentlyHit) {
        super.dropCustomDeathLoot(source, looting, recentlyHit);
        GunType gun = heldGun();
        if (gun != null) {
            spawnAtLocation(new ItemStack(gun.ammo.get(), 6 + random.nextInt(10 + looting * 4)));
        }
        if (random.nextFloat() < 0.3F) spawnAtLocation(new ItemStack(ModItems.MEDKIT.get()));
        if (random.nextFloat() < 0.25F) spawnAtLocation(new ItemStack(ModItems.ARMOR_PLATE.get()));
        if (random.nextFloat() < 0.15F) spawnAtLocation(new ItemStack(ModItems.FRAG_GRENADE.get(), 1 + random.nextInt(2)));
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return distance > 6 && super.causeFallDamage(distance - 4, multiplier, source);
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
    protected boolean shouldDespawnInPeaceful() {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Team", getSquad());
        tag.putInt("Tier", getTier());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        setSquad(tag.getInt("Team"));
        entityData.set(TIER, tag.getInt("Tier"));
    }
}
