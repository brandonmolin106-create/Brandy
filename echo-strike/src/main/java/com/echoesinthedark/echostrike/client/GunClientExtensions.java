package com.echoesinthedark.echostrike.client;

import com.echoesinthedark.echostrike.item.GunItem;
import com.echoesinthedark.echostrike.item.GunType;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/**
 * First-person gun animation. Forge calls this right before the held item is drawn, so the gun
 * can be moved and tilted for recoil, aiming down sights, reloading and sprinting. All of it is
 * procedural: no animation files, just math on the pose stack.
 */
public final class GunClientExtensions implements IClientItemExtensions {
    public static final GunClientExtensions INSTANCE = new GunClientExtensions();

    private GunClientExtensions() {}

    @Override
    public boolean applyForgeHandTransform(PoseStack pose, LocalPlayer player, HumanoidArm arm, ItemStack stack,
                                           float partialTick, float equipProcess, float swingProcess) {
        if (!(stack.getItem() instanceof GunItem gun)) return false;
        GunType type = gun.type;
        float side = arm == HumanoidArm.RIGHT ? 1.0F : -1.0F;

        float ads = GunController.zoomProgress(partialTick);
        float kick = GunController.kickProgress(partialTick);
        float sprint = GunController.sprintProgress(partialTick);
        float reload = GunController.reloadAnim(stack, partialTick);

        // Where the gun rests from the hip (vanilla's numbers) and where it sits when aiming.
        float hipX = 0.56F, hipY = -0.52F, hipZ = -0.72F;
        float adsX = type.is(GunType.Class.SNIPER) ? 0.0F : 0.03F;
        float adsY = type.is(GunType.Class.SNIPER) ? -0.26F : -0.33F;
        float adsZ = type.is(GunType.Class.SNIPER) ? -0.5F : -0.9F;
        float x = Mth.lerp(ads, hipX, adsX) * side;
        float y = Mth.lerp(ads, hipY, adsY) - 0.6F * equipProcess;
        float z = Mth.lerp(ads, hipZ, adsZ);
        pose.translate(x, y, z);

        // Sprint: swing the gun across the body and point it down a little.
        if (sprint > 0) {
            pose.translate(-0.12F * sprint * side, -0.08F * sprint, 0.05F * sprint);
            pose.mulPose(Axis.YP.rotationDegrees(38.0F * sprint * side));
            pose.mulPose(Axis.XP.rotationDegrees(-18.0F * sprint));
        }

        // Reload: tilt the gun down and roll it toward you, then bring it back.
        if (reload > 0) {
            float r = Mth.sin(reload * Mth.PI);
            pose.translate(0.0F, -0.18F * r, 0.0F);
            pose.mulPose(Axis.XP.rotationDegrees(35.0F * r));
            pose.mulPose(Axis.ZP.rotationDegrees(-25.0F * r * side));
        }

        // Recoil: the gun jumps back and the muzzle climbs, then settles.
        if (kick > 0) {
            float strength = 0.35F + type.recoilVertical * 0.09F;
            pose.translate(0.0F, 0.01F * kick * strength, 0.11F * kick * strength);
            pose.mulPose(Axis.XP.rotationDegrees(-9.0F * kick * strength));
            pose.mulPose(Axis.ZP.rotationDegrees(3.0F * kick * strength * side));
        }
        return true;
    }
}
