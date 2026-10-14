package com.echoesinthedark.echostrike.combat;

import com.echoesinthedark.echostrike.entity.OperativeEntity;
import com.echoesinthedark.echostrike.game.StrikeGame;
import com.echoesinthedark.echostrike.item.GunType;
import com.echoesinthedark.echostrike.network.HitmarkerPacket;
import com.echoesinthedark.echostrike.network.ModNetwork;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.network.PacketDistributor;
import org.jetbrains.annotations.Nullable;

/**
 * Hitscan shooting shared by players and operatives. A shot is a ray from the shooter's eyes;
 * the first block or living thing it crosses gets hit. Hits above the target's shoulders are
 * headshots and do extra damage.
 */
public final class Gunplay {
    private Gunplay() {}

    private static final boolean DEVTEST = System.getProperty("echostrike.devtest") != null;

    /** Multiplies the cone of fire. Aiming tightens it, sprinting and jumping open it up. */
    public static float spreadMultiplier(LivingEntity shooter, boolean aiming) {
        float m = aiming ? 0.35F : 1.0F;
        if (shooter.isSprinting()) m *= 1.8F;
        if (!shooter.onGround()) m *= 1.5F;
        if (shooter.isCrouching()) m *= 0.8F;
        return m;
    }

    /** A player pulls the trigger. Spread and damage come from the gun type. */
    public static void fire(Player player, GunType gun, boolean aiming) {
        float spread = gun.spread * spreadMultiplier(player, aiming);
        float damage = gun.damage;
        if (!player.level().isClientSide) {
            shoot(player, gun, spread, damage, gun.pellets, 1.0F);
        }
    }

    /**
     * Fire a shot from any living thing.
     *
     * @param spreadDeg   cone of fire in degrees
     * @param damageScale 1 for players, lower for enemy operatives so they don't two-tap you
     */
    public static void shoot(LivingEntity shooter, GunType gun, float spreadDeg, float damage, int pellets, float damageScale) {
        Level level = shooter.level();
        if (!(level instanceof ServerLevel sl)) return;
        RandomSource rand = shooter.getRandom();
        Vec3 eye = shooter.getEyePosition();
        Vec3 look = shooter.getLookAngle();

        level.playSound(null, shooter.getX(), shooter.getY(), shooter.getZ(), gun.sound, SoundSource.PLAYERS, gun.volume, gun.pitch + (rand.nextFloat() - 0.5F) * 0.1F);
        Vec3 muzzle = eye.add(look.scale(0.9));
        sl.sendParticles(ParticleTypes.SMOKE, muzzle.x, muzzle.y - 0.1, muzzle.z, 2, 0.05, 0.05, 0.05, 0.01);
        sl.sendParticles(ParticleTypes.FLAME, muzzle.x, muzzle.y - 0.1, muzzle.z, 1, 0.0, 0.0, 0.0, 0.0);

        boolean anyHit = false, anyHead = false, anyKill = false;
        for (int i = 0; i < pellets; i++) {
            Vec3 dir = scatter(look, spreadDeg, rand);
            Vec3 end = eye.add(dir.scale(gun.range));

            BlockHitResult blockHit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, shooter));
            Vec3 stop = blockHit.getType() == HitResult.Type.MISS ? end : blockHit.getLocation();

            AABB box = shooter.getBoundingBox().expandTowards(dir.scale(gun.range)).inflate(1.0);
            EntityHitResult entityHit = ProjectileUtil.getEntityHitResult(level, shooter, eye, stop, box,
                    e -> e != shooter && e.isAlive() && e.isPickable() && !e.isSpectator() && !e.isPassengerOfSameVehicle(shooter)
                            && !(shooter instanceof OperativeEntity op && e instanceof OperativeEntity other && op.sameTeam(other)));

