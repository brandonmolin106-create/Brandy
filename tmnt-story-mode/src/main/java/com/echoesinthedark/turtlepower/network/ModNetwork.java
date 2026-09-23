package com.echoesinthedark.turtlepower.network;

import com.echoesinthedark.turtlepower.TurtlePower;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

public final class ModNetwork {
    private ModNetwork() {}

    private static final String VERSION = "1";

    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            TurtlePower.id("main"), () -> VERSION, VERSION::equals, VERSION::equals);

    public static void register() {
        int id = 0;
        CHANNEL.messageBuilder(DialoguePacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(DialoguePacket::encode).decoder(DialoguePacket::decode)
                .consumerMainThread(DialoguePacket::handle).add();
        CHANNEL.messageBuilder(ObjectivePacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(ObjectivePacket::encode).decoder(ObjectivePacket::decode)
                .consumerMainThread(ObjectivePacket::handle).add();
        CHANNEL.messageBuilder(VoiceTogglePacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(VoiceTogglePacket::encode).decoder(VoiceTogglePacket::decode)
                .consumerMainThread(VoiceTogglePacket::handle).add();
    }
}
