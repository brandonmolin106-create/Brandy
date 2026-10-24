package com.echoesinthedark.echostrike.network;

import com.echoesinthedark.echostrike.EchoStrike;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

public final class ModNetwork {
    private ModNetwork() {}

    private static final String VERSION = "1";

    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            EchoStrike.id("main"), () -> VERSION, VERSION::equals, VERSION::equals);

    public static void register() {
        int id = 0;
        CHANNEL.messageBuilder(ShootPacket.class, id++, NetworkDirection.PLAY_TO_SERVER)
                .encoder(ShootPacket::encode).decoder(ShootPacket::decode)
                .consumerMainThread(ShootPacket::handle).add();
        CHANNEL.messageBuilder(ReloadPacket.class, id++, NetworkDirection.PLAY_TO_SERVER)
                .encoder(ReloadPacket::encode).decoder(ReloadPacket::decode)
                .consumerMainThread(ReloadPacket::handle).add();
        CHANNEL.messageBuilder(HitmarkerPacket.class, id++, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(HitmarkerPacket::encode).decoder(HitmarkerPacket::decode)
                .consumerMainThread(HitmarkerPacket::handle).add();
    }
}
