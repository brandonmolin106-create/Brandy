package com.echoesinthedark.turtlepower.network;

import com.echoesinthedark.turtlepower.client.ClientHooks;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Sent by /tmnt voice on|off. */
public record VoiceTogglePacket(boolean enabled) {
    public void encode(FriendlyByteBuf buf) {
        buf.writeBoolean(enabled);
    }

    public static VoiceTogglePacket decode(FriendlyByteBuf buf) {
        return new VoiceTogglePacket(buf.readBoolean());
    }

    public void handle(Supplier<NetworkEvent.Context> ctx) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> ClientHooks.setTextToSpeech(enabled));
        ctx.get().setPacketHandled(true);
    }
}
