package com.echoesinthedark.echostrike.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** Slap in a plate: +4 absorption hearts (max 8) that soak damage before your health does. */
public class ArmorPlateItem extends Item {
    public static final float PER_PLATE = 8.0F;
    public static final float MAX = 16.0F;

    public ArmorPlateItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getAbsorptionAmount() >= MAX) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.literal("Plates full").withStyle(ChatFormatting.GRAY), true);
            }
            return InteractionResultHolder.fail(stack);
        }
        if (!level.isClientSide) {
            player.setAbsorptionAmount(Math.min(MAX, player.getAbsorptionAmount() + PER_PLATE));
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARMOR_EQUIP_NETHERITE, SoundSource.PLAYERS, 0.8F, 1.2F);
            if (!player.getAbilities().instabuild) {
                stack.shrink(1);
            }
        }
        player.getCooldowns().addCooldown(this, 30);
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Right click: +4 shield hearts (up to 8).").withStyle(ChatFormatting.GRAY));
    }
}
