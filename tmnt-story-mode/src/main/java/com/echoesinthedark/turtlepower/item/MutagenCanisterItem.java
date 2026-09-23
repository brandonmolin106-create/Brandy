package com.echoesinthedark.turtlepower.item;

import com.echoesinthedark.turtlepower.entity.Mutation;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Glowing green mutagen. Splash it on a mob to mutate it, or chug it yourself for a Mutagen Surge
 * (strength, speed, jump boost and resistance for 30 seconds).
 */
public class MutagenCanisterItem extends Item {
    public MutagenCanisterItem(Properties props) {
        super(props);
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return true;
    }

    @Override
    public InteractionResult interactLivingEntity(ItemStack stack, Player player, LivingEntity target, InteractionHand hand) {
        if (!(target instanceof Mob mob) || !Mutation.canMutate(mob)) {
            return InteractionResult.PASS;
        }
        if (!player.level().isClientSide) {
            if (Mutation.mutate((ServerLevel) player.level(), mob, player)) {
                if (!player.getAbilities().instabuild) {
                    stack.shrink(1);
                }
            } else {
                player.displayClientMessage(Component.literal("That one is already a mutant!").withStyle(ChatFormatting.GREEN), true);
            }
        }
        return InteractionResult.sidedSuccess(player.level().isClientSide);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        return ItemUtils.startUsingInstantly(level, player, hand);
    }

    @Override
    public int getUseDuration(ItemStack stack) {
        return 32;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.DRINK;
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        if (!level.isClientSide) {
            int t = 20 * 30;
            entity.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, t, 1));
            entity.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, t, 1));
            entity.addEffect(new MobEffectInstance(MobEffects.JUMP, t, 1));
            entity.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, t, 0));
            entity.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 80, 0));
            level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), SoundEvents.BREWING_STAND_BREW, SoundSource.PLAYERS, 1.0F, 0.6F);
            if (entity instanceof Player p) {
                p.displayClientMessage(Component.literal("MUTAGEN SURGE!").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD), true);
            }
        }
        if (entity instanceof Player p && !p.getAbilities().instabuild) {
            stack.shrink(1);
        }
        return stack;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Right click a mob to mutate it.").withStyle(ChatFormatting.GREEN));
        tooltip.add(Component.literal("Hold right click to drink: Mutagen Surge (30s).").withStyle(ChatFormatting.DARK_GREEN));
    }
}
