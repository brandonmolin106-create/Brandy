package com.echoesinthedark.turtlepower.entity.ai;

import com.echoesinthedark.turtlepower.entity.TurtleBrotherEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;

import java.util.EnumSet;

/** Keep close to Raph. Teleporting when left behind is handled in the entity tick. */
public class FollowBrotherGoal extends Goal {
    private final TurtleBrotherEntity mob;
    private final double speed;
    private final float startDist;
    private final float stopDist;
    private Player owner;
    private int repath;

    public FollowBrotherGoal(TurtleBrotherEntity mob, double speed, float startDist, float stopDist) {
        this.mob = mob;
        this.speed = speed;
        this.startDist = startDist;
        this.stopDist = stopDist;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        Player p = mob.getOwner();
        if (p == null || p.isSpectator() || mob.getTarget() != null) {
            return false;
        }
        if (mob.distanceToSqr(p) < startDist * startDist) {
            return false;
        }
        owner = p;
        return true;
    }

    @Override
    public boolean canContinueToUse() {
        return owner != null && owner.isAlive() && mob.getTarget() == null
                && mob.distanceToSqr(owner) > stopDist * stopDist;
    }

    @Override
    public void start() {
        repath = 0;
    }

    @Override
    public void stop() {
        owner = null;
        mob.getNavigation().stop();
    }

    @Override
    public void tick() {
        mob.getLookControl().setLookAt(owner, 10.0F, mob.getMaxHeadXRot());
        if (--repath <= 0) {
            repath = adjustedTickDelay(8);
            // Run a bit faster when far behind.
            double s = mob.distanceToSqr(owner) > 10 * 10 ? speed * 1.25 : speed;
            mob.getNavigation().moveTo(owner, s);
        }
    }
}
