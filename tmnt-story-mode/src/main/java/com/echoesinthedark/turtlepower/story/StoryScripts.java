package com.echoesinthedark.turtlepower.story;

import com.echoesinthedark.turtlepower.story.Dialogue.Line;

import static com.echoesinthedark.turtlepower.story.Dialogue.line;
import static com.echoesinthedark.turtlepower.story.Speaker.APRIL;
import static com.echoesinthedark.turtlepower.story.Speaker.DONNIE;
import static com.echoesinthedark.turtlepower.story.Speaker.KRAANG;
import static com.echoesinthedark.turtlepower.story.Speaker.KRAANG_PRIME;
import static com.echoesinthedark.turtlepower.story.Speaker.LEO;
import static com.echoesinthedark.turtlepower.story.Speaker.MIKEY;
import static com.echoesinthedark.turtlepower.story.Speaker.NARRATOR;
import static com.echoesinthedark.turtlepower.story.Speaker.RAPH;
import static com.echoesinthedark.turtlepower.story.Speaker.SPLINTER;

/** All the story dialogue in one place. Everything here is spoken by text-to-speech too. */
public final class StoryScripts {
    private StoryScripts() {}

    public static final Line[] OPENING = {
            line(NARRATOR, "Deep below New York City, in an old abandoned subway station, four brothers train in secret."),
            line(SPLINTER, "Raphael. Wake up, my son. Your brothers are already awake."),
            line(MIKEY, "Raaaaph! Dude, get up! Splinter's doing the scary eyebrow thing!"),
            line(RAPH, "Alright, alright. I'm up. Nobody touches my stuff."),
    };

    /** Lines when a step starts. */
    public static Line[] enter(StoryStep step) {
        return switch (step) {
            case GET_SAIS -> new Line[]{
                    line(LEO, "Your sais are on the weapon rack in the dojo, Raph. Grab them and meet us by the tree."),
            };
            case TRAINING -> new Line[]{
                    line(SPLINTER, "Strike the training dummies, Raphael. Control your anger. Let it flow through your sais, not your mouth."),
            };
            case EAT_PIZZA -> new Line[]{
                    line(MIKEY, "Training's over? PIZZA TIME! Kitchen, now! I saved you a slice. Okay, I saved you a box. Okay, I ate most of the box."),
            };
            case DONNIE_LAB -> new Line[]{
                    line(DONNIE, "Guys! Get to my lab, right now! You need to see this!"),
            };
            case EXIT_SEWER -> new Line[]{
                    line(LEO, "Take the subway stairs up to the sewer. The ladder to the manhole is right next to the stairs. Right click the manhole to open it."),
            };
            case ROOFTOPS -> new Line[]{
                    line(MIKEY, "Race you to the rooftops! The fire escape on Antonio's goes all the way up. Last one up is a Kraang!"),
            };
            case MEET_APRIL -> new Line[]{
                    line(DONNIE, "Text from April! She's inside Antonio's Pizza. She says it's urgent. And... she used three exclamation points."),
            };
            case PORTAL -> new Line[]{
                    line(DONNIE, "Energy readings are off the charts in Times Square! It's a Kraang portal! Go, go, go!"),
            };
            case DEFEAT_KRAANG -> new Line[]{
                    line(KRAANG, "Kraang has opened the portal to the place that is here. Now Kraang will take the mutagen from the place."),
                    line(LEO, "Not tonight! Turtles, attack!"),
            };
            case COLLECT_MUTAGEN -> new Line[]{
                    line(DONNIE, "Grab every mutagen canister you can find. The Kraang drop them, and there are Kraang crates hidden around the city. My T-Phone will point you to them."),
            };
            case MUTANT_LOOSE -> new Line[]{
                    line(MIKEY, "Uh... guys? Why is Central Park making screaming noises?"),
                    line(LEO, "A canister must have spilled in the park. Something mutated! Move!"),
            };
            case RETURN_LAB -> new Line[]{
                    line(DONNIE, "Back to the lab! With the mutagen we collected, I can finally finish my retro-mutagen."),
            };
            case INFILTRATE_TCRI -> new Line[]{
                    line(SPLINTER, "The Kraang will not stop. Their nest is the tower they call TCRI. End this, my sons, and come home safe."),
                    line(DONNIE, "TCRI. Techno Cosmic Research Institute. Biggest Kraang lab in New York. It's the tall glass tower with the purple letters."),
            };
            case BOSS -> new Line[]{
                    line(KRAANG_PRIME, "The turtles have come to the place of Kraang. Kraang Prime will now destroy the turtles, who are turtles."),
                    line(RAPH, "Big words for a brain in a tin can."),
                    line(LEO, "Everyone together. Now!"),
            };
            case RETURN_HOME -> new Line[]{
                    line(LEO, "Let's go home, guys."),
            };
            case FREE_ROAM -> new Line[]{
                    line(NARRATOR, "THE END... for now. New York still needs you. The Kraang and the Foot Clan are still out there."),
                    line(DONNIE, "My T-Phone will beep when something happens in the city. Right click it any time."),
            };
            default -> new Line[0];
        };
    }

