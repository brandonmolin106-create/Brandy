package com.echoesinthedark.echostrike.network;

import com.echoesinthedark.echostrike.client.ClientHooks;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Server -> client: you hit something. Draws the hitmarker and plays the ding. */
public record HitmarkerPacket(int kind) {
    public static final int HIT = 0;
    public static final int HEADSHOT = 1;
    public static final int KILL = 2;

    public void encode(FriendlyByteBuf buf) {
        buf.writeByte(kind);
    }

    public static HitmarkerPacket decode(FriendlyByteBuf buf) {
        return new HitmarkerPacket(buf.readByte());
    }

    public void handle(Supplier<NetworkEvent.Context> ctx) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> ClientHooks.onHitmarker(kind));
        ctx.get().setPacketHandled(true);
    }
}
