package com.echoesinthedark.turtlepower.network;

import com.echoesinthedark.turtlepower.client.ClientHooks;
import com.echoesinthedark.turtlepower.story.Dialogue;
import com.echoesinthedark.turtlepower.story.Speaker;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

public record DialoguePacket(Speaker speaker, String text, Dialogue.Kind kind) {
    public void encode(FriendlyByteBuf buf) {
        buf.writeEnum(speaker);
        buf.writeUtf(text, 1024);
        buf.writeEnum(kind);
    }

    public static DialoguePacket decode(FriendlyByteBuf buf) {
        return new DialoguePacket(buf.readEnum(Speaker.class), buf.readUtf(1024), buf.readEnum(Dialogue.Kind.class));
    }

    public void handle(Supplier<NetworkEvent.Context> ctx) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> ClientHooks.onDialogue(this));
        ctx.get().setPacketHandled(true);
    }
}
