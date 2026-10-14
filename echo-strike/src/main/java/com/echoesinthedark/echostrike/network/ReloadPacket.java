package com.echoesinthedark.echostrike.network;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.item.GunItem;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Client -> server: the reload key was pressed. */
public record ReloadPacket() {
    public void encode(FriendlyByteBuf buf) {
    }

    public static ReloadPacket decode(FriendlyByteBuf buf) {
        return new ReloadPacket();
    }

    public void handle(Supplier<NetworkEvent.Context> ctx) {
        ServerPlayer player = ctx.get().getSender();
        try {
            if (player != null && player.isAlive()) {
                ItemStack stack = player.getMainHandItem();
                if (stack.getItem() instanceof GunItem gun) {
                    gun.startReload(player, stack);
                }
            }
        } catch (Exception e) {
            EchoStrike.LOGGER.error("Reload packet failed", e);
        }
        ctx.get().setPacketHandled(true);
    }
}
