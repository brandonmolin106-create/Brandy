package com.echoesinthedark.echostrike.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraftforge.client.settings.KeyConflictContext;
import org.lwjgl.glfw.GLFW;

public final class ModKeys {
    private ModKeys() {}

    public static final String CATEGORY = "key.categories.echostrike";
    public static final KeyMapping RELOAD = new KeyMapping("key.echostrike.reload", KeyConflictContext.IN_GAME, InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, CATEGORY);
}
