package com.echoesinthedark.turtlepower.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** Pizza with gummy worms, peanut butter and hot sauce. Nobody knows what it does. Not even Mikey. */
public class MikeySpecialPizzaItem extends Item {
    private static final String[] REACTIONS = {
            "Gummy worms AND peanut butter? ...okay that actually slaps.",
            "Whoa. My shell is tingling.",
            "Mikey, WHAT did you put on this?!",
            "Booyakasha! Pizza powers, activate!",
            "Tastes like... sardines and marshmallows."
    };

    public MikeySpecialPizzaItem(Properties props) {
        super(props);
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        if (!level.isClientSide) {
            int roll = level.getRandom().nextInt(5);
            switch (roll) {
                case 0 -> entity.addEffect(new MobEffectInstance(MobEffects.JUMP, 600, 2));
                case 1 -> entity.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 600, 2));
                case 2 -> entity.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 2400, 0));
                case 3 -> entity.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 600, 1));
                default -> entity.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 60, 0));
            }
            if (entity instanceof Player p) {
                p.displayClientMessage(Component.literal(REACTIONS[roll]).withStyle(ChatFormatting.GOLD), true);
            }
        }
        return super.finishUsingItem(stack, level, entity);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Gummy worms, peanut butter and hot sauce. Random power-up!").withStyle(ChatFormatting.GOLD));
    }
}
