package com.echoesinthedark.echostrike.network;

import com.echoesinthedark.echostrike.EchoStrike;
import com.echoesinthedark.echostrike.item.GunItem;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Client -> server: "I pulled the trigger". The server checks ammo and fire rate and shoots. */
public record ShootPacket(boolean aiming) {
    public void encode(FriendlyByteBuf buf) {
        buf.writeBoolean(aiming);
    }

    public static ShootPacket decode(FriendlyByteBuf buf) {
        return new ShootPacket(buf.readBoolean());
    }

    public void handle(Supplier<NetworkEvent.Context> ctx) {
        ServerPlayer player = ctx.get().getSender();
        try {
            if (player != null && player.isAlive() && !player.isSpectator()) {
                ItemStack stack = player.getMainHandItem();
                if (stack.getItem() instanceof GunItem gun) {
                    gun.tryShoot(player, stack, aiming);
                }
            }
        } catch (Exception e) {
            // Exceptions inside enqueued packet work are swallowed by the game: log them instead.
            EchoStrike.LOGGER.error("Shoot packet failed", e);
        }
        ctx.get().setPacketHandled(true);
    }
}