            Vec3 impact = stop;
            if (entityHit != null) {
                Entity target = entityHit.getEntity();
                impact = entityHit.getLocation();
                boolean headshot = isHeadshot(target, impact);
                float dmg = damage * damageScale * (headshot ? gun.headshotMultiplier : 1.0F);
                // distance falloff for close range guns
                double dist = eye.distanceTo(impact);
                if (gun.is(GunType.Class.SHOTGUN) && dist > 6) dmg *= (float) Math.max(0.25, 1.0 - (dist - 6) / 12.0);
                if ((gun.is(GunType.Class.SMG) || gun.is(GunType.Class.PISTOL)) && dist > 24) dmg *= 0.75F;
                boolean wasAlive = target.isAlive();
                Vec3 before = target.getDeltaMovement();
                target.invulnerableTime = 0;
                boolean hurt = target.hurt(ModDamageTypes.bullet(level, shooter, headshot), dmg);
                if (hurt) {
                    anyHit = true;
                    anyHead |= headshot;
                    // Vanilla knockback would juggle people at SMG fire rates: keep their momentum
                    // and add only a tiny push (the hurt flag still syncs the velocity to clients).
                    if (target instanceof LivingEntity) {
                        target.setDeltaMovement(before.add(dir.x * 0.04, 0.0, dir.z * 0.04));
                    }
                    if (wasAlive && !target.isAlive()) {
                        anyKill = true;
                        if (shooter instanceof ServerPlayer sp) {
                            StrikeGame.get(sl.getServer()).onKill(sp, target);
                        }
                    }
                    sl.sendParticles(headshot ? ParticleTypes.CRIT : ParticleTypes.DAMAGE_INDICATOR, impact.x, impact.y, impact.z, headshot ? 8 : 4, 0.1, 0.1, 0.1, 0.1);
                    if (DEVTEST) {
                        com.echoesinthedark.echostrike.EchoStrike.LOGGER.info("DEVTEST hit {} with {} dmg={} headshot={} hpLeft={}",
                                target.getName().getString(), gun.id, dmg, headshot, target instanceof LivingEntity le ? le.getHealth() : -1);
                    }
                }
            } else if (blockHit.getType() == HitResult.Type.BLOCK) {
                sl.sendParticles(ParticleTypes.SMOKE, impact.x, impact.y, impact.z, 3, 0.05, 0.05, 0.05, 0.02);
                sl.sendParticles(ParticleTypes.CRIT, impact.x, impact.y, impact.z, 2, 0.1, 0.1, 0.1, 0.05);
            }
            tracer(sl, muzzle, impact);
        }

        if (shooter instanceof ServerPlayer sp && anyHit) {
            ModNetwork.CHANNEL.send(PacketDistributor.PLAYER.with(() -> sp),
                    new HitmarkerPacket(anyKill ? HitmarkerPacket.KILL : anyHead ? HitmarkerPacket.HEADSHOT : HitmarkerPacket.HIT));
        }
    }

    /** Rotate the look vector by a random angle inside a cone. */
    private static Vec3 scatter(Vec3 look, float spreadDeg, RandomSource rand) {
        if (spreadDeg <= 0) return look;
        // Gaussian-ish: most shots near the center.
        float angle = (float) Math.toRadians(spreadDeg) * (rand.nextFloat() + rand.nextFloat()) * 0.5F;
        float around = rand.nextFloat() * Mth.TWO_PI;
        Vec3 any = Math.abs(look.y) < 0.9 ? new Vec3(0, 1, 0) : new Vec3(1, 0, 0);
        Vec3 u = look.cross(any).normalize();
        Vec3 v = look.cross(u).normalize();
        Vec3 off = u.scale(Math.cos(around)).add(v.scale(Math.sin(around))).scale(Math.tan(angle));
        return look.add(off).normalize();
    }

    private static boolean isHeadshot(Entity target, Vec3 hit) {
        if (!(target instanceof LivingEntity le) || le.getBbHeight() < 1.0F) return false;
        double headTop = le.getY() + le.getBbHeight();
        double headBottom = le.getEyeY() - 0.25;
        return hit.y >= headBottom && hit.y <= headTop + 0.3;
    }

    private static void tracer(ServerLevel level, Vec3 from, Vec3 to) {
        double len = from.distanceTo(to);
        int points = (int) Math.min(14, len / 1.5);
        if (points <= 0) return;
        Vec3 step = to.subtract(from).scale(1.0 / points);
        Vec3 p = from.add(step.scale(0.5));
        for (int i = 0; i < points; i++) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            p = p.add(step);
        }
    }

    @Nullable
    public static LivingEntity asLiving(Entity e) {
        return e instanceof LivingEntity le ? le : null;
    }
}
