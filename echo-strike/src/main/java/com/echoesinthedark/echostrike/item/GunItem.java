package com.echoesinthedark.echostrike.item;

import com.echoesinthedark.echostrike.combat.Gunplay;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * A gun. Left click shoots (handled client side, which asks the server to fire), right click aims,
 * R reloads. The magazine, the reload timer and the last shot time live in the item's NBT so the
 * HUD on the client can show them.
 */
public class GunItem extends Item {
    public static final String AMMO = "Ammo";
    public static final String RELOAD_END = "ReloadEnd";
    public static final String LAST_SHOT = "LastShot";

    public final GunType type;

    public GunItem(GunType type, Properties props) {
        super(props.stacksTo(1));
        this.type = type;
    }

    // ---------------------------------------------------------------- magazine helpers

    public static int getAmmo(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        if (tag == null || !tag.contains(AMMO)) {
            return stack.getItem() instanceof GunItem g ? g.type.magSize : 0;
        }
        return tag.getInt(AMMO);
    }

    public static void setAmmo(ItemStack stack, int ammo) {
        stack.getOrCreateTag().putInt(AMMO, Math.max(0, ammo));
    }

    public static boolean isReloading(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        return tag != null && tag.getLong(RELOAD_END) > gameTime;
    }

    /** 0..1 how far along the reload is, or -1 when not reloading. */
    public static float reloadProgress(ItemStack stack, long gameTime) {
        CompoundTag tag = stack.getTag();
        if (tag == null || tag.getLong(RELOAD_END) <= gameTime || !(stack.getItem() instanceof GunItem g)) {
            return -1;
        }
        long left = tag.getLong(RELOAD_END) - gameTime;
        return 1.0F - (float) left / g.type.reloadTicks;
    }

    /** Game time of the last shot. A fresh gun reports "long ago" (never MIN_VALUE: that overflows the subtraction). */
    public static long lastShot(ItemStack stack) {
        CompoundTag tag = stack.getTag();
        return tag == null || !tag.contains(LAST_SHOT) ? -100000L : tag.getLong(LAST_SHOT);
    }

    /** Can this gun fire right now (not reloading, has ammo, fire rate allows it)? */
    public static boolean canFire(ItemStack stack, long gameTime) {
        if (!(stack.getItem() instanceof GunItem g)) return false;
        if (isReloading(stack, gameTime)) return false;
        if (getAmmo(stack) <= 0) return false;
        return gameTime - lastShot(stack) >= g.type.ticksPerShot;
    }

