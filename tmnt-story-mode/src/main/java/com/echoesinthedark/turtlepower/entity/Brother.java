package com.echoesinthedark.turtlepower.entity;

import com.echoesinthedark.turtlepower.registry.ModEntities;
import com.echoesinthedark.turtlepower.registry.ModItems;
import com.echoesinthedark.turtlepower.story.Speaker;
import net.minecraft.ChatFormatting;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.Item;

import java.util.function.Supplier;

/** Leo, Donnie and Mikey: who they are, what they carry and what they say. */
public enum Brother {
    LEO("Leonardo", ChatFormatting.BLUE, Speaker.LEO, ModItems.KATANA::get, 16, 0,
            new String[]{"Turtles, attack!", "Stay sharp, Raph!", "Nobody touches my brother!", "Watch your flank!", "Get behind me... okay, get beside me."},
            new String[]{"Stay focused, Raph. Master Splinter says patience is a weapon too.",
                    "Captain Ryan would have a plan for this. So do I. Mostly.",
                    "Remember: we stick together. Always.",
                    "I've got your back. You've got mine."},
            new String[]{"Ugh... I'm okay. Still in this!", "That one hurt my pride more than my shell."}),
    DONNIE("Donatello", ChatFormatting.DARK_PURPLE, Speaker.DONNIE, ModItems.BO_STAFF::get, 22, 1,
            new String[]{"Calculating the optimal whack angle!", "Bo staff, engage!", "Get away from him!", "Science... AND violence!"},
            new String[]{"Fun fact: turtle shells are made of over fifty bones. Ours are ninja-grade.",
                    "I upgraded the T-Phone. It now has 12% more beeps.",
                    "Mutagen levels in this area are... concerning.",
                    "If I had a dollar for every Kraang we've beaten, I could finally buy a real lab."},
            new String[]{"Ow, ow, ow. Okay. Rebooting.", "I'm fine! Minor structural damage!"}),
    MIKEY("Michelangelo", ChatFormatting.GOLD, Speaker.MIKEY, ModItems.NUNCHUCKS::get, 12, 2,
            new String[]{"Booyakasha!", "Cowabunga, dude!", "Hey! Nobody messes with Raphie!", "Nunchuck time!", "Take THAT, brain-face!"},
            new String[]{"Dude, is it pizza time? It feels like pizza time.",
                    "Raph, you ever think about how pizza is just a flat sandwich?",
                    "I named a sewer rat Klunk. Wait, no, Klunk is my cat. I have a cat?",
                    "Race you to the rooftops! Well, after this.",
                    "What if the Kraang like pizza too? Could we be friends? ...Nah."},
            new String[]{"I'm good! Totally good! Seeing stars, but good!", "That's it, I'm getting a snack after this."});

    public final String displayName;
    public final ChatFormatting color;
    public final Speaker speaker;
    private final Supplier<Item> weapon;
    /** Ticks between melee swings. Mikey is the fastest, Donnie the slowest but hits hardest. */
    public final int attackInterval;
    public final int index;
    public final String[] battleCries;
    public final String[] chatter;
    public final String[] knockedOut;

    Brother(String displayName, ChatFormatting color, Speaker speaker, Supplier<Item> weapon, int attackInterval, int index,
            String[] battleCries, String[] chatter, String[] knockedOut) {
        this.displayName = displayName;
        this.color = color;
        this.speaker = speaker;
        this.weapon = weapon;
        this.attackInterval = attackInterval;
        this.index = index;
        this.battleCries = battleCries;
        this.chatter = chatter;
        this.knockedOut = knockedOut;
    }

    public Item weapon() {
        return weapon.get();
    }

    public EntityType<TurtleBrotherEntity> entityType() {
        return switch (this) {
            case LEO -> ModEntities.LEONARDO.get();
            case DONNIE -> ModEntities.DONATELLO.get();
            case MIKEY -> ModEntities.MICHELANGELO.get();
        };
    }

    public static Brother of(EntityType<?> type) {
        if (type == ModEntities.DONATELLO.get()) return DONNIE;
        if (type == ModEntities.MICHELANGELO.get()) return MIKEY;
        return LEO;
    }
}
