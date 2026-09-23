package com.echoesinthedark.turtlepower.command;

import com.echoesinthedark.turtlepower.network.ModNetwork;
import com.echoesinthedark.turtlepower.network.VoiceTogglePacket;
import com.echoesinthedark.turtlepower.story.CityEvents;
import com.echoesinthedark.turtlepower.story.StoryData;
import com.echoesinthedark.turtlepower.story.StoryManager;
import com.echoesinthedark.turtlepower.story.StoryStep;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraftforge.network.PacketDistributor;

import java.util.Arrays;
import java.util.Locale;

/**
 * /tmnt start           build New York + the lair here (or join the story if it's built) and begin
 * /tmnt home            teleport back to your room in the lair
 * /tmnt status          what you're supposed to be doing
 * /tmnt turtles         call Leo, Donnie and Mikey to you
 * /tmnt voice on|off    text-to-speech on or off
 * /tmnt skip            finish the current step (if you get stuck)
 * /tmnt chapter 1-5     jump to a chapter
 * /tmnt event <type>    start a city event right now
 * /tmnt reset           start the story over
 * /tmnt build           (console/ops) build the city at world spawn without starting anyone's story
 */
public final class TmntCommand {
    private TmntCommand() {}

    /** Ops, or the owner of a single player world even without cheats on. */
    private static boolean trusted(CommandSourceStack src) {
        if (src.hasPermission(2)) return true;
        return src.getEntity() instanceof ServerPlayer p && src.getServer().isSingleplayerOwner(p.getGameProfile());
    }

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        d.register(Commands.literal("tmnt")
                .then(Commands.literal("start").requires(TmntCommand::trusted).executes(ctx -> start(ctx.getSource())))
                .then(Commands.literal("build").requires(s -> s.hasPermission(2)).executes(ctx -> buildAtSpawn(ctx.getSource())))
                .then(Commands.literal("home").executes(ctx -> {
                    StoryManager.goHome(ctx.getSource().getPlayerOrException());
                    return 1;
                }))
                .then(Commands.literal("status").executes(ctx -> status(ctx.getSource())))
                .then(Commands.literal("turtles").executes(ctx -> {
                    StoryManager.recallBrothers(ctx.getSource().getPlayerOrException());
                    ctx.getSource().sendSuccess(() -> Component.literal("Turtles, regroup!").withStyle(ChatFormatting.GREEN), false);
                    return 1;
                }))
                .then(Commands.literal("voice")
                        .then(Commands.literal("on").executes(ctx -> voice(ctx.getSource(), true)))
                        .then(Commands.literal("off").executes(ctx -> voice(ctx.getSource(), false))))
                .then(Commands.literal("skip").requires(TmntCommand::trusted).executes(ctx -> {
                    StoryManager.complete(ctx.getSource().getPlayerOrException());
                    return 1;
                }))
                .then(Commands.literal("chapter").requires(TmntCommand::trusted)
                        .then(Commands.argument("number", IntegerArgumentType.integer(1, 6)).executes(ctx -> {
                            int n = IntegerArgumentType.getInteger(ctx, "number");
                            StoryManager.jumpTo(ctx.getSource().getPlayerOrException(), StoryStep.firstOfChapter(n));
                            return 1;
                        })))
                .then(Commands.literal("event").requires(TmntCommand::trusted)
                        .then(Commands.argument("type", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(
                                        Arrays.stream(CityEvents.Type.values()).map(t -> t.name().toLowerCase(Locale.ROOT)), b))
                                .executes(ctx -> event(ctx.getSource(), StringArgumentType.getString(ctx, "type")))))
                .then(Commands.literal("reset").requires(TmntCommand::trusted).executes(ctx -> {
                    ServerPlayer p = ctx.getSource().getPlayerOrException();
                    StoryManager.jumpTo(p, StoryStep.NOT_STARTED);
                    StoryManager.startStory(p);
                    return 1;
                })));
    }

    private static int start(CommandSourceStack src) throws CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        StoryData data = StoryData.get(src.getServer());
        if (StoryManager.isBuilding()) {
            src.sendFailure(Component.literal("New York is still being built, hang on!"));
            return 0;
        }
        if (data.built) {
            if (data.progress(p.getUUID()).step != StoryStep.NOT_STARTED) {
                src.sendSuccess(() -> Component.literal("Your story already started. Use /tmnt home to go back to the lair, or /tmnt reset to start over.")
                        .withStyle(ChatFormatting.YELLOW), false);
                return 0;
            }
            StoryManager.startStory(p);
            return 1;
        }
        if (p.level().dimension() != Level.OVERWORLD) {
            src.sendFailure(Component.literal("New York can only be built in the Overworld."));
            return 0;
        }
        BlockPos at = p.blockPosition();
        boolean ok = StoryManager.beginBuild(p.serverLevel(), at.getX(), at.getZ(), p, false);
        return ok ? 1 : 0;
    }

    private static int buildAtSpawn(CommandSourceStack src) {
        ServerLevel ow = src.getServer().overworld();
        BlockPos spawn = ow.getSharedSpawnPos();
        boolean ok = StoryManager.beginBuild(ow, spawn.getX(), spawn.getZ(), null, true);
        src.sendSuccess(() -> Component.literal(ok ? "Building the TMNT story world at spawn." : "Already built (or building)."), true);
        return ok ? 1 : 0;
    }

    private static int status(CommandSourceStack src) throws CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        StoryData data = StoryData.get(src.getServer());
        if (!data.built) {
            src.sendSuccess(() -> Component.literal("The story world isn't built yet. Type /tmnt start where you want New York to appear."), false);
            return 1;
        }
        StoryData.PlayerProgress pr = data.progress(p.getUUID());
        String prog = pr.step.goal > 0 ? " (" + pr.counter + "/" + pr.step.goal + ")" : "";
        src.sendSuccess(() -> Component.literal(pr.step.chapterTitle + ": ").withStyle(ChatFormatting.GREEN)
                .append(Component.literal(pr.step.objective + prog).withStyle(ChatFormatting.WHITE)), false);
        StoryManager.sendObjective(p);
        return 1;
    }

    private static int voice(CommandSourceStack src, boolean on) throws CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        ModNetwork.CHANNEL.send(PacketDistributor.PLAYER.with(() -> p), new VoiceTogglePacket(on));
        return 1;
    }

    private static int event(CommandSourceStack src, String type) throws CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        try {
            CityEvents.trigger(p, StoryData.get(src.getServer()), CityEvents.parse(type));
            return 1;
        } catch (IllegalArgumentException e) {
            src.sendFailure(Component.literal("Unknown event. Try: kraang_portal, mutagen_spill, foot_ambush, pizza_drop, kraang_supply"));
            return 0;
        }
    }
}