    public static int countAmmoInInventory(Player player, Item ammo) {
        int n = 0;
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            ItemStack s = player.getInventory().getItem(i);
            if (s.is(ammo)) n += s.getCount();
        }
        return n;
    }

    private static int takeAmmoFromInventory(Player player, Item ammo, int wanted) {
        int taken = 0;
        for (int i = 0; i < player.getInventory().getContainerSize() && taken < wanted; i++) {
            ItemStack s = player.getInventory().getItem(i);
            if (s.is(ammo)) {
                int n = Math.min(s.getCount(), wanted - taken);
                s.shrink(n);
                taken += n;
            }
        }
        return taken;
    }

    // ---------------------------------------------------------------- server actions

    /** Server: begin a reload if it makes sense. */
    public void startReload(Player player, ItemStack stack) {
        Level level = player.level();
        long now = level.getGameTime();
        if (isReloading(stack, now) || getAmmo(stack) >= type.magSize) return;
        if (!player.isCreative() && countAmmoInInventory(player, type.ammo.get()) <= 0) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS, 0.5F, 1.4F);
            player.displayClientMessage(Component.literal("No " + type.ammo.get().getDescription().getString() + " left!").withStyle(ChatFormatting.RED), true);
            return;
        }
        stack.getOrCreateTag().putLong(RELOAD_END, now + type.reloadTicks);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ITEM_FRAME_ROTATE_ITEM, SoundSource.PLAYERS, 1.0F, 0.7F);
    }

    /** Server: fire one shot (all pellets) if the gun allows it. Returns true if it fired. */
    public boolean tryShoot(Player player, ItemStack stack, boolean aiming) {
        Level level = player.level();
        long now = level.getGameTime();
        if (isReloading(stack, now)) return false;
        if (getAmmo(stack) <= 0) {
            if (now - lastShot(stack) >= 6) {
                stack.getOrCreateTag().putLong(LAST_SHOT, now);
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS, 0.4F, 1.6F);
                startReload(player, stack);
            }
            return false;
        }
        // Be a little forgiving about timing so network jitter doesn't eat shots.
        if (now - lastShot(stack) < type.ticksPerShot - 1) return false;
        stack.getOrCreateTag().putLong(LAST_SHOT, now);
        if (!player.isCreative()) {
            setAmmo(stack, getAmmo(stack) - 1);
        }
        Gunplay.fire(player, type, aiming);
        if (getAmmo(stack) <= 0 && !player.isCreative()) {
            startReload(player, stack);
        }
        return true;
    }

    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        if (level.isClientSide || !(entity instanceof Player player)) return;
        CompoundTag tag = stack.getTag();
        if (tag == null || tag.getLong(RELOAD_END) == 0) return;
        long now = level.getGameTime();
        boolean held = selected || player.getOffhandItem() == stack;
        if (!held) {
            tag.putLong(RELOAD_END, 0); // switching weapons cancels the reload
            return;
        }
        if (tag.getLong(RELOAD_END) <= now) {
            tag.putLong(RELOAD_END, 0);
            int need = type.magSize - getAmmo(stack);
            int got = player.isCreative() ? need : takeAmmoFromInventory(player, type.ammo.get(), need);
            setAmmo(stack, getAmmo(stack) + got);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.CROSSBOW_LOADING_END, SoundSource.PLAYERS, 0.8F, 1.3F);
        }
    }

    // ---------------------------------------------------------------- vanilla hooks

    /**
     * Right click is "aim", which the client handles. CONSUME (not FAIL) so the game doesn't fall
     * through to the off hand and throw a grenade every time you aim.
     */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        return InteractionResultHolder.consume(player.getItemInHand(hand));
    }

    @Override
    public boolean onEntitySwing(ItemStack stack, LivingEntity entity) {
        return true; // no arm swing animation when shooting
    }

    @Override
    public boolean canAttackBlock(net.minecraft.world.level.block.state.BlockState state, Level level, net.minecraft.core.BlockPos pos, Player player) {
        return false; // guns don't break blocks
    }

    /** First-person animation lives in the client package; only the client ever runs this. */
    @Override
    public void initializeClient(java.util.function.Consumer<net.minecraftforge.client.extensions.common.IClientItemExtensions> consumer) {
        consumer.accept(com.echoesinthedark.echostrike.client.GunClientExtensions.INSTANCE);
    }

    @Override
    public boolean isEnchantable(ItemStack stack) {
        return false;
    }

    @Override
    public boolean isBarVisible(ItemStack stack) {
        return getAmmo(stack) < type.magSize;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13.0F * getAmmo(stack) / type.magSize);
    }

    @Override
    public int getBarColor(ItemStack stack) {
        return getAmmo(stack) == 0 ? 0xFF3030 : 0xFFC832;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.literal(type.auto ? "Full auto" : "Semi auto").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.literal("Damage " + type.damage + (type.pellets > 1 ? " x" + type.pellets : "")
                + "  |  Mag " + getAmmo(stack) + "/" + type.magSize).withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.literal("Ammo: " + type.ammo.get().getDescription().getString()).withStyle(ChatFormatting.DARK_GRAY));
        tooltip.add(Component.literal("Left click shoot, right click aim, R reload").withStyle(ChatFormatting.DARK_GREEN));
    }
}
