package com.echoesinthedark.turtlepower.item;

import com.echoesinthedark.turtlepower.client.ClientHooks;
import com.echoesinthedark.turtlepower.story.StoryManager;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Donnie's T-Phone.
 * Right click: repeat the current objective and call your brothers to your side.
 * Sneak + right click: turn the text-to-speech voice on or off.
 */
public class TPhoneItem extends Item {
    public TPhoneItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.isShiftKeyDown()) {
            if (level.isClientSide) {
                DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> ClientHooks::toggleTextToSpeech);
            }
        } else if (player instanceof ServerPlayer sp) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.PLAYERS, 0.8F, 1.6F);
            StoryManager.useTPhone(sp);
        }
        player.getCooldowns().addCooldown(this, 20);
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Right click: current mission + call your brothers").withStyle(ChatFormatting.GREEN));
        tooltip.add(Component.literal("Sneak + right click: voice (text-to-speech) on/off").withStyle(ChatFormatting.GRAY));
    }
}
