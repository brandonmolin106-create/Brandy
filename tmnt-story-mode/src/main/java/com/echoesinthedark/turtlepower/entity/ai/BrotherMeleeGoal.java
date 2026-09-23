package com.echoesinthedark.turtlepower.entity.ai;

import com.echoesinthedark.turtlepower.entity.Brother;
import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

import java.util.EnumSet;

/** Melee fighting with each brother's own attack speed (Mikey fast, Donnie slow but with reach). */
public class BrotherMeleeGoal extends Goal {
    private final TurtleBrotherEntity mob;
    private final double speed;
    private int cooldown;
    private int repath;

    public BrotherMeleeGoal(TurtleBrotherEntity mob, double speed) {
        this.mob = mob;
        this.speed = speed;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity t = mob.getTarget();
        return t != null && t.isAlive() && mob.canAttack(t);
    }

    @Override
    public boolean canContinueToUse() {
        return canUse();
    }

    @Override
    public void start() {
        repath = 0;
    }

    @Override
    public void stop() {
        mob.getNavigation().stop();
        LivingEntity t = mob.getTarget();
        if (t != null && !t.isAlive()) {
            mob.setTarget(null);
        }
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        LivingEntity target = mob.getTarget();
        if (target == null) {
            return;
        }
        mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
        if (--repath <= 0) {
            repath = 4 + mob.getRandom().nextInt(6);
            mob.getNavigation().moveTo(target, speed);
        }
        if (cooldown > 0) {
            cooldown--;
        }
        double reach = mob.getBbWidth() * 2.0 * mob.getBbWidth() * 2.0 + target.getBbWidth();
        if (mob.brother() == Brother.DONNIE) {
            reach += 2.5; // bo staff
        }
        if (cooldown <= 0 && mob.distanceToSqr(target) <= reach + 1.0 && mob.hasLineOfSight(target)) {
            mob.swing(InteractionHand.MAIN_HAND);
            mob.doHurtTarget(target);
            cooldown = mob.brother().attackInterval;
        }
    }
}
