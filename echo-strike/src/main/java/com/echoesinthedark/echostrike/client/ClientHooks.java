package com.echoesinthedark.echostrike.client;

/** Client-only entry points called from packets. Only ever loaded on the client. */
public final class ClientHooks {
    private ClientHooks() {}

    public static void onHitmarker(int kind) {
        StrikeHud.hitmarker(kind);
        if (System.getProperty("echostrike.devtest") != null) {
            com.echoesinthedark.echostrike.EchoStrike.LOGGER.info("DEVTEST hitmarker kind={}", kind);
        }
    }
}
