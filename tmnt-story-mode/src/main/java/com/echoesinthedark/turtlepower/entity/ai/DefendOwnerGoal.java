package com.echoesinthedark.turtlepower.entity.ai;

import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.target.TargetGoal;
import net.minecraft.world.entity.ai.targeting.TargetingConditions;
import net.minecraft.world.entity.player.Player;

import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;

/**
 * The important one: the moment anything tries to attack Raph (it has him as its target) or actually
 * hurts him, the brothers go after it.
 */
public class DefendOwnerGoal extends TargetGoal {
    private final TurtleBrotherEntity brother;
    private LivingEntity threat;
    private int lastHurtTimestamp;

    public DefendOwnerGoal(TurtleBrotherEntity brother) {
        super(brother, false);
        this.brother = brother;
        setFlags(EnumSet.of(Flag.TARGET));
    }

    @Override
    public boolean canUse() {
        Player owner = brother.getOwner();
        if (owner == null) {
            return false;
        }
        // 1. Whoever just hurt Raph.
        LivingEntity attacker = owner.getLastHurtByMob();
        int ts = owner.getLastHurtByMobTimestamp();
        if (attacker != null && ts != lastHurtTimestamp && valid(attacker)) {
            threat = attacker;
            return true;
        }
        // 2. Anything that has Raph in its sights.
        List<Mob> hunters = brother.level().getEntitiesOfClass(Mob.class, owner.getBoundingBox().inflate(18.0),
                m -> m.isAlive() && m.getTarget() == owner && valid(m));
        if (hunters.isEmpty()) {
            return false;
        }
        LivingEntity current = brother.getTarget();
        if (current != null && current.isAlive() && hunters.contains(current)) {
            return false; // already on it
        }
        threat = hunters.stream().min(Comparator.comparingDouble(brother::distanceToSqr)).orElse(null);
        return threat != null;
    }

    private boolean valid(LivingEntity e) {
        return !brother.isFriendly(e) && canAttack(e, TargetingConditions.DEFAULT.ignoreLineOfSight().ignoreInvisibilityTesting());
    }

    @Override
    public void start() {
        brother.setTarget(threat);
        Player owner = brother.getOwner();
        if (owner != null) {
            lastHurtTimestamp = owner.getLastHurtByMobTimestamp();
        }
        super.start();
    }
}
