package com.echoesinthedark.turtlepower.client.model;

import com.echoesinthedark.turtlepower.TurtlePower;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * Model shapes. They are all normal humanoid models with extra pieces:
 * turtles get a 3D shell and mask tails, Splinter gets rat ears, a snout and a tail, and Kraang
 * droids get the alien brain bulging out of their belly.
 */
public final class TmntModels {
    private TmntModels() {}

    public static final ModelLayerLocation TURTLE = layer("turtle");
    public static final ModelLayerLocation RAT = layer("rat");
    public static final ModelLayerLocation KRAANG = layer("kraang");
    public static final ModelLayerLocation HUMAN = layer("human");
    public static final ModelLayerLocation PLAYER_SHELL = layer("player_shell");

    private static ModelLayerLocation layer(String name) {
        return new ModelLayerLocation(TurtlePower.id(name), "main");
    }

    private static MeshDefinition base() {
        MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
        // Use the 64x64 layout for the left limbs too, so both sides can be painted differently.
        PartDefinition root = mesh.getRoot();
        root.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(32, 48)
                .addBox(-1.0F, -2.0F, -2.0F, 4.0F, 12.0F, 4.0F), PartPose.offset(5.0F, 2.0F, 0.0F));
        root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(16, 48)
                .addBox(-2.0F, 0.0F, -2.0F, 4.0F, 12.0F, 4.0F), PartPose.offset(1.9F, 12.0F, 0.0F));
        return mesh;
    }

    public static LayerDefinition human() {
        return LayerDefinition.create(base(), 64, 64);
    }

    public static LayerDefinition turtle() {
        MeshDefinition mesh = base();
        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.getChild("body");
        body.addOrReplaceChild("shell", CubeListBuilder.create().texOffs(0, 32)
                .addBox(-5.0F, -0.5F, 2.0F, 10.0F, 13.0F, 3.0F), PartPose.ZERO);
        PartDefinition head = root.getChild("head");
        head.addOrReplaceChild("mask_tail_left", CubeListBuilder.create().texOffs(0, 58)
                .addBox(-0.5F, -0.5F, 0.0F, 1.0F, 1.0F, 5.0F), PartPose.offsetAndRotation(1.5F, -5.0F, 4.0F, -0.85F, 0.25F, 0.0F));
        head.addOrReplaceChild("mask_tail_right", CubeListBuilder.create().texOffs(48, 58)
                .addBox(-0.5F, -0.5F, 0.0F, 1.0F, 1.0F, 5.0F), PartPose.offsetAndRotation(-1.5F, -5.0F, 4.0F, -0.7F, -0.25F, 0.0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    public static LayerDefinition rat() {
        MeshDefinition mesh = base();
        PartDefinition root = mesh.getRoot();
        PartDefinition head = root.getChild("head");
        head.addOrReplaceChild("ear_left", CubeListBuilder.create().texOffs(0, 32)
                .addBox(-1.0F, -3.0F, -0.5F, 3.0F, 3.0F, 1.0F), PartPose.offset(2.0F, -8.0F, -0.5F));
        head.addOrReplaceChild("ear_right", CubeListBuilder.create().texOffs(8, 32)
                .addBox(-2.0F, -3.0F, -0.5F, 3.0F, 3.0F, 1.0F), PartPose.offset(-2.0F, -8.0F, -0.5F));
        head.addOrReplaceChild("snout", CubeListBuilder.create().texOffs(16, 32)
                .addBox(-1.5F, -3.5F, -7.0F, 3.0F, 3.0F, 3.0F), PartPose.ZERO);
        PartDefinition body = root.getChild("body");
        body.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(28, 32)
                .addBox(-0.5F, -0.5F, 0.0F, 1.0F, 1.0F, 12.0F), PartPose.offsetAndRotation(0.0F, 11.0F, 2.0F, -1.1F, 0.0F, 0.0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    public static LayerDefinition kraang() {
        MeshDefinition mesh = base();
        PartDefinition body = mesh.getRoot().getChild("body");
        body.addOrReplaceChild("brain", CubeListBuilder.create().texOffs(0, 32)
                .addBox(-2.5F, 3.0F, -3.5F, 5.0F, 5.0F, 2.0F), PartPose.ZERO);
        return LayerDefinition.create(mesh, 64, 64);
    }

    public static LayerDefinition playerShell() {
        MeshDefinition mesh = new MeshDefinition();
        mesh.getRoot().addOrReplaceChild("shell", CubeListBuilder.create().texOffs(0, 0)
                .addBox(-5.0F, -0.5F, 2.0F, 10.0F, 13.0F, 3.0F), PartPose.ZERO);
        return LayerDefinition.create(mesh, 32, 32);
    }
}
