package com.echoesinthedark.turtlepower.item;

import com.echoesinthedark.turtlepower.entity.KraangBoltEntity;
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

/** Laser gun dropped by Kraang droids. */
public class KraangBlasterItem extends Item {
    public KraangBlasterItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6F, 2.0F);
        if (!level.isClientSide) {
            KraangBoltEntity bolt = new KraangBoltEntity(level, player);
            bolt.setDamage(6.0F);
            bolt.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 2.6F, 0.2F);
            level.addFreshEntity(bolt);
            stack.hurtAndBreak(1, player, p -> p.broadcastBreakEvent(hand));
        }
        player.getCooldowns().addCooldown(this, 8);
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Kraang tech. The Kraang call it \"the weapon of blasting, which blasts.\"")
                .withStyle(ChatFormatting.LIGHT_PURPLE));
    }
}
