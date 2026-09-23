package com.echoesinthedark.turtlepower.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/** Raphael's red mask and his shell. Wearing both gives the Hothead set bonus. */
public class TurtleArmorItem extends ArmorItem {
    public TurtleArmorItem(ArmorMaterial material, Type type, Properties props) {
        super(material, type, props);
    }

    @Override
    public @Nullable String getArmorTexture(ItemStack stack, Entity entity, EquipmentSlot slot, String layer) {
        return getType() == Type.HELMET
                ? "turtlepower:textures/models/armor/raph_mask.png"
                : "turtlepower:textures/models/armor/turtle_shell.png";
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal("Set bonus (mask + shell): Hothead").withStyle(ChatFormatting.RED));
        tooltip.add(Component.literal(" Shell toughness: Resistance I").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.literal(" Below 40% health you get Strength II").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.literal(" Swim like a turtle: Dolphin's Grace in water").withStyle(ChatFormatting.GRAY));
    }
}