    /** Lines when a step is finished. */
    public static Line[] done(StoryStep step) {
        return switch (step) {
            case GET_SAIS -> new Line[]{
                    line(RAPH, "There they are. Missed you guys."),
                    line(SPLINTER, "Good. Now show me what you have learned."),
            };
            case TRAINING -> new Line[]{
                    line(SPLINTER, "Hai. Strong. But patience is also a weapon, Raphael. Remember that."),
            };
            case EAT_PIZZA -> new Line[]{
                    line(RAPH, "Mmm. Pepperoni. Best part of being a turtle."),
                    line(MIKEY, "Booyakasha! Pizza powers, activate!"),
            };
            case DONNIE_LAB -> new Line[]{
                    line(DONNIE, "I've been tracking weird energy spikes all over the city. Mutagen. Lots of it."),
                    line(DONNIE, "Here, Raph. I made you a T-Phone. Right click it to see our mission and call us to you. Sneak and right click to turn my voice on or off."),
                    line(LEO, "If there's mutagen out there, somebody is using it. We're going topside."),
                    line(SPLINTER, "Be careful, my sons. Stay in the shadows."),
            };
            case EXIT_SEWER -> new Line[]{
                    line(MIKEY, "Ahh, sweet city air! It smells like... garbage. And pizza. Mostly garbage."),
                    line(LEO, "Up to the rooftops. Nobody ever looks up."),
            };
            case ROOFTOPS -> new Line[]{
                    line(LEO, "Nothing beats the view from up here."),
            };
            case MEET_APRIL -> new Line[]{
                    line(APRIL, "Guys! Finally! I followed some men in suits from TCRI tonight. They weren't men. They were robots!"),
                    line(APRIL, "They had canisters of glowing green goo, and they're opening some kind of portal in Times Square!"),
                    line(RAPH, "Kraang. Figures."),
                    line(LEO, "Then we'll be there to close it."),
            };
            case PORTAL -> new Line[0];
            case DEFEAT_KRAANG -> new Line[]{
                    line(DONNIE, "That's the last of them! They dropped mutagen canisters. We need those!"),
                    line(MIKEY, "Evidence... that glows. So cool."),
            };
            case COLLECT_MUTAGEN -> new Line[]{
                    line(DONNIE, "Five canisters! That's enough to start making a retro-mutagen."),
            };
            case MUTANT_LOOSE -> new Line[]{
                    line(LEO, "The mutant's down. The park is safe."),
                    line(MIKEY, "I'm calling him Spider Bytez. You're welcome."),
                    line(RAPH, "You name EVERYTHING, Mikey."),
            };
            case RETURN_LAB -> new Line[]{
                    line(DONNIE, "Aaaand... done! Retro-mutagen! It turns mutants back into whatever they were before. Take some, Raph."),
                    line(SPLINTER, "Well done, my sons. But the Kraang will not stop."),
            };
            case INFILTRATE_TCRI -> new Line[0];
            case BOSS -> new Line[]{
                    line(KRAANG_PRIME, "Kraang... will... return... to the place... of returning..."),
                    line(LEO, "We did it! TCRI is shut down!"),
                    line(MIKEY, "Best. Night. EVER! Can we get pizza now?"),
                    line(RAPH, "Yeah, Mikey. We can get pizza now."),
            };
            case RETURN_HOME -> new Line[]{
                    line(SPLINTER, "My sons... I am proud of you. You fought as one. That is the true way of the ninja."),
                    line(SPLINTER, "Raphael. Your anger made you strong tonight. But your brothers made you stronger."),
                    line(RAPH, "Yeah... yeah, I know. Don't tell anyone I said that."),
                    line(MIKEY, "PIZZA PARTY! Booyakasha!"),
            };
            default -> new Line[0];
        };
    }

    public static final Line SPIDER_BYTEZ_APPEARS = line(Speaker.MIKEY, "Whoa, whoa, WHOA! Giant mutant spider! Somebody hit it!");

    public static final String[] SPLINTER_WISDOM = {
            "A true ninja does not fight because he is angry. He fights to protect those he loves.",
            "Your brothers are your greatest strength, Raphael.",
            "The mind is like water. When it is calm, it sees everything.",
            "Even the smallest sewer rat can topple a giant, if he is patient.",
            "Anger is a fire. Keep it in the stove, not in the curtains.",
    };

    public static final String[] APRIL_CHATTER = {
            "Be careful out there, guys. The Kraang are everywhere tonight.",
            "Antonio says the next pizza is on the house. For you guys, anyway.",
            "My T-Phone is on if you need me. Donnie made it. It only explodes sometimes.",
            "I'll keep an eye on TCRI. Something weird is always going on in there.",
    };
}
