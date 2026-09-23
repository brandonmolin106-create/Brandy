package com.echoesinthedark.turtlepower.item;

import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.Multimap;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.common.ForgeMod;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.UUID;

/** Raph's sai, Leo's katana, Donnie's bo staff and Mikey's nunchucks. */
public class NinjaWeaponItem extends SwordItem {
    public enum Style {
        SAI("Raphael's weapon. Hits can knock the fight out of enemies (Weakness).", ChatFormatting.RED),
        KATANA("Leonardo's weapon. Clean sweeping slashes.", ChatFormatting.BLUE),
        BO_STAFF("Donatello's weapon. Longer reach and a big knockback swing.", ChatFormatting.DARK_PURPLE),
        NUNCHUCKS("Michelangelo's weapon. Super fast hits that can stun.", ChatFormatting.GOLD);

        final String tooltip;
        final ChatFormatting color;

        Style(String tooltip, ChatFormatting color) {
            this.tooltip = tooltip;
            this.color = color;
        }
    }

    private static final UUID REACH_ID = UUID.fromString("6b1f7a0e-3a8e-4f51-9d3a-2f4a0d1c7b11");

    private final Style style;
    private final double reachBonus;

    public NinjaWeaponItem(Style style, Tier tier, int damage, float speed, double reachBonus, Properties props) {
        super(tier, damage, speed, props);
        this.style = style;
        this.reachBonus = reachBonus;
    }

    public Style style() {
        return style;
    }

    @Override
    public Multimap<Attribute, AttributeModifier> getAttributeModifiers(EquipmentSlot slot, ItemStack stack) {
        Multimap<Attribute, AttributeModifier> base = super.getAttributeModifiers(slot, stack);
        if (slot != EquipmentSlot.MAINHAND || reachBonus <= 0) {
            return base;
        }
        ImmutableMultimap.Builder<Attribute, AttributeModifier> b = ImmutableMultimap.builder();
        b.putAll(base);
        b.put(ForgeMod.ENTITY_REACH.get(), new AttributeModifier(REACH_ID, "Bo staff reach", reachBonus, AttributeModifier.Operation.ADDITION));
        return b.build();
    }

    @Override
    public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        switch (style) {
            case SAI -> {
                if (attacker.getRandom().nextFloat() < 0.25F) {
                    target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 1), attacker);
                }
            }
            case BO_STAFF -> target.knockback(0.8, attacker.getX() - target.getX(), attacker.getZ() - target.getZ());
            case NUNCHUCKS -> {
                if (attacker.getRandom().nextFloat() < 0.2F) {
                    target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 4), attacker);
                }
            }
            default -> { }
        }
        return super.hurtEnemy(stack, target, attacker);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal(style.tooltip).withStyle(style.color));
    }
}
