package com.echoesinthedark.turtlepower.network;

import com.echoesinthedark.turtlepower.client.ClientHooks;
import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;
import org.jetbrains.annotations.Nullable;

import java.util.function.Supplier;

/** Current chapter, objective and where to go. An empty chapter clears the objective HUD. */
public record ObjectivePacket(String chapter, String objective, String progress, @Nullable BlockPos target) {
    public void encode(FriendlyByteBuf buf) {
        buf.writeUtf(chapter, 256);
        buf.writeUtf(objective, 512);
        buf.writeUtf(progress, 128);
        buf.writeBoolean(target != null);
        if (target != null) {
            buf.writeBlockPos(target);
        }
    }

    public static ObjectivePacket decode(FriendlyByteBuf buf) {
        String chapter = buf.readUtf(256);
        String objective = buf.readUtf(512);
        String progress = buf.readUtf(128);
        BlockPos target = buf.readBoolean() ? buf.readBlockPos() : null;
        return new ObjectivePacket(chapter, objective, progress, target);
    }

    public void handle(Supplier<NetworkEvent.Context> ctx) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> ClientHooks.onObjective(this));
        ctx.get().setPacketHandled(true);
    }
}
