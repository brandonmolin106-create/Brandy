package com.echoesinthedark.echostrike.command;

import com.echoesinthedark.echostrike.game.ArenaBuilder;
import com.echoesinthedark.echostrike.game.LootCrates;
import com.echoesinthedark.echostrike.game.StrikeGame;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

/**
 * /strike kit [assault|m4|smg|sniper|shotgun|heavy|pistol]   give yourself a loadout
 * /strike arena                                       build an arena around you
 * /strike waves start|stop                            Wave Survival
 * /strike br start [minutes] [bots]                   Battle Royale with a shrinking zone
 * /strike crate                                       drop a loot crate where you stand
 * /strike stop                                        end whatever is running
 * /strike status
 */
public final class StrikeCommand {
    private StrikeCommand() {}

    private static boolean trusted(CommandSourceStack src) {
        if (src.hasPermission(2)) return true;
        return src.getEntity() instanceof ServerPlayer p && src.getServer().isSingleplayerOwner(p.getGameProfile());
    }

    public static void register(CommandDispatcher<CommandSourceStack> d) {
        d.register(Commands.literal("strike")
                .then(Commands.literal("kit")
                        .executes(ctx -> kit(ctx.getSource(), "assault"))
                        .then(Commands.argument("name", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(new String[]{"assault", "m4", "smg", "sniper", "shotgun", "heavy", "pistol"}, b))
                                .executes(ctx -> kit(ctx.getSource(), StringArgumentType.getString(ctx, "name")))))
                .then(Commands.literal("arena").requires(StrikeCommand::trusted).executes(ctx -> arena(ctx.getSource())))
                .then(Commands.literal("crate").requires(StrikeCommand::trusted).executes(ctx -> crate(ctx.getSource())))
                .then(Commands.literal("waves").requires(StrikeCommand::trusted)
                        .then(Commands.literal("start").executes(ctx -> waves(ctx.getSource())))
                        .then(Commands.literal("stop").executes(ctx -> stop(ctx.getSource()))))
                .then(Commands.literal("br").requires(StrikeCommand::trusted)
                        .then(Commands.literal("start")
                                .executes(ctx -> br(ctx.getSource(), 6, 12))
                                .then(Commands.argument("minutes", IntegerArgumentType.integer(1, 60))
                                        .executes(ctx -> br(ctx.getSource(), IntegerArgumentType.getInteger(ctx, "minutes"), 12))
                                        .then(Commands.argument("bots", IntegerArgumentType.integer(0, 60))
                                                .executes(ctx -> br(ctx.getSource(), IntegerArgumentType.getInteger(ctx, "minutes"),
                                                        IntegerArgumentType.getInteger(ctx, "bots"))))))
                        .then(Commands.literal("stop").executes(ctx -> stop(ctx.getSource()))))
                .then(Commands.literal("stop").requires(StrikeCommand::trusted).executes(ctx -> stop(ctx.getSource())))
                .then(Commands.literal("status").executes(ctx -> {
                    ctx.getSource().sendSuccess(() -> Component.literal(StrikeGame.describe(StrikeGame.get(ctx.getSource().getServer()))), false);
                    return 1;
                }))
                .then(Commands.literal("help").executes(ctx -> help(ctx.getSource())))
                .executes(ctx -> help(ctx.getSource())));
    }

    private static int help(CommandSourceStack src) {
        src.sendSuccess(() -> Component.literal("Echo Strike commands").withStyle(ChatFormatting.RED, ChatFormatting.BOLD), false);
        src.sendSuccess(() -> Component.literal("/strike kit [assault|m4|smg|sniper|shotgun|heavy|pistol]  - loadout").withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> Component.literal("/strike arena  - build an arena around you").withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> Component.literal("/strike waves start  - Wave Survival").withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> Component.literal("/strike br start [minutes] [bots]  - Battle Royale").withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> Component.literal("/strike crate  - drop a loot crate").withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> Component.literal("/strike stop  - end the game").withStyle(ChatFormatting.GRAY), false);
        src.sendSuccess(() -> Component.literal("Controls: left click shoot, right click aim, R reload, sprint+crouch slide, run at a wall to vault").withStyle(ChatFormatting.DARK_GREEN), false);
        return 1;
    }

    private static int kit(CommandSourceStack src, String name) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        StrikeGame.giveKit(p, name);
        src.sendSuccess(() -> Component.literal("Kit: " + name).withStyle(ChatFormatting.GREEN), false);
        return 1;
    }

    private static int arena(CommandSourceStack src) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        ArenaBuilder.build(p.serverLevel(), p.blockPosition(), p.getRandom());
        p.teleportTo(p.getX(), p.getY() + 2, p.getZ());
        src.sendSuccess(() -> Component.literal("Arena built. /strike waves start when you're ready.").withStyle(ChatFormatting.GREEN), false);
        return 1;
    }

    private static int crate(CommandSourceStack src) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        LootCrates.place(p.serverLevel(), p.blockPosition().relative(p.getDirection(), 2), p.getRandom());
        return 1;
    }

    private static int waves(CommandSourceStack src) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        StrikeGame.get(src.getServer()).startWaves(p);
        return 1;
    }

    private static int br(CommandSourceStack src, int minutes, int bots) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer p = src.getPlayerOrException();
        StrikeGame.get(src.getServer()).startBattleRoyale(p, minutes, bots);
        return 1;
    }

    private static int stop(CommandSourceStack src) {
        StrikeGame g = StrikeGame.get(src.getServer());
        if (g.mode() == StrikeGame.Mode.NONE) {
            src.sendSuccess(() -> Component.literal("Nothing is running.").withStyle(ChatFormatting.GRAY), false);
        } else {
            g.stop(true);
        }
        return 1;
    }
}
