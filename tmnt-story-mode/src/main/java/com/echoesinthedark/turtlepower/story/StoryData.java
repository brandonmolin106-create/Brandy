package com.echoesinthedark.turtlepower.story;

import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Everything the story remembers in the world save: where things were built and how far each player got. */
public class StoryData extends SavedData {
    private static final String NAME = "turtlepower_story";

    public boolean built;
    public boolean building;
    public int y0;
    public BlockPos origin = BlockPos.ZERO;
    public final Map<String, BlockPos> pois = new HashMap<>();
    public final Map<String, List<BlockPos>> poiLists = new HashMap<>();
    public final Map<UUID, PlayerProgress> players = new HashMap<>();
    /** Players who were already offered the story in a normal world (so we only ask once). */
    public final List<UUID> offered = new ArrayList<>();

    public static class PlayerProgress {
        public StoryStep step = StoryStep.NOT_STARTED;
        public int counter;
        public boolean stepIntroDone;
        public boolean eventSpawned;
        public long nextEventTick;
        public final Map<com.echoesinthedark.turtlepower.entity.Brother, UUID> brothers =
                new EnumMap<>(com.echoesinthedark.turtlepower.entity.Brother.class);
        @Nullable public UUID bossId;

        CompoundTag save() {
            CompoundTag t = new CompoundTag();
            t.putString("Step", step.name());
            t.putInt("Counter", counter);
            t.putBoolean("IntroDone", stepIntroDone);
            t.putBoolean("EventSpawned", eventSpawned);
            t.putLong("NextEvent", nextEventTick);
            CompoundTag b = new CompoundTag();
            brothers.forEach((k, v) -> b.putUUID(k.name(), v));
            t.put("Brothers", b);
            if (bossId != null) t.putUUID("Boss", bossId);
            return t;
        }

        static PlayerProgress load(CompoundTag t) {
            PlayerProgress p = new PlayerProgress();
            try {
                p.step = StoryStep.valueOf(t.getString("Step"));
            } catch (IllegalArgumentException e) {
                p.step = StoryStep.NOT_STARTED;
            }
            p.counter = t.getInt("Counter");
            p.stepIntroDone = t.getBoolean("IntroDone");
            p.eventSpawned = t.getBoolean("EventSpawned");
            p.nextEventTick = t.getLong("NextEvent");
            CompoundTag b = t.getCompound("Brothers");
            for (com.echoesinthedark.turtlepower.entity.Brother br : com.echoesinthedark.turtlepower.entity.Brother.values()) {
                if (b.hasUUID(br.name())) p.brothers.put(br, b.getUUID(br.name()));
            }
            if (t.hasUUID("Boss")) p.bossId = t.getUUID("Boss");
            return p;
        }
    }

    public static StoryData get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(StoryData::load, StoryData::new, NAME);
    }

    public PlayerProgress progress(UUID player) {
        return players.computeIfAbsent(player, u -> new PlayerProgress());
    }

    @Nullable
    public BlockPos poi(String key) {
        return pois.get(key);
    }

    public List<BlockPos> poiList(String key) {
        return poiLists.getOrDefault(key, List.of());
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        tag.putBoolean("Built", built);
        tag.putInt("Y0", y0);
        tag.put("Origin", NbtUtils.writeBlockPos(origin));
        CompoundTag p = new CompoundTag();
        pois.forEach((k, v) -> p.put(k, NbtUtils.writeBlockPos(v)));
        tag.put("Pois", p);
        CompoundTag pl = new CompoundTag();
        poiLists.forEach((k, v) -> {
            ListTag list = new ListTag();
            v.forEach(bp -> list.add(NbtUtils.writeBlockPos(bp)));
            pl.put(k, list);
        });
        tag.put("PoiLists", pl);
        CompoundTag players = new CompoundTag();
        this.players.forEach((k, v) -> players.put(k.toString(), v.save()));
        tag.put("Players", players);
        ListTag off = new ListTag();
        offered.forEach(u -> off.add(NbtUtils.createUUID(u)));
        tag.put("Offered", off);
        return tag;
    }

    public static StoryData load(CompoundTag tag) {
        StoryData d = new StoryData();
        d.built = tag.getBoolean("Built");
        d.y0 = tag.getInt("Y0");
        d.origin = NbtUtils.readBlockPos(tag.getCompound("Origin"));
        CompoundTag p = tag.getCompound("Pois");
        for (String k : p.getAllKeys()) d.pois.put(k, NbtUtils.readBlockPos(p.getCompound(k)));
        CompoundTag pl = tag.getCompound("PoiLists");
        for (String k : pl.getAllKeys()) {
            ListTag list = pl.getList(k, Tag.TAG_COMPOUND);
            List<BlockPos> out = new ArrayList<>();
            for (int i = 0; i < list.size(); i++) out.add(NbtUtils.readBlockPos(list.getCompound(i)));
            d.poiLists.put(k, out);
        }
        CompoundTag players = tag.getCompound("Players");
        for (String k : players.getAllKeys()) {
            try {
                d.players.put(UUID.fromString(k), PlayerProgress.load(players.getCompound(k)));
            } catch (IllegalArgumentException ignored) {
            }
        }
        ListTag off = tag.getList("Offered", Tag.TAG_INT_ARRAY);
        for (Tag t : off) d.offered.add(NbtUtils.loadUUID(t));
        return d;
    }
}
