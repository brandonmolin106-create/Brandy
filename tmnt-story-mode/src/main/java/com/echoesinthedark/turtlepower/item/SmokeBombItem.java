package com.echoesinthedark.turtlepower.item;

import com.echoesinthedark.turtlepower.entity.SmokeBombEntity;
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

public class SmokeBombItem extends Item {
    public SmokeBombItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.SNOWBALL_THROW, SoundSource.PLAYERS, 0.6F, 0.6F);
        if (!level.isClientSide) {
            SmokeBombEntity bomb = new SmokeBombEntity(level, player);
            bomb.setItem(stack);
            bomb.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 1.2F, 0.8F);
            level.addFreshEntity(bomb);
        }
        player.getCooldowns().addCooldown(this, 20);
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Ninja vanish! Blinds enemies. If you are close to the smoke you turn invisible and fast.")
                .withStyle(ChatFormatting.GRAY));
    }
}
