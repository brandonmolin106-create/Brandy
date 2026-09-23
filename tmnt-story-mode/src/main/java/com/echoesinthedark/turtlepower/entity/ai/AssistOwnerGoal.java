package com.echoesinthedark.turtlepower.entity.ai;

import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.target.TargetGoal;
import net.minecraft.world.entity.ai.targeting.TargetingConditions;
import net.minecraft.world.entity.player.Player;

import java.util.EnumSet;

/** Whatever Raph hits, the brothers hit too. */
public class AssistOwnerGoal extends TargetGoal {
    private final TurtleBrotherEntity brother;
    private LivingEntity victim;
    private int timestamp;

    public AssistOwnerGoal(TurtleBrotherEntity brother) {
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
        victim = owner.getLastHurtMob();
        int ts = owner.getLastHurtMobTimestamp();
        return victim != null && ts != timestamp && victim.isAlive() && !brother.isFriendly(victim)
                && canAttack(victim, TargetingConditions.DEFAULT);
    }

    @Override
    public void start() {
        brother.setTarget(victim);
        Player owner = brother.getOwner();
        if (owner != null) {
            timestamp = owner.getLastHurtMobTimestamp();
        }
        super.start();
    }
}
