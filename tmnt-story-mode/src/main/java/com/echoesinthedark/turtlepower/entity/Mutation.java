package com.echoesinthedark.turtlepower.entity;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.animal.Pig;
import net.minecraft.world.entity.animal.Rabbit;
import net.minecraft.world.entity.animal.AbstractFish;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.monster.Spider;
import net.minecraft.world.entity.monster.hoglin.Hoglin;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.animal.Wolf;
import net.minecraft.world.entity.animal.frog.Frog;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

/**
 * What mutagen does to living things. Most mobs just get a lot stronger (and a green "Mutant" name),
 * but a few turn into something else entirely, TMNT style.
 */
public final class Mutation {
    private Mutation() {}

    public static final String TAG = "turtlepower_mutant";
    private static final UUID HEALTH_ID = UUID.fromString("a4b1e8a2-9c21-4b1e-8e0b-1c2f3d4e5f60");
    private static final UUID DAMAGE_ID = UUID.fromString("b5c2f9b3-ad32-4c2f-9f1c-2d3e4f506171");
    private static final UUID SPEED_ID = UUID.fromString("c6d30ac4-be43-4d30-a02d-3e4f50617282");

    public static boolean isMutant(Mob mob) {
        return mob.getPersistentData().getBoolean(TAG);
    }

    public static boolean canMutate(Mob mob) {
        return !(mob instanceof TurtleBrotherEntity || mob instanceof StoryNpcEntity || mob instanceof TrainingDummyEntity
                || mob instanceof KraangDroidEntity || mob instanceof EnderDragon || mob instanceof WitherBoss)
                && !isMutant(mob);
    }

    /** Returns false if the mob can't be mutated (already a mutant, a boss, a friend...). */
    public static boolean mutate(ServerLevel level, Mob mob, @Nullable Player by) {
        if (!canMutate(mob)) {
            return false;
        }
        Mob result = transform(level, mob);
        if (result == null) {
            result = mob;
            applyBuffs(result, "Mutant " + mob.getType().getDescription().getString());
        }
        effects(level, result);
        if (by != null) {
            by.displayClientMessage(Component.literal("It's mutating! " + result.getName().getString() + "!")
                    .withStyle(ChatFormatting.GREEN), true);
        }
        return true;
    }

    /** Some animals turn into something completely new. */
    @Nullable
    private static Mob transform(ServerLevel level, Mob mob) {
        if (mob instanceof Pig) {
            Hoglin hog = replace(level, mob, EntityType.HOGLIN);
            if (hog != null) {
                hog.setImmuneToZombification(true);
                applyBuffs(hog, "Bebop Jr.");
            }
            return hog;
        }
        if (mob instanceof Cow) {
            Mob rhino = replace(level, mob, EntityType.RAVAGER);
            if (rhino != null) applyBuffs(rhino, "Rocksteady Jr.");
            return rhino;
        }
        if (mob instanceof AbstractFish) {
            Mob fish = replace(level, mob, EntityType.DROWNED);
            if (fish != null) applyBuffs(fish, "Fishface");
            return fish;
        }
        if (mob instanceof Rabbit rabbit) {
            rabbit.setVariant(Rabbit.Variant.EVIL);
            applyBuffs(rabbit, "Mutant Killer Bunny");
            return rabbit;
        }
        if (mob instanceof Wolf wolf && !wolf.isTame()) {
            applyBuffs(wolf, "Dogpound");
            return wolf;
        }
        if (mob instanceof Spider spider) {
            applyBuffs(spider, "Spider Bytez");
            return spider;
        }
        if (mob instanceof Frog frog) {
            applyBuffs(frog, "Napoleon Bonafrog");
            return frog;
        }
        return null;
    }

    @Nullable
    private static <T extends Mob> T replace(ServerLevel level, Mob old, EntityType<T> type) {
        T fresh = type.create(level);
        if (fresh == null) {
            return null;
        }
        fresh.moveTo(old.getX(), old.getY(), old.getZ(), old.getYRot(), old.getXRot());
        fresh.finalizeSpawn(level, level.getCurrentDifficultyAt(old.blockPosition()), MobSpawnType.CONVERSION, null, null);
        fresh.setPersistenceRequired();
        old.discard();
        level.addFreshEntity(fresh);
        return fresh;
    }

    public static void applyBuffs(Mob mob, String name) {
        mob.getPersistentData().putBoolean(TAG, true);
        addModifier(mob.getAttribute(Attributes.MAX_HEALTH), HEALTH_ID, 1.5);
        addModifier(mob.getAttribute(Attributes.ATTACK_DAMAGE), DAMAGE_ID, 0.6);
        addModifier(mob.getAttribute(Attributes.MOVEMENT_SPEED), SPEED_ID, 0.2);
        mob.setHealth(mob.getMaxHealth());
        mob.setCustomName(Component.literal(name).withStyle(ChatFormatting.GREEN));
        mob.setPersistenceRequired();
    }

    private static void addModifier(@Nullable AttributeInstance attr, UUID id, double amount) {
        if (attr != null && attr.getModifier(id) == null) {
            attr.addPermanentModifier(new AttributeModifier(id, "Mutagen", amount, AttributeModifier.Operation.MULTIPLY_TOTAL));
        }
    }

    public static void cure(ServerLevel level, Mob mob) {
        mob.getPersistentData().remove(TAG);
        for (var attr : new net.minecraft.world.entity.ai.attributes.Attribute[]{Attributes.MAX_HEALTH, Attributes.ATTACK_DAMAGE, Attributes.MOVEMENT_SPEED}) {
            AttributeInstance inst = mob.getAttribute(attr);
            if (inst != null) {
                inst.removeModifier(HEALTH_ID);
                inst.removeModifier(DAMAGE_ID);
                inst.removeModifier(SPEED_ID);
            }
        }
        mob.setHealth(Math.min(mob.getHealth(), mob.getMaxHealth()));
        mob.setCustomName(null);
        level.sendParticles(ParticleTypes.HAPPY_VILLAGER, mob.getX(), mob.getY() + 1, mob.getZ(), 20, 0.5, 0.6, 0.5, 0.0);
        level.playSound(null, mob.blockPosition(), SoundEvents.ZOMBIE_VILLAGER_CURE, SoundSource.NEUTRAL, 0.8F, 1.3F);
    }

    private static void effects(ServerLevel level, Mob mob) {
        level.sendParticles(net.minecraft.core.particles.ParticleTypes.SNEEZE, mob.getX(), mob.getY() + 1, mob.getZ(), 30, 0.5, 0.7, 0.5, 0.05);
        level.sendParticles(com.echoesinthedark.turtlepower.block.MutagenOozeBlock.GLOW, mob.getX(), mob.getY() + 1, mob.getZ(), 40, 0.6, 0.8, 0.6, 0.0);
        level.playSound(null, mob.blockPosition(), SoundEvents.ZOMBIE_VILLAGER_CONVERTED, SoundSource.HOSTILE, 1.0F, 0.7F);
    }
}
