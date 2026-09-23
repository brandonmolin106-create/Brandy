package com.echoesinthedark.turtlepower.item;

import com.echoesinthedark.turtlepower.entity.ShurikenEntity;
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

public class ShurikenItem extends Item {
    public ShurikenItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.TRIDENT_THROW, SoundSource.PLAYERS, 0.6F, 1.8F);
        if (!level.isClientSide) {
            ShurikenEntity star = new ShurikenEntity(level, player);
            star.setItem(stack);
            star.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 2.2F, 0.4F);
            level.addFreshEntity(star);
        }
        player.getCooldowns().addCooldown(this, 5);
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Right click to throw. You can pick them back up.").withStyle(ChatFormatting.GRAY));
    }
}
