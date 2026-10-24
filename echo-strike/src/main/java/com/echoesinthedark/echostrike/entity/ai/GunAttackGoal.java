package com.echoesinthedark.echostrike.entity.ai;

import com.echoesinthedark.echostrike.combat.Gunplay;
import com.echoesinthedark.echostrike.entity.OperativeEntity;
import com.echoesinthedark.echostrike.item.GunType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

import java.util.EnumSet;

/**
 * Shoot the target in bursts, strafe sideways while doing it, close in when too far and back
 * off when too close. Loosely based on the skeleton's bow goal.
 */
public class GunAttackGoal extends Goal {
    private final OperativeEntity mob;
    private int seeTime;
    private int burstLeft;
    private int cooldown;
    private int strafeTime = -1;
    private boolean strafeClockwise;
    private boolean strafeBackwards;

    public GunAttackGoal(OperativeEntity mob) {
        this.mob = mob;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        return mob.getTarget() != null && mob.getTarget().isAlive() && mob.heldGun() != null;
    }

    @Override
    public boolean canContinueToUse() {
        return canUse() || !mob.getNavigation().isDone();
    }

    @Override
    public void stop() {
        seeTime = 0;
        burstLeft = 0;
        mob.getMoveControl().strafe(0, 0);
        mob.setAggressive(false);
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        LivingEntity target = mob.getTarget();
        GunType gun = mob.heldGun();
        if (target == null || gun == null) return;
        mob.setAggressive(true);

        double dist = mob.distanceTo(target);
        boolean sees = mob.getSensing().hasLineOfSight(target);
        seeTime = sees ? Math.max(1, seeTime + 1) : Math.min(-1, seeTime - 1);

        double preferred = switch (gun.weaponClass) {
            case SHOTGUN -> 6.0;
            case SNIPER -> 28.0;
            case PISTOL, SMG -> 10.0;
            default -> 16.0;
        };

        if (dist > preferred * 1.6 || seeTime < -20) {
            mob.getNavigation().moveTo(target, 1.1);
            strafeTime = -1;
        } else {
            mob.getNavigation().stop();
            strafeTime++;
        }

        if (strafeTime >= 20) {
            if (mob.getRandom().nextFloat() < 0.3F) strafeClockwise = !strafeClockwise;
            if (mob.getRandom().nextFloat() < 0.3F) strafeBackwards = !strafeBackwards;
            strafeTime = 0;
        }
        if (strafeTime > -1) {
            if (dist > preferred * 1.2) strafeBackwards = false;
            else if (dist < preferred * 0.6) strafeBackwards = true;
            mob.getMoveControl().strafe(strafeBackwards ? -0.5F : 0.5F, strafeClockwise ? 0.5F : -0.5F);
            mob.lookAt(target, 30.0F, 30.0F);
        } else {
            mob.getLookControl().setLookAt(target, 30.0F, 30.0F);
        }

        if (cooldown > 0) {
            cooldown--;
            return;
        }
        if (seeTime < 3 || dist > gun.range) return;

        if (burstLeft <= 0) {
            burstLeft = gun.auto ? 3 + mob.getRandom().nextInt(4) : 1;
        }
        mob.lookAt(target, 60.0F, 60.0F);
        // Operatives are deliberately a bit wild so a fight lasts longer than two seconds.
        int tier = mob.getTier();
        float spread = gun.spread * 1.5F + Math.max(0, 7 - tier * 1.2F);
        float damageScale = 0.3F + tier * 0.08F;
        Gunplay.shoot(mob, gun, spread, gun.damage, gun.pellets, damageScale);
        mob.swing(net.minecraft.world.InteractionHand.MAIN_HAND);
        burstLeft--;
        cooldown = burstLeft > 0 ? Math.max(2, gun.ticksPerShot) : gun.ticksPerShot + 24 + mob.getRandom().nextInt(20) - tier * 3;
    }
}
