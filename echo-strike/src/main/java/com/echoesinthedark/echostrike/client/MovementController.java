package com.echoesinthedark.echostrike.client;

import com.echoesinthedark.echostrike.EchoStrike;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * BloodStrike-style movement, done on the client because that's where Minecraft moves the player:
 *
 * SLIDE: sprint and tap crouch. A burst of speed in the direction you're running that fades over
 *        about 3/4 of a second. Jump out of it to keep the momentum.
 * VAULT: run into a one block high obstacle and you hop it. Jump at a two block wall and you mantle
 *        over the top.
 * TAC SPRINT: handled on the server (faster sprint while holding a gun).
 */
@Mod.EventBusSubscriber(modid = EchoStrike.MODID, value = Dist.CLIENT)
public final class MovementController {
    private MovementController() {}

    private static final int SLIDE_TICKS = 15;

    private static int slideTicks;
    private static int slideCooldown;
    private static int vaultCooldown;
    private static boolean sneakWasDown;
    private static Vec3 slideDir = Vec3.ZERO;

    public static boolean isSliding() {
        return slideTicks > 0;
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.level == null || mc.isPaused()) return;
        if (slideCooldown > 0) slideCooldown--;
        if (vaultCooldown > 0) vaultCooldown--;

        boolean inGame = mc.screen == null;
        boolean sneak = inGame && mc.options.keyShift.isDown();
        boolean canMove = !p.getAbilities().flying && !p.isInWater() && !p.isPassenger() && !p.isFallFlying();

        // ---- slide
        if (slideTicks == 0 && slideCooldown == 0 && sneak && !sneakWasDown && p.isSprinting() && p.onGround() && canMove) {
            Vec3 v = p.getDeltaMovement();
            Vec3 horizontal = new Vec3(v.x, 0, v.z);
            slideDir = horizontal.lengthSqr() > 0.001 ? horizontal.normalize() : flatLook(p);
            slideTicks = SLIDE_TICKS;
            p.playSound(SoundEvents.GRAVEL_STEP, 0.8F, 0.55F);
        }
        sneakWasDown = sneak;

        if (slideTicks > 0) {
            if (!sneak || !canMove) {
                slideTicks = 0;
                slideCooldown = 10;
            } else {
                slideTicks--;
                double t = slideTicks / (double) SLIDE_TICKS;
                double speed = 0.85 * (0.3 + 0.7 * t);
                Vec3 v = p.getDeltaMovement();
                if (p.onGround()) {
                    p.setDeltaMovement(slideDir.x * speed, v.y, slideDir.z * speed);
                    if (slideTicks % 2 == 0) {
                        mc.level.addParticle(ParticleTypes.POOF, p.getX() - slideDir.x * 0.5, p.getY() + 0.1, p.getZ() - slideDir.z * 0.5, 0, 0.02, 0);
                    }
                }
                if (slideTicks == 0) slideCooldown = 14;
            }
        }

        // ---- vault / mantle
        if (vaultCooldown == 0 && slideTicks == 0 && canMove && inGame && p.input.forwardImpulse > 0.1F && p.horizontalCollision) {
            Vec3 look = flatLook(p);
            BlockPos front = BlockPos.containing(p.getX() + look.x * 0.75, p.getY() + 0.1, p.getZ() + look.z * 0.75);
            Vec3 v = p.getDeltaMovement();
            int height = 0;
            if (solid(mc, front) && free(mc, front.above()) && free(mc, front.above(2))) {
                height = 1;
            } else if (solid(mc, front.above()) && free(mc, front.above(2)) && free(mc, front.above(3)) && !p.onGround() && v.y > -0.25) {
                height = 2;
            }
            if (height > 0) {
                double up = height == 1 ? 0.48 : 0.58;
                p.setDeltaMovement(look.x * 0.28 + v.x * 0.4, up, look.z * 0.28 + v.z * 0.4);
                p.fallDistance = 0;
                vaultCooldown = 12;
                p.playSound(SoundEvents.ARMOR_EQUIP_LEATHER, 0.6F, 1.3F);
            }
        }
    }

    private static Vec3 flatLook(LocalPlayer p) {
        float yaw = (float) Math.toRadians(p.getYRot());
        return new Vec3(-Math.sin(yaw), 0, Math.cos(yaw));
    }

    private static boolean solid(Minecraft mc, BlockPos pos) {
        return !mc.level.getBlockState(pos).getCollisionShape(mc.level, pos).isEmpty();
    }

    private static boolean free(Minecraft mc, BlockPos pos) {
        return mc.level.getBlockState(pos).getCollisionShape(mc.level, pos).isEmpty();
    }

    @SuppressWarnings("unused")
    private static void sound(LocalPlayer p) {
        p.level().playLocalSound(p.getX(), p.getY(), p.getZ(), SoundEvents.GRAVEL_STEP, SoundSource.PLAYERS, 0.8F, 0.5F, false);
    }
}
