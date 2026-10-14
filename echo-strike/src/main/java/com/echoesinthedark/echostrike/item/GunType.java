package com.echoesinthedark.echostrike.item;

import com.echoesinthedark.echostrike.registry.ModItems;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.Item;

import java.util.function.Supplier;

/**
 * The weapon roster, modelled on the BloodStrike lineup: the same guns, with fire rate, magazine,
 * damage and recoil tuned so each one plays like its namesake. Damage is in half-hearts (a player
 * has 20); every number here is ours, rebuilt from how the guns feel, not copied from anywhere.
 */
public enum GunType {
    //     id        class     auto   dmg    pel rate mag  reload range spread recV  recH  zoom  head   ammo                                 sound                              pitch  vol
    G18("g18",       Class.PISTOL,  true,  3.2F,  1,  3,   20,  26,  36,   3.0F,  1.3F, 1.4F, 1.2F,  1.75F, () -> ModItems.LIGHT_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 1.9F,  0.6F),
    DEAGLE("deagle", Class.PISTOL,  false, 9.0F,  1,  9,   7,   30,  48,   1.4F,  4.5F, 1.6F, 1.25F, 2.0F,  () -> ModItems.HEAVY_AMMO.get(),     SoundEvents.GENERIC_EXPLODE,       1.8F,  0.5F),
    MP5("mp5",       Class.SMG,     true,  3.5F,  1,  2,   30,  34,  40,   2.6F,  1.1F, 1.3F, 1.25F, 1.75F, () -> ModItems.LIGHT_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 1.95F, 0.6F),
    UMP45("ump45",   Class.SMG,     true,  4.4F,  1,  3,   25,  36,  44,   2.2F,  1.4F, 1.2F, 1.25F, 1.75F, () -> ModItems.LIGHT_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 1.7F,  0.65F),
    VECTOR("vector", Class.SMG,     true,  2.8F,  1,  1,   33,  40,  32,   3.2F,  0.9F, 1.6F, 1.25F, 1.75F, () -> ModItems.LIGHT_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 2.0F,  0.5F),
    AK47("ak47",     Class.RIFLE,   true,  6.2F,  1,  4,   30,  46,  64,   2.1F,  2.3F, 1.4F, 1.4F,  2.0F,  () -> ModItems.HEAVY_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 1.3F,  0.85F),
    M4A1("m4a1",     Class.RIFLE,   true,  5.0F,  1,  3,   30,  42,  64,   1.6F,  1.4F, 1.0F, 1.4F,  2.0F,  () -> ModItems.HEAVY_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 1.5F,  0.8F),
    M870("m870",     Class.SHOTGUN, false, 2.6F,  8,  16,  6,   60,  16,   7.0F,  5.0F, 1.5F, 1.15F, 1.5F,  () -> ModItems.SHOTGUN_SHELLS.get(), SoundEvents.GENERIC_EXPLODE,       1.6F,  0.6F),
    AWM("awm",       Class.SNIPER,  false, 22.0F, 1,  32,  5,   70,  160,  0.4F,  7.0F, 1.2F, 4.0F,  2.5F,  () -> ModItems.SNIPER_ROUNDS.get(),  SoundEvents.GENERIC_EXPLODE,       1.25F, 0.55F),
    M249("m249",     Class.LMG,     true,  4.5F,  1,  3,   100, 100, 56,   3.2F,  1.5F, 1.8F, 1.3F,  1.75F, () -> ModItems.HEAVY_AMMO.get(),     SoundEvents.FIREWORK_ROCKET_BLAST, 1.1F,  0.85F);

    public enum Class { PISTOL, SMG, RIFLE, SHOTGUN, SNIPER, LMG }

    public final String id;
    public final Class weaponClass;
    /** Hold the trigger to keep firing. Semi-auto guns need a new click per shot. */
    public final boolean auto;
    public final float damage;
    public final int pellets;
    /** Ticks between shots (20 ticks = 1 second). */
    public final int ticksPerShot;
    public final int magSize;
    public final int reloadTicks;
    public final float range;
    /** Base cone of fire in degrees from the hip. Aiming shrinks it. */
    public final float spread;
    public final float recoilVertical;
    public final float recoilHorizontal;
    /** Field-of-view divider while aiming. 4 = the sniper scope. */
    public final float zoom;
    public final float headshotMultiplier;
    public final Supplier<Item> ammo;
    public final SoundEvent sound;
    public final float pitch;
    public final float volume;

    GunType(String id, Class weaponClass, boolean auto, float damage, int pellets, int ticksPerShot, int magSize, int reloadTicks, float range,
            float spread, float recoilVertical, float recoilHorizontal, float zoom, float headshotMultiplier,
            Supplier<Item> ammo, SoundEvent sound, float pitch, float volume) {
        this.id = id;
        this.weaponClass = weaponClass;
        this.auto = auto;
        this.damage = damage;
        this.pellets = pellets;
        this.ticksPerShot = ticksPerShot;
        this.magSize = magSize;
        this.reloadTicks = reloadTicks;
        this.range = range;
        this.spread = spread;
        this.recoilVertical = recoilVertical;
        this.recoilHorizontal = recoilHorizontal;
        this.zoom = zoom;
        this.headshotMultiplier = headshotMultiplier;
        this.ammo = ammo;
        this.sound = sound;
        this.pitch = pitch;
        this.volume = volume;
    }

    public boolean is(Class c) {
        return weaponClass == c;
    }

    public String displayName() {
        return switch (this) {
            case G18 -> "G18";
            case DEAGLE -> "Desert Eagle";
            case MP5 -> "MP5";
            case UMP45 -> "UMP45";
            case VECTOR -> "Vector";
            case AK47 -> "AK-47";
            case M4A1 -> "M4A1";
            case M870 -> "M870";
            case AWM -> "AWM";
            case M249 -> "M249";
        };
    }
}
