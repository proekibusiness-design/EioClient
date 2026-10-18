package com.eio.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.*;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.ScreenKeyboardEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.*;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.options.controls.KeyBindsScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;

import java.awt.Color;
import java.io.*;
import java.nio.file.*;
import java.time.Instant;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public final class EioClient implements ClientModInitializer {
    public static final String VERSION = "0.26.1";
    public static final String BUILD_ID = "EIO-0261-MINEFIX1";
    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path CONFIG_BACKUP = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties.bak");
    private static final Path PROFILE_DIR = FabricLoader.getInstance().getConfigDir().resolve("eio").resolve("profiles");
    private static final Path DIAGNOSTIC_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-diagnostics.log");
    private static final List<Mod> MODS = new ArrayList<>();
    private static final Map<String, Mod> MOD_INDEX = new LinkedHashMap<>();
    private static final Map<String, Waypoint> WAYPOINTS = new LinkedHashMap<>();
    private static KeyMapping.Category keyCategory;
    private static KeyMapping guiKey;
    private static boolean guiOpen;
    private static double clickAccumulator;
    private static int auraCooldown;
    private static int triggerCooldown;
    private static Entity combatTarget;
    private static BlockPos chunkMineTarget;
    private static int chunkMineRearmTicks;
    private static int chunkMineAimTicks;
    private static int chunkMineChunkX = Integer.MIN_VALUE;
    private static int chunkMineChunkZ = Integer.MIN_VALUE;
    private static final Set<BlockPos> CHUNK_MINE_SKIPPED = new HashSet<>();
    private static BlockPos nukerTarget;
    private static int nukerRearmTicks;
    private static int nukerAimTicks;
    private static final Set<BlockPos> NUKER_SKIPPED = new HashSet<>();
    private static BlockPos areaMineTarget;
    private static int areaMineRearmTicks;
    private static int areaMineAimTicks;
    private static int areaNavIndex;
    private static int areaMoveTicks;
    private static int areaMinedThisPass;
    private static boolean areaMoveRequested;
    private static boolean areaComplete;
    private static BlockPos areaDestroyTarget;
    private static boolean areaDestroyStarted;
    private static int areaMineWorkTicks;
    private static final Set<BlockPos> AREA_MINE_SKIPPED = new HashSet<>();
    private static boolean attackForced;
    private static boolean toolSaverWarned;
    private static MobEffectInstance fullbrightInjected;
    private static String notificationText = "";
    private static long notificationUntil;
    private static Entity followTarget;
    private static boolean jumpForced;
    private static boolean sneakForced;
    private static boolean forwardForced;
    private static boolean flyForced;
    private static boolean flyPrevMayfly;
    private static boolean flyPrevFlying;
    private static float flyPrevSpeed = 0.05f;
    private static boolean lowHealthAlerted;
    private static int lowHealthCooldown;
    private static boolean creativeAssistWarned;
    private static boolean creativeAssistSpeedForced;
    private static float creativeAssistPrevSpeed = 0.05f;
    private static String configSource = "defaults";
    private static final ArrayDeque<Long> ATTACK_TIMES = new ArrayDeque<>();
    private static boolean runtimeSafeMode;
    private static int runtimeFaults;
    private static String lastRuntimeFault = "none";
    private static final CompatibilityState COMPAT = new CompatibilityState();
    private static long suppressedOutOfRangeAttacks;
    private static final long sessionStartedNanos = System.nanoTime();
    private static final DateTimeFormatter CLOCK_FORMATTER = DateTimeFormatter.ofPattern("HH:mm:ss", Locale.ROOT);
    private static final String[] FOLLOW_MOB_IDS = {
            "entity.minecraft.allay", "entity.minecraft.armadillo", "entity.minecraft.axolotl", "entity.minecraft.bat",
            "entity.minecraft.bee", "entity.minecraft.blaze", "entity.minecraft.bogged", "entity.minecraft.breeze",
            "entity.minecraft.camel", "entity.minecraft.cat", "entity.minecraft.cave_spider", "entity.minecraft.chicken",
            "entity.minecraft.cod", "entity.minecraft.cow", "entity.minecraft.creaking", "entity.minecraft.creeper",
            "entity.minecraft.dolphin", "entity.minecraft.donkey", "entity.minecraft.drowned", "entity.minecraft.elder_guardian",
            "entity.minecraft.enderman", "entity.minecraft.endermite", "entity.minecraft.evoker", "entity.minecraft.fox",
            "entity.minecraft.frog", "entity.minecraft.ghast", "entity.minecraft.glow_squid", "entity.minecraft.goat",
            "entity.minecraft.guardian", "entity.minecraft.hoglin", "entity.minecraft.horse", "entity.minecraft.husk",
            "entity.minecraft.iron_golem", "entity.minecraft.llama", "entity.minecraft.magma_cube", "entity.minecraft.mooshroom",
            "entity.minecraft.mule", "entity.minecraft.ocelot", "entity.minecraft.panda", "entity.minecraft.parrot",
            "entity.minecraft.phantom", "entity.minecraft.pig", "entity.minecraft.piglin", "entity.minecraft.piglin_brute",
            "entity.minecraft.pillager", "entity.minecraft.polar_bear", "entity.minecraft.pufferfish", "entity.minecraft.rabbit",
            "entity.minecraft.ravager", "entity.minecraft.salmon", "entity.minecraft.sheep", "entity.minecraft.shulker",
            "entity.minecraft.silverfish", "entity.minecraft.skeleton", "entity.minecraft.skeleton_horse", "entity.minecraft.slime",
            "entity.minecraft.sniffer", "entity.minecraft.snow_golem", "entity.minecraft.spider", "entity.minecraft.squid",
            "entity.minecraft.stray", "entity.minecraft.strider", "entity.minecraft.tadpole", "entity.minecraft.trader_llama",
            "entity.minecraft.tropical_fish", "entity.minecraft.turtle", "entity.minecraft.vex", "entity.minecraft.villager",
            "entity.minecraft.vindicator", "entity.minecraft.wandering_trader", "entity.minecraft.warden", "entity.minecraft.witch",
            "entity.minecraft.wither", "entity.minecraft.wither_skeleton", "entity.minecraft.wolf", "entity.minecraft.zoglin",
            "entity.minecraft.zombie", "entity.minecraft.zombie_horse", "entity.minecraft.zombie_villager", "entity.minecraft.zombified_piglin"
    };

    static {
        mod("Kill Aura", "Combat", "Attacks the nearest allowed living target inside the configured range.", InputConstants.KEY_K)
                .num("Range", 4.0, 1.0, 6.0, 0.25, "Maximum distance at which a target can be selected.")
                .num("Delay", 5.0, 1.0, 20.0, 1.0, "Ticks between attack attempts. Lower values attack more often.")
                .num("FOV", 180.0, 30.0, 360.0, 15.0, "Horizontal field of view in degrees used for target selection.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible living targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Kill Aura may target.");
        mod("Auto Clicker", "Combat", "Automatically attacks a valid target near your crosshair at the configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Attack attempts per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance used when selecting a click target.")
                .num("FOV", 18.0, 5.0, 90.0, 1.0, "Maximum angle from your crosshair used when selecting a target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Auto Clicker may target.");
        mod("Reach", "Combat", "Shows the nearest allowed target inside a configurable 3-10 block radius without changing server hit distance.", -1)
                .num("Range", 6.0, 3.0, 10.0, 0.25, "Target scan and display radius in blocks.")
                .bool("Players", true, "Include players in Reach display targeting.")
                .bool("Mobs", true, "Include non-player living entities in Reach display targeting.")
                .bool("Invisible", false, "Include invisible living entities in Reach display targeting.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Reach may display as targets.");

        mod("Target Lock", "Combat", "Tracks one allowed target and can keep your view centered on it without attacking automatically.", -1)
                .num("Range", 6.0, 2.0, 10.0, 0.25, "Maximum lock distance.")
                .num("FOV", 120.0, 20.0, 360.0, 10.0, "Target acquisition field of view.")
                .bool("Face Target", true, "Continuously face the locked target.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Target Lock may select.");
        mod("Trigger Bot", "Combat", "Attacks an allowed living entity only while your crosshair is directly over it.", -1)
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum direct-crosshair attack distance.")
                .num("Delay", 5.0, 1.0, 20.0, 1.0, "Ticks between trigger attacks.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Trigger Bot may attack.");
        mod("Combat Sprint", "Combat", "Automatically sprints while an allowed target is nearby and inside the configured view cone.", -1)
                .num("Range", 8.0, 2.0, 12.0, 0.5, "Target detection range used to activate sprinting.")
                .num("FOV", 180.0, 30.0, 360.0, 15.0, "Target detection field of view.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Combat Sprint may react to.");

        mod("Sprint", "Movement", "Automatically sprints while moving forward.", InputConstants.KEY_R)
                .bool("Hunger Check", true, "Only sprint when your food level is high enough.");
        mod("AutoWalk", "Movement", "Keeps moving forward until disabled.", InputConstants.KEY_G);
        mod("Follow", "Movement", "Follows the nearest allowed player or selected mob type while keeping a configurable distance.", InputConstants.KEY_H)
                .num("Search Range", 24.0, 4.0, 64.0, 1.0, "Maximum distance used when finding a follow target.")
                .num("Distance", 3.0, 1.0, 12.0, 0.5, "Distance to maintain behind the follow target.")
                .bool("Players", true, "Allow following players.")
                .bool("Mobs", true, "Master switch for following non-player living entities.")
                .bool("Face Target", true, "Turn your view toward the follow target.")
                .bool("Sprint", true, "Sprint while closing distance to the target.")
                .mobList("Mob Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Follow is allowed to target.");
        mod("Fly", "Movement", "Creative-style client flight with adjustable speed.", InputConstants.KEY_F)
                .num("Speed", 0.10, 0.05, 1.00, 0.05, "Local flying speed while the module is enabled.");
        mod("SafeWalk", "Movement", "Automatically sneaks while moving on the ground to reduce edge falls.", -1);
        mod("Auto Jump", "Movement", "Jumps automatically when you run into a horizontal obstacle.", -1);
        mod("Auto Swim", "Movement", "Holds jump while you are in water so swimming upward is effortless.", -1);

        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
        mod("Creative Assist", "Player", "Creative-flight helper that activates only when the server/player already grants flight permission.", -1)
                .bool("Auto Fly", true, "Automatically enter flight while creative flight permission is available.")
                .num("Flight Speed", 0.10, 0.05, 1.00, 0.05, "Creative flight speed while this helper is active.");
        mod("Low Health Alert", "Player", "Shows an urgent HUD alert when your health drops below a configurable threshold.", -1)
                .num("Threshold", 6.0, 1.0, 20.0, 0.5, "Health value that triggers the warning.")
                .num("Cooldown", 10.0, 2.0, 60.0, 1.0, "Minimum seconds between repeated low-health warnings.");
        mod("Inventory Info", "Player", "Shows occupied inventory slots on the HUD.", -1);
        mod("Durability HUD", "Player", "Shows durability of the selected item.", -1);

        mod("Coordinates", "Render", "Shows your XYZ position.", -1)
                .num("Decimals", 1.0, 0.0, 3.0, 1.0, "Number of decimal places used for coordinates.");
        mod("FPS", "Render", "Shows current FPS.", -1);
        mod("Active Modules", "Render", "Lists enabled modules on the HUD.", -1)
                .num("Max", 12.0, 3.0, 20.0, 1.0, "Maximum number of enabled modules shown before collapsing the rest.");
        mod("Target HUD", "Render", "Shows the current crosshair or Follow target and its distance.", -1);
        mod("Health", "Render", "Shows current and maximum health on the HUD.", -1);
        mod("Speed", "Movement", "Adjusts horizontal movement speed while you are moving, with an optional live HUD readout.", -1)
                .num("Multiplier", 1.8, 1.0, 10.0, 0.1, "Horizontal movement multiplier. Extreme values may be rejected or corrected by multiplayer servers.")
                .bool("Ground Only", true, "Only apply the speed multiplier while standing on the ground.")
                .bool("Show HUD", true, "Show current horizontal blocks-per-second while Speed is enabled.");
        mod("Facing", "Render", "Shows the cardinal direction you are facing.", -1);
        mod("Rotation", "Render", "Shows your current yaw and pitch.", -1);
        mod("Memory", "Render", "Shows JVM memory currently used by Minecraft.", -1);
        mod("Clock", "Render", "Shows your local 24-hour clock.", -1);
        mod("CPS", "Render", "Shows attacks performed by Eio during the last rolling second.", -1);
        mod("Keystrokes", "Render", "Shows live movement, jump and sprint input state.", -1);
        mod("Held Item", "Render", "Shows the selected item name and stack count.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);

        mod("Chunk Info", "World", "Shows your current chunk coordinates.", -1);
        mod("Waypoints", "World", "Shows your nearest saved waypoint and distance.", -1);

        mod("Auto Mine", "Mining", "Keeps normal mining input held while your crosshair is on a block.", -1)
                .bool("Stop In GUI", true, "Release mining input while Eio's ClickGUI is open.");
        mod("Tunnel Miner", "Mining", "Straight-line tunneling helper that can hold forward and mine continuously.", -1)
                .bool("Auto Walk", true, "Hold forward while tunneling.")
                .bool("Sprint", false, "Sprint while moving through the tunnel.")
                .bool("Pause On Entity", true, "Do not hold mining input while an entity is directly under your crosshair.");
        mod("Chunk Miner", "Mining", "Continuously mines nearby valid blocks in your current chunk, re-arming normal mining input between targets.", -1)
                .num("Radius", 4.0, 2.0, 5.0, 0.5, "Local block scan radius. Server interaction range still applies.")
                .num("Vertical", 2.0, 1.0, 4.0, 1.0, "Vertical scan distance above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next block.")
                .num("Aim Timeout", 12.0, 4.0, 40.0, 1.0, "Ticks allowed to acquire the selected block under the crosshair before trying another block.")
                .bool("Exposed Only", true, "Only choose blocks with at least one air-adjacent face.")
                .bool("Avoid Below", true, "Avoid selecting blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the selected chunk-mining block.");
        mod("Nuker", "Mining", "Aggressively clears nearby breakable blocks with continuous retargeting while still using normal mining interaction.", -1)
                .num("Radius", 5.0, 1.0, 6.0, 0.5, "Area-clear radius around you. Normal server interaction distance still applies.")
                .num("Vertical", 3.0, 1.0, 5.0, 1.0, "Vertical area cleared above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 3.0, 1.0, "Ticks to release attack before starting the next Nuker target.")
                .num("Aim Timeout", 8.0, 4.0, 30.0, 1.0, "Ticks allowed to acquire a block before skipping it temporarily.")
                .bool("Exposed Only", true, "Only target blocks with at least one exposed face.")
                .bool("Avoid Below", true, "Avoid mining blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the active Nuker target.");
        mod("Area Miner", "Mining", "Serpentine tunnel miner: clears the next lane cell straight ahead, moves into it, turns at the boundary, shifts one cell and works back across the selected zone.", -1)
                .point("Corner A", "Stand at the first horizontal corner and left-click this row to set it here. Right-click clears it.")
                .point("Corner B", "Stand at the opposite horizontal corner and left-click this row to set it here. Right-click clears it.")
                .num("Depth", 8.0, 1.0, 64.0, 1.0, "Vertical depth included in the selected zone. Area Miner only targets the current serpentine lane column instead of mining surrounding blocks.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next area target.")
                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to line up with a target before temporarily skipping it.")
                .num("Mine Timeout", 240.0, 40.0, 600.0, 20.0, "Maximum ticks to work one block before skipping it and continuing the lane.")
                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one navigation cell before moving to the next cell.")
                .bool("Auto Move", true, "Walk the serpentine lane path after the block column directly ahead is clear.")
                .bool("Sprint", false, "Sprint while Area Miner is navigating between cells.")
                .bool("Auto Jump", true, "Jump over simple one-block obstacles while Area Miner is moving.")
                .bool("Exposed Only", true, "Mine only blocks with an air-adjacent face, exposing deeper layers progressively.")
                .bool("Face Block", true, "Turn your view toward the current Area Miner target.");
        mod("Tool Saver", "Mining", "Stops Eio mining automation before the held damageable tool reaches the configured remaining durability.", -1)
                .num("Remaining", 12.0, 1.0, 100.0, 1.0, "Minimum durability to keep in reserve.")
                .bool("Notify", true, "Show a warning when mining pauses to protect the tool.");
        mod("Mining HUD", "Mining", "Shows the current automatic mining target and held-tool durability.", -1)
                .bool("Target", true, "Show the current Chunk Miner target coordinates.")
                .bool("Tool", true, "Show remaining durability for the selected tool.");

        mod("Compatibility Guard", "Misc", "Keeps automated interactions inside vanilla reach and yields briefly when the server corrects player position.", -1)
                .bool("Vanilla Ranges", true, "Require Minecraft's own entity/block interaction-range checks before automated actions.")
                .bool("Pause On Correction", true, "Temporarily yield Eio movement/combat/mining after a server position correction or teleport.")
                .num("Pause Ticks", 4.0, 1.0, 20.0, 1.0, "Ticks to yield automation after a server position correction.")
                .bool("Diagnostics", true, "Write server-position telemetry to eio-diagnostics.log.");

        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1)
                .bool("Build ID", false, "Also show the exact Eio QA build identifier.");
        mod("Session Timer", "Misc", "Shows how long the current Eio client session has been running.", -1);
        mod("Notifications", "Misc", "Shows a small upper-left card when modules are toggled.", -1)
                .num("Seconds", 2.0, 0.5, 5.0, 0.5, "How long toggle notifications remain visible.")
                .bool("Show Disable", true, "Show notifications when a module is disabled as well as enabled.");
    }

    private static Mod mod(String name, String category, String description, int defaultKey) {
        Mod m = new Mod(name, category, description, defaultKey);
        String indexKey = name.toLowerCase(Locale.ROOT);
        if (MOD_INDEX.putIfAbsent(indexKey, m) != null) throw new IllegalStateException("Duplicate module: " + name);
        MODS.add(m);
        return m;
    }

    @Override
    public void onInitializeClient() {
        validateModel();
        load();
        keyCategory = KeyMapping.Category.register(Identifier.fromNamespaceAndPath("eioclient", "general"));
        guiKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
                "key.eioclient.clickgui", InputConstants.Type.KEYBOARD, InputConstants.KEY_RSHIFT, keyCategory));
        for (Mod m : MODS) {
            int key = m.defaultKey < 0 ? InputConstants.UNKNOWN.getValue() : m.defaultKey;
            m.bind = KeyMappingHelper.registerKeyMapping(new KeyMapping(
                    "key.eioclient." + slug(m.name), InputConstants.Type.KEYBOARD, key, keyCategory));
        }

        ClientTickEvents.END_CLIENT_TICK.register(EioClient::guardedTick);
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient", "hud"), EioClient::guardedHud);
        ScreenEvents.AFTER_INIT.register((client, screen, w, h) -> {
            if (screen instanceof TitleScreen) {
                ScreenEvents.afterExtract(screen).register((s, g, mx, my, delta) -> drawBrand(g, s.width));
            }
            if (screen instanceof ClickGui) {
                ScreenKeyboardEvents.beforeKeyPress(screen).register((s, event) -> {
                    if (guiKey != null && guiKey.matches(event)) s.onClose();
                });
            }
        });
        ClientCommandRegistrationCallback.EVENT.register((dispatcher, access) -> dispatcher.register(
                ClientCommands.literal("eio")
                        .executes(c -> { openGui(); return 1; })
                        .then(ClientCommands.literal("gui").executes(c -> { openGui(); return 1; }))
                        .then(ClientCommands.literal("list").executes(c -> {
                            c.getSource().sendFeedback(Component.literal(summary())); return 1;
                        }))
                        .then(ClientCommands.literal("doctor").executes(c -> {
                            long bound = MODS.stream().filter(m -> m.bind != null && !m.bind.isUnbound()).count();
                            String report = validateModel() + " | Eio " + VERSION + " [" + BUILD_ID + "] | enabled=" + enabledCount()
                                    + " bound=" + bound + " | GUI=760x430 modern-nav-glass | config=" + configSource
                                    + " | backup=" + Files.exists(CONFIG_BACKUP) + " | safeMode=" + runtimeSafeMode
                                    + " | faults=" + runtimeFaults + " | lastFault=" + lastRuntimeFault
                                    + " | serverCorrections=" + COMPAT.correctionCount() + " correctionPause=" + COMPAT.pauseTicks()
                                    + " | blockedOutOfRangeAttacks=" + suppressedOutOfRangeAttacks;
                            c.getSource().sendFeedback(Component.literal(report));
                            return 1;
                        }))
                        .then(ClientCommands.literal("selftest").executes(c -> {
                            String report = selfTestSummary();
                            appendDiagnostic("SELFTEST " + report);
                            c.getSource().sendFeedback(Component.literal(report));
                            return report.startsWith("selftest=PASS") ? 1 : 0;
                        }))
                        .then(ClientCommands.literal("panic").executes(c -> {
                            panic(Minecraft.getInstance());
                            c.getSource().sendFeedback(Component.literal("Eio panic: all modules disabled and owned inputs released"));
                            return 1;
                        }))
                        .then(ClientCommands.literal("resetsettings").executes(c -> {
                            resetAllSettings();
                            save();
                            c.getSource().sendFeedback(Component.literal("Eio settings reset to defaults"));
                            return 1;
                        }))
                        .then(ClientCommands.literal("reloadconfig").executes(c -> {
                            releaseRuntimeState(Minecraft.getInstance());
                            load();
                            c.getSource().sendFeedback(Component.literal("Eio config reloaded from " + configSource));
                            return 1;
                        }))
                        .then(ClientCommands.literal("recover").executes(c -> {
                            runtimeSafeMode = false;
                            notifyMessage("EIO SAFE MODE CLEARED", 0xFF70DFA8, 2200L);
                            appendDiagnostic("RECOVER manual");
                            c.getSource().sendFeedback(Component.literal("Eio safe mode cleared; modules may run again"));
                            return 1;
                        }))
                        .then(ClientCommands.literal("profile")
                                .then(ClientCommands.literal("save")
                                        .then(ClientCommands.argument("name", StringArgumentType.greedyString()).executes(c -> {
                                            String name = StringArgumentType.getString(c, "name");
                                            boolean ok = saveProfile(name);
                                            c.getSource().sendFeedback(Component.literal(ok ? "Saved Eio profile " + cleanProfileName(name) : "Could not save profile"));
                                            return ok ? 1 : 0;
                                        })))
                                .then(ClientCommands.literal("load")
                                        .then(ClientCommands.argument("name", StringArgumentType.greedyString()).executes(c -> {
                                            String name = StringArgumentType.getString(c, "name");
                                            boolean ok = loadProfile(name);
                                            c.getSource().sendFeedback(Component.literal(ok ? "Loaded Eio profile " + cleanProfileName(name) : "Profile not found or invalid"));
                                            return ok ? 1 : 0;
                                        })))
                                .then(ClientCommands.literal("delete")
                                        .then(ClientCommands.argument("name", StringArgumentType.greedyString()).executes(c -> {
                                            String name = StringArgumentType.getString(c, "name");
                                            boolean ok = deleteProfile(name);
                                            c.getSource().sendFeedback(Component.literal(ok ? "Deleted Eio profile " + cleanProfileName(name) : "Profile not found"));
                                            return ok ? 1 : 0;
                                        })))
                                .then(ClientCommands.literal("list").executes(c -> {
                                    c.getSource().sendFeedback(Component.literal(profileSummary()));
                                    return 1;
                                })))
                        .then(ClientCommands.literal("toggle")
                                .then(ClientCommands.argument("module", StringArgumentType.greedyString()).executes(c -> {
                                    Mod m = find(StringArgumentType.getString(c, "module"));
                                    if (m == null) { c.getSource().sendFeedback(Component.literal("Unknown module")); return 0; }
                                    toggle(m); return 1;
                                })))
                        .then(ClientCommands.literal("followtarget").executes(c -> {
                            Minecraft mc = Minecraft.getInstance();
                            if (mc.hitResult instanceof EntityHitResult hit && hit.getEntity() instanceof LivingEntity) {
                                followTarget = hit.getEntity();
                                c.getSource().sendFeedback(Component.literal("Follow target: " + followTarget.getDisplayName().getString()));
                                return 1;
                            }
                            c.getSource().sendFeedback(Component.literal("Look directly at a living entity first"));
                            return 0;
                        }))
                        .then(ClientCommands.literal("followclear").executes(c -> {
                            followTarget = null;
                            c.getSource().sendFeedback(Component.literal("Follow target cleared"));
                            return 1;
                        }))
                        .then(ClientCommands.literal("area")
                                .then(ClientCommands.literal("pos1").executes(c -> {
                                    Minecraft mc = Minecraft.getInstance();
                                    if (mc.player == null) return 0;
                                    Mod area = find("Area Miner");
                                    area.point("Corner A").set(mc.player.blockPosition());
                                    resetAreaRuntime(); save();
                                    c.getSource().sendFeedback(Component.literal("Area corner A set to " + area.point("Corner A").display()));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("pos2").executes(c -> {
                                    Minecraft mc = Minecraft.getInstance();
                                    if (mc.player == null) return 0;
                                    Mod area = find("Area Miner");
                                    area.point("Corner B").set(mc.player.blockPosition());
                                    resetAreaRuntime(); save();
                                    c.getSource().sendFeedback(Component.literal("Area corner B set to " + area.point("Corner B").display()));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("clear").executes(c -> {
                                    Mod area = find("Area Miner");
                                    area.point("Corner A").reset(); area.point("Corner B").reset();
                                    resetAreaRuntime(); save();
                                    c.getSource().sendFeedback(Component.literal("Area Miner corners cleared"));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("status").executes(c -> {
                                    c.getSource().sendFeedback(Component.literal(areaStatus(find("Area Miner"))));
                                    return 1;
                                })))
                        .then(ClientCommands.literal("waypoint")
                                .then(ClientCommands.literal("add")
                                        .then(ClientCommands.argument("name", StringArgumentType.greedyString()).executes(c -> {
                                            Minecraft mc = Minecraft.getInstance();
                                            if (mc.player == null) return 0;
                                            String name = StringArgumentType.getString(c, "name").trim();
                                            if (name.isEmpty()) return 0;
                                            WAYPOINTS.put(name, new Waypoint(name, mc.player.getX(), mc.player.getY(), mc.player.getZ()));
                                            save();
                                            c.getSource().sendFeedback(Component.literal("Saved waypoint " + name));
                                            return 1;
                                        })))
                                .then(ClientCommands.literal("remove")
                                        .then(ClientCommands.argument("name", StringArgumentType.greedyString()).executes(c -> {
                                            String name = StringArgumentType.getString(c, "name").trim();
                                            boolean removed = WAYPOINTS.remove(name) != null;
                                            save();
                                            c.getSource().sendFeedback(Component.literal(removed ? "Removed waypoint " + name : "Waypoint not found"));
                                            return removed ? 1 : 0;
                                        })))
                                .then(ClientCommands.literal("clear").executes(c -> {
                                    WAYPOINTS.clear(); save(); c.getSource().sendFeedback(Component.literal("Cleared waypoints")); return 1;
                                }))
                                .then(ClientCommands.literal("list").executes(c -> {
                                    c.getSource().sendFeedback(Component.literal(waypointSummary())); return 1;
                                })))
        ));
    }

    private static String slug(String s) {
        return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "_").replaceAll("^_+|_+$", "");
    }

    private static void openGui() {
        if (guiOpen) return;
        Minecraft.getInstance().setScreenAndShow(new ClickGui());
    }

    public static void onServerPositionCorrection(int id) {
        Minecraft mc = Minecraft.getInstance();
        Mod guard = find("Compatibility Guard");
        int pause = guard != null && guard.enabled && guard.bool("Pause On Correction").value
                ? Math.max(1, (int) Math.round(guard.num("Pause Ticks").value)) : 0;
        COMPAT.onServerCorrection(id, pause, System.currentTimeMillis());
        if (guard != null && guard.enabled) releaseCorrectionSensitiveState(mc);
        if (guard != null && guard.enabled && guard.bool("Diagnostics").value) {
            appendDiagnostic("SERVER_POSITION id=" + id + " pause=" + pause + " localServer=" + mc.isLocalServer());
        }
    }

    private static void guardedTick(Minecraft mc) {
        try {
            if (runtimeSafeMode) {
                while (guiKey != null && guiKey.consumeClick()) if (!guiOpen) openGui();
                return;
            }
            tick(mc);
        } catch (Throwable t) {
            enterSafeMode("tick", t, mc);
        }
    }

    private static void guardedHud(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (runtimeSafeMode) {
            if (mc.player != null) {
                g.fill(3, 3, 183, 27, 0xD0181210);
                g.text(mc.font, "Eio Safe Mode", 8, 7, 0xFFFFA071, true);
                g.text(mc.font, "/eio recover after fixing the module", 8, 17, 0xFFD9E0E6, false);
            }
            return;
        }
        try {
            hud(g, dt);
        } catch (Throwable t) {
            enterSafeMode("hud", t, mc);
        }
    }

    private static void enterSafeMode(String stage, Throwable t, Minecraft mc) {
        runtimeFaults++;
        String message = t.getMessage() == null ? "" : t.getMessage().replace('\n', ' ').replace('\r', ' ');
        if (message.length() > 80) message = message.substring(0, 80);
        lastRuntimeFault = stage + ":" + t.getClass().getSimpleName() + (message.isEmpty() ? "" : "(" + message + ")");
        appendDiagnostic("FAULT " + lastRuntimeFault);
        try { releaseRuntimeState(mc); } catch (Throwable ignored) {}
        runtimeSafeMode = true;
        notifyMessage("EIO SAFE MODE - /eio recover", 0xFFFF9B72, 5000L);
    }

    private static void appendDiagnostic(String line) {
        try {
            Files.createDirectories(DIAGNOSTIC_LOG.getParent());
            Files.writeString(DIAGNOSTIC_LOG, Instant.now() + " " + line + System.lineSeparator(),
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception ignored) {}
    }

    private static String selfTestSummary() {
        List<String> failures = new ArrayList<>();
        try { validateModel(); } catch (Throwable t) { failures.add("model:" + t.getClass().getSimpleName()); }
        if (guiKey == null) failures.add("guiKey:null");
        long missingBinds = MODS.stream().filter(m -> m.bind == null).count();
        if (missingBinds > 0) failures.add("binds:" + missingBinds);
        Set<String> boundKeys = new HashSet<>();
        int conflicts = 0;
        for (Mod m : MODS) if (m.bind != null && !m.bind.isUnbound()) {
            String key = m.bind.getTranslatedKeyMessage().getString();
            if (!boundKeys.add(key)) conflicts++;
        }
        try {
            Files.createDirectories(CONFIG.getParent());
            Path probe = CONFIG.resolveSibling(".eio-write-test");
            Files.writeString(probe, "ok", StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            Files.deleteIfExists(probe);
        } catch (Throwable t) { failures.add("configWrite:" + t.getClass().getSimpleName()); }
        try { Files.createDirectories(PROFILE_DIR); } catch (Throwable t) { failures.add("profiles:" + t.getClass().getSimpleName()); }
        String state = failures.isEmpty() ? "PASS" : "FAIL";
        return "selftest=" + state + " modules=" + MODS.size() + " keyConflicts=" + conflicts
                + " safeMode=" + runtimeSafeMode + " faults=" + runtimeFaults
                + (failures.isEmpty() ? "" : " issues=" + String.join(",", failures));
    }

    private static String cleanProfileName(String raw) {
        String name = raw == null ? "" : raw.trim().replaceAll("[^A-Za-z0-9_-]+", "_");
        if (name.length() > 32) name = name.substring(0, 32);
        return name;
    }

    private static Properties snapshotProperties() {
        Properties p = new Properties();
        for (Mod m : MODS) {
            p.setProperty("enabled." + m.name, Boolean.toString(m.enabled));
            for (Setting setting : m.settings) {
                if (setting instanceof BoolSetting b) p.setProperty("setting." + m.name + "." + setting.name, Boolean.toString(b.value));
                else if (setting instanceof NumSetting n) p.setProperty("setting." + m.name + "." + setting.name, Double.toString(n.value));
                else if (setting instanceof MobListSetting ml) p.setProperty("mobfilter." + m.name + "." + setting.name, ml.disabledCsv());
                else if (setting instanceof PointSetting point && point.value != null) p.setProperty("point." + m.name + "." + setting.name, point.csv());
            }
        }
        p.setProperty("_schema", "5");
        p.setProperty("_lastVersion", VERSION);
        for (Waypoint w : WAYPOINTS.values()) p.setProperty("wp." + w.name, w.x + "," + w.y + "," + w.z);
        return p;
    }

    private static void applyProperties(Properties p, String source) {
        configSource = source;
        for (Mod m : MODS) {
            String enabledDefault = (m.name.equals("Notifications") || m.name.equals("Compatibility Guard")) ? "true" : "false";
            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, enabledDefault));
            for (Setting setting : m.settings) {
                if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                else if (setting instanceof MobListSetting ml) ml.reset();
                else if (setting instanceof PointSetting point) point.reset();
                if (setting instanceof MobListSetting ml) {
                    ml.loadDisabledCsv(p.getProperty("mobfilter." + m.name + "." + setting.name, ""));
                    continue;
                }
                if (setting instanceof PointSetting point) {
                    point.load(p.getProperty("point." + m.name + "." + setting.name));
                    continue;
                }
                String v = p.getProperty("setting." + m.name + "." + setting.name);
                if (v == null) continue;
                try {
                    if (setting instanceof BoolSetting b) b.value = Boolean.parseBoolean(v);
                    else if (setting instanceof NumSetting n) n.set(Double.parseDouble(v));
                } catch (Exception ignored) {}
            }
        }
        WAYPOINTS.clear();
        for (String key : p.stringPropertyNames()) if (key.startsWith("wp.")) {
            String name = key.substring(3);
            try {
                String[] a = p.getProperty(key).split(",");
                if (a.length == 3) WAYPOINTS.put(name, new Waypoint(name, Double.parseDouble(a[0]), Double.parseDouble(a[1]), Double.parseDouble(a[2])));
            } catch (Exception ignored) {}
        }
    }

    private static boolean saveProfile(String raw) {
        String name = cleanProfileName(raw);
        if (name.isEmpty()) return false;
        try {
            Files.createDirectories(PROFILE_DIR);
            Path target = PROFILE_DIR.resolve(name + ".properties");
            Path tmp = PROFILE_DIR.resolve(name + ".properties.tmp");
            try (OutputStream out = Files.newOutputStream(tmp, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
                snapshotProperties().store(out, "Eio profile " + name + " / " + VERSION);
            }
            try { Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
            catch (AtomicMoveNotSupportedException ex) { Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING); }
            return true;
        } catch (Exception e) { appendDiagnostic("PROFILE SAVE " + e.getClass().getSimpleName()); return false; }
    }

    private static boolean loadProfile(String raw) {
        String name = cleanProfileName(raw);
        if (name.isEmpty()) return false;
        Path target = PROFILE_DIR.resolve(name + ".properties");
        if (!Files.exists(target)) return false;
        Properties props = new Properties();
        try (InputStream in = Files.newInputStream(target)) {
            props.load(in);
            releaseRuntimeState(Minecraft.getInstance());
            applyProperties(props, "profile:" + name);
            runtimeSafeMode = false;
            save();
            return true;
        } catch (Exception e) { appendDiagnostic("PROFILE LOAD " + e.getClass().getSimpleName()); return false; }
    }

    private static boolean deleteProfile(String raw) {
        String name = cleanProfileName(raw);
        if (name.isEmpty()) return false;
        try { return Files.deleteIfExists(PROFILE_DIR.resolve(name + ".properties")); }
        catch (Exception e) { appendDiagnostic("PROFILE DELETE " + e.getClass().getSimpleName()); return false; }
    }

    private static String profileSummary() {
        if (!Files.isDirectory(PROFILE_DIR)) return "No Eio profiles saved";
        try (var stream = Files.list(PROFILE_DIR)) {
            List<String> names = stream.filter(path -> path.getFileName().toString().endsWith(".properties"))
                    .map(path -> path.getFileName().toString().replaceFirst("\\.properties$", ""))
                    .sorted().toList();
            return names.isEmpty() ? "No Eio profiles saved" : "Profiles: " + String.join(", ", names);
        } catch (Exception e) { return "Could not list Eio profiles"; }
    }

    private static int currentCps() {
        long cutoff = System.currentTimeMillis() - 1000L;
        while (!ATTACK_TIMES.isEmpty() && ATTACK_TIMES.peekFirst() < cutoff) ATTACK_TIMES.removeFirst();
        return ATTACK_TIMES.size();
    }

    private static void tick(Minecraft mc) {
        while (guiKey != null && guiKey.consumeClick()) {
            if (!guiOpen) openGui();
        }
        for (Mod m : MODS) {
            if (m.bind != null) while (m.bind.consumeClick()) {
                if (!guiOpen && mc.player != null) toggle(m);
            }
        }
        if (mc.player == null) {
            if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
            if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
            if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
            if (attackForced) { mc.options.keyAttack.setDown(false); attackForced = false; }
            followTarget = null;
            combatTarget = null;
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
            chunkMineChunkX = Integer.MIN_VALUE;
            chunkMineChunkZ = Integer.MIN_VALUE;
            CHUNK_MINE_SKIPPED.clear();
            nukerTarget = null;
            nukerRearmTicks = 0;
            nukerAimTicks = 0;
            NUKER_SKIPPED.clear();
            resetAreaRuntime();
            clickAccumulator = 0.0;
            auraCooldown = 0;
            triggerCooldown = 0;
            toolSaverWarned = false;
            flyForced = false;
            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            COMPAT.clearPause();
            return;
        }

        Mod walk = find("AutoWalk");
        Mod sprint = find("Sprint");
        Mod follow = find("Follow");
        Mod fly = find("Fly");
        Mod safe = find("SafeWalk");
        Mod autoJump = find("Auto Jump");
        Mod autoSwim = find("Auto Swim");
        Mod speed = find("Speed");
        Mod respawn = find("Auto Respawn");
        Mod creative = find("Creative Assist");
        Mod lowHealth = find("Low Health Alert");
        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod targetLock = find("Target Lock");
        Mod trigger = find("Trigger Bot");
        Mod combatSprint = find("Combat Sprint");
        Mod autoMine = find("Auto Mine");
        Mod tunnelMiner = find("Tunnel Miner");
        Mod chunkMiner = find("Chunk Miner");
        Mod nuker = find("Nuker");
        Mod areaMiner = find("Area Miner");
        Mod bright = find("Fullbright");
        Mod compatibility = find("Compatibility Guard");
        boolean correctionPause = compatibility != null && compatibility.enabled
                && compatibility.bool("Pause On Correction").value && COMPAT.paused();

        areaMoveRequested = !correctionPause && areaMiner.enabled && areaMiner.bool("Auto Move").value
                && updateAreaNavigation(mc, areaMiner);
        boolean areaOwnsMovement = areaMiner.enabled && areaMiner.bool("Auto Move").value;
        boolean shouldForceForward = areaMoveRequested || (!areaOwnsMovement && !correctionPause && walk.enabled);
        if (!areaOwnsMovement && !correctionPause && follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (!areaOwnsMovement && !correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;
        if (shouldForceForward) {
            mc.options.keyUp.setDown(true);
            forwardForced = true;
        } else if (forwardForced) {
            mc.options.keyUp.setDown(false);
            forwardForced = false;
        }

        if (!correctionPause && sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            boolean hungerOk = !sprint.bool("Hunger Check").value || mc.player.getFoodData().getFoodLevel() > 6;
            if (hungerOk) mc.player.setSprinting(true);
        }
        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }
        if (areaMoveRequested && areaMiner.bool("Sprint").value && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }
        if (!correctionPause && speed.enabled) applyMovementSpeed(mc, speed);
        boolean movingForSafeWalk = mc.options.keyUp.isDown() || mc.options.keyDown.isDown()
                || mc.options.keyLeft.isDown() || mc.options.keyRight.isDown();
        boolean shouldForceSneak = !correctionPause && safe.enabled && movingForSafeWalk && mc.player.onGround();
        if (shouldForceSneak) {
            mc.options.keyShift.setDown(true);
            sneakForced = true;
        } else if (sneakForced) {
            mc.options.keyShift.setDown(false);
            sneakForced = false;
        }

        if (!correctionPause && fly.enabled) {
            var a = mc.player.getAbilities();
            if (!flyForced) {
                flyPrevMayfly = a.mayfly;
                flyPrevFlying = a.flying;
                flyPrevSpeed = a.getFlyingSpeed();
                flyForced = true;
            }
            a.mayfly = true;
            a.flying = true;
            a.setFlyingSpeed((float) fly.num("Speed").value);
        } else if (flyForced) {
            restoreFly(mc);
        }
        if (respawn.enabled && mc.player.isDeadOrDying()) mc.player.respawn();

        if (!correctionPause && creative.enabled && !fly.enabled && creative.bool("Auto Fly").value) {
            var abilities = mc.player.getAbilities();
            if (abilities.mayfly) {
                if (!creativeAssistSpeedForced) creativeAssistPrevSpeed = abilities.getFlyingSpeed();
                abilities.flying = true;
                abilities.setFlyingSpeed((float) creative.num("Flight Speed").value);
                creativeAssistSpeedForced = true;
                creativeAssistWarned = false;
            } else if (!creativeAssistWarned) {
                notifyMessage("CREATIVE ASSIST: SERVER FLIGHT PERMISSION REQUIRED", 0xFFFFB36B, 3200L);
                creativeAssistWarned = true;
            }
        } else {
            creativeAssistWarned = false;
            if (creativeAssistSpeedForced && !fly.enabled) {
                mc.player.getAbilities().setFlyingSpeed(creativeAssistPrevSpeed);
                creativeAssistSpeedForced = false;
            }
        }

        if (lowHealth.enabled) {
            if (lowHealthCooldown > 0) lowHealthCooldown--;
            double threshold = lowHealth.num("Threshold").value;
            if (mc.player.getHealth() <= threshold) {
                if (!lowHealthAlerted || lowHealthCooldown <= 0) {
                    notifyMessage(String.format(Locale.ROOT, "LOW HEALTH %.1f", mc.player.getHealth()), 0xFFFF7D7D,
                            (long) (find("Notifications").num("Seconds").value * 1000.0));
                    lowHealthAlerted = true;
                    lowHealthCooldown = Math.max(40, (int) Math.round(lowHealth.num("Cooldown").value * 20.0));
                }
            } else if (mc.player.getHealth() >= threshold + 2.0) {
                lowHealthAlerted = false;
            }
        } else {
            lowHealthAlerted = false;
            lowHealthCooldown = 0;
        }

        if (!correctionPause && targetLock.enabled) {
            double lockRange = targetLock.num("Range").value;
            double lockFov = targetLock.num("FOV").value;
            if (!validConfiguredTarget(mc, targetLock, combatTarget, lockRange, lockFov)) {
                combatTarget = nearestTarget(mc, targetLock, lockRange, lockFov);
            }
            if (combatTarget != null && targetLock.bool("Face Target").value) faceEntity(mc.player, combatTarget);
        } else combatTarget = null;

        if (!correctionPause && trigger.enabled) {
            if (triggerCooldown > 0) triggerCooldown--;
            if (triggerCooldown <= 0 && mc.hitResult instanceof EntityHitResult hit) {
                Entity t = hit.getEntity();
                double r = trigger.num("Range").value;
                if (validModuleTarget(trigger, t) && mc.player.distanceToSqr(t) <= r * r) {
                    attack(mc, t);
                    triggerCooldown = Math.max(1, (int) Math.round(trigger.num("Delay").value));
                }
            }
        } else triggerCooldown = 0;

        if (!correctionPause && combatSprint.enabled && !mc.player.horizontalCollision) {
            Entity t = nearestTarget(mc, combatSprint, combatSprint.num("Range").value, combatSprint.num("FOV").value);
            if (t != null) mc.player.setSprinting(true);
        }

        boolean miningAllowed = !correctionPause && miningToolSafe(mc);
        boolean shouldForceAttack = false;
        if (miningAllowed) {
            if (areaMiner.enabled) {
                if (!areaConfigured(areaMiner)) {
                    areaMineTarget = null;
                } else {
                    if (areaMineTarget != null && mc.level.getBlockState(areaMineTarget).isAir()) {
                        areaMinedThisPass++;
                        stopAreaDestroy(mc);
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                        areaMineWorkTicks = 0;
                        areaMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                    } else if (areaMineTarget != null && !validAreaMineTarget(mc, areaMiner, areaMineTarget)) {
                        stopAreaDestroy(mc);
                        AREA_MINE_SKIPPED.add(areaMineTarget.immutable());
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                        areaMineWorkTicks = 0;
                        areaMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                    }
                    if (areaMineRearmTicks > 0) {
                        areaMineRearmTicks--;
                    } else {
                        if (areaMineTarget == null) {
                            areaMineTarget = findAreaMineTarget(mc, areaMiner);
                            areaMineAimTicks = 0;
                            areaMineWorkTicks = 0;
                            if (areaMineTarget == null && !AREA_MINE_SKIPPED.isEmpty()) {
                                AREA_MINE_SKIPPED.clear();
                                areaMineTarget = findAreaMineTarget(mc, areaMiner);
                            }
                        }
                        if (areaMineTarget != null) {
                            if (areaMiner.bool("Face Block").value) faceBlock(mc.player, areaMineTarget);
                            areaMineAimTicks++;
                            areaMineWorkTicks++;
                            // The old implementation only held the key at END_CLIENT_TICK. That can miss
                            // Minecraft's destroy-start window even though navigation still works. Drive
                            // the normal MultiPlayerGameMode start/continue path instead.
                            if (areaMineAimTicks >= 2) continueAreaDestroy(mc, areaMineTarget);
                            if (areaMineWorkTicks >= Math.max(40, (int) Math.round(areaMiner.num("Mine Timeout").value))) {
                                stopAreaDestroy(mc);
                                AREA_MINE_SKIPPED.add(areaMineTarget.immutable());
                                areaMineTarget = null;
                                areaMineAimTicks = 0;
                                areaMineWorkTicks = 0;
                                areaMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                            }
                        }
                    }
                }
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
            } else if (nuker.enabled) {
                if (nukerTarget != null && mc.level.getBlockState(nukerTarget).isAir()) {
                    nukerTarget = null;
                    nukerAimTicks = 0;
                    nukerRearmTicks = Math.max(1, (int) Math.round(nuker.num("Retarget Delay").value));
                } else if (nukerTarget != null && !validNukerTarget(mc, nuker, nukerTarget)) {
                    NUKER_SKIPPED.add(nukerTarget.immutable());
                    nukerTarget = null;
                    nukerAimTicks = 0;
                    nukerRearmTicks = Math.max(1, (int) Math.round(nuker.num("Retarget Delay").value));
                }

                if (nukerRearmTicks > 0) {
                    nukerRearmTicks--;
                } else {
                    if (nukerTarget == null) {
                        nukerTarget = findNukerTarget(mc, nuker);
                        nukerAimTicks = 0;
                        if (nukerTarget == null && !NUKER_SKIPPED.isEmpty()) {
                            NUKER_SKIPPED.clear();
                            nukerTarget = findNukerTarget(mc, nuker);
                        }
                    }
                    if (nukerTarget != null) {
                        if (nuker.bool("Face Block").value) faceBlock(mc.player, nukerTarget);
                        boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(nukerTarget);
                        if (aimed) {
                            shouldForceAttack = true;
                            nukerAimTicks = 0;
                        } else if (++nukerAimTicks >= Math.max(4, (int) Math.round(nuker.num("Aim Timeout").value))) {
                            NUKER_SKIPPED.add(nukerTarget.immutable());
                            nukerTarget = null;
                            nukerAimTicks = 0;
                            nukerRearmTicks = 1;
                        }
                    }
                }

                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
            } else if (chunkMiner.enabled) {
                int cx = mc.player.blockPosition().getX() >> 4;
                int cz = mc.player.blockPosition().getZ() >> 4;
                if (cx != chunkMineChunkX || cz != chunkMineChunkZ) {
                    chunkMineChunkX = cx;
                    chunkMineChunkZ = cz;
                    chunkMineTarget = null;
                    chunkMineRearmTicks = 0;
                    chunkMineAimTicks = 0;
                    CHUNK_MINE_SKIPPED.clear();
                }

                if (chunkMineTarget != null && mc.level.getBlockState(chunkMineTarget).isAir()) {
                    chunkMineTarget = null;
                    chunkMineAimTicks = 0;
                    CHUNK_MINE_SKIPPED.clear();
                    chunkMineRearmTicks = Math.max(1, (int) Math.round(chunkMiner.num("Retarget Delay").value));
                } else if (chunkMineTarget != null && !validChunkMineTarget(mc, chunkMiner, chunkMineTarget)) {
                    CHUNK_MINE_SKIPPED.add(chunkMineTarget.immutable());
                    chunkMineTarget = null;
                    chunkMineAimTicks = 0;
                    chunkMineRearmTicks = Math.max(1, (int) Math.round(chunkMiner.num("Retarget Delay").value));
                }

                if (chunkMineRearmTicks > 0) {
                    chunkMineRearmTicks--;
                } else {
                    if (chunkMineTarget == null) {
                        chunkMineTarget = findChunkMineTarget(mc, chunkMiner);
                        chunkMineAimTicks = 0;
                        if (chunkMineTarget == null && !CHUNK_MINE_SKIPPED.isEmpty()) {
                            CHUNK_MINE_SKIPPED.clear();
                            chunkMineTarget = findChunkMineTarget(mc, chunkMiner);
                        }
                    }
                    if (chunkMineTarget != null) {
                        if (chunkMiner.bool("Face Block").value) faceBlock(mc.player, chunkMineTarget);
                        boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(chunkMineTarget);
                        if (aimed) {
                            shouldForceAttack = true;
                            chunkMineAimTicks = 0;
                        } else if (++chunkMineAimTicks >= Math.max(4, (int) Math.round(chunkMiner.num("Aim Timeout").value))) {
                            CHUNK_MINE_SKIPPED.add(chunkMineTarget.immutable());
                            chunkMineTarget = null;
                            chunkMineAimTicks = 0;
                            chunkMineRearmTicks = 1;
                        }
                    }
                }
            } else {
                resetAreaRuntime();
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                NUKER_SKIPPED.clear();
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;
                chunkMineChunkZ = Integer.MIN_VALUE;
                CHUNK_MINE_SKIPPED.clear();

                if (autoMine.enabled && (!autoMine.bool("Stop In GUI").value || !guiOpen)
                        && mc.hitResult instanceof BlockHitResult) shouldForceAttack = true;
                if (tunnelMiner.enabled && (!tunnelMiner.bool("Pause On Entity").value || !(mc.hitResult instanceof EntityHitResult))) {
                    shouldForceAttack = true;
                }
            }
        } else {
            stopAreaDestroy(mc);
            areaMineTarget = null;
            areaMineRearmTicks = 0;
            areaMineAimTicks = 0;
            areaMineWorkTicks = 0;
            areaMoveRequested = false;
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
            nukerTarget = null;
            nukerRearmTicks = 0;
            nukerAimTicks = 0;
        }

        if (shouldForceAttack) {
            mc.options.keyAttack.setDown(true);
            attackForced = true;
        } else if (attackForced) {
            mc.options.keyAttack.setDown(false);
            attackForced = false;
        }

        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();
        if (!correctionPause && clicker.enabled && clickAllowed) {
            double cps = Math.max(1.0, Math.min(20.0, clicker.num("CPS").value));
            clickAccumulator = Math.min(2.0, clickAccumulator + cps / 20.0);
            if (clickAccumulator >= 1.0) {
                clickAccumulator -= 1.0;
                Entity clickTarget = null;
                if (mc.hitResult instanceof EntityHitResult hit && validClickTarget(mc, clicker, hit.getEntity())) {
                    clickTarget = hit.getEntity();
                }
                if (clickTarget == null) {
                    clickTarget = nearestTarget(mc, clicker, clicker.num("Range").value, clicker.num("FOV").value);
                }
                if (clickTarget != null) attack(mc, clickTarget);
            }
        } else clickAccumulator = 0.0;

        if (!correctionPause && aura.enabled) {
            if (auraCooldown-- <= 0) {
                auraCooldown = Math.max(1, (int) Math.round(aura.num("Delay").value));
                Entity target = nearestTarget(mc, aura, aura.num("Range").value, aura.num("FOV").value);
                if (target != null) attack(mc, target);
            }
        } else auraCooldown = 0;

        boolean shouldForceJump = !correctionPause && ((autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater())
                || (areaMoveRequested && areaMiner.bool("Auto Jump").value && mc.player.horizontalCollision && mc.player.onGround()));
        if (shouldForceJump) {
            mc.options.keyJump.setDown(true);
            jumpForced = true;
        } else if (jumpForced) {
            mc.options.keyJump.setDown(false);
            jumpForced = false;
        }

        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);
        COMPAT.tick();
    }

    private static void applyMovementSpeed(Minecraft mc, Mod speed) {
        if (mc.player == null || mc.player.getAbilities().flying) return;
        if (speed.bool("Ground Only").value && !mc.player.onGround()) return;

        double forward = 0.0;
        double strafe = 0.0;
        if (mc.options.keyUp.isDown()) forward += 1.0;
        if (mc.options.keyDown.isDown()) forward -= 1.0;
        if (mc.options.keyRight.isDown()) strafe += 1.0;
        if (mc.options.keyLeft.isDown()) strafe -= 1.0;
        double length = Math.sqrt(forward * forward + strafe * strafe);
        if (length < 0.001) return;
        forward /= length;
        strafe /= length;

        double yaw = Math.toRadians(mc.player.getYRot());
        double sin = Math.sin(yaw);
        double cos = Math.cos(yaw);
        double worldX = -forward * sin + strafe * cos;
        double worldZ = forward * cos + strafe * sin;
        double basePerTick = mc.player.isSprinting() ? 0.2805 : 0.21585;
        double horizontal = basePerTick * speed.num("Multiplier").value;
        var velocity = mc.player.getDeltaMovement();
        mc.player.setDeltaMovement(worldX * horizontal, velocity.y, worldZ * horizontal);
    }

    private static boolean validConfiguredTarget(Minecraft mc, Mod selector, Entity target, double range, double fov) {
        if (mc.player == null || target == null || !validModuleTarget(selector, target)) return false;
        if (mc.player.distanceToSqr(target) > range * range) return false;
        return fov >= 359.9 || angleFromView(mc.player, target) <= fov / 2.0;
    }

    private static void faceEntity(Player player, Entity target) {
        double dx = target.getX() - player.getX();
        double dz = target.getZ() - player.getZ();
        double dy = target.getY() + target.getBbHeight() * 0.5 - player.getEyeY();
        double horizontal = Math.sqrt(dx * dx + dz * dz);
        player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        player.setXRot((float) (-Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)))));
    }

    private static boolean miningToolSafe(Minecraft mc) {
        Mod saver = find("Tool Saver");
        if (saver == null || !saver.enabled || mc.player == null) {
            toolSaverWarned = false;
            return true;
        }
        ItemStack held = mc.player.getInventory().getSelectedItem();
        if (held.isEmpty() || !held.isDamageableItem()) {
            toolSaverWarned = false;
            return true;
        }
        int remaining = held.getMaxDamage() - held.getDamageValue();
        int reserve = (int) Math.round(saver.num("Remaining").value);
        if (remaining <= reserve) {
            if (!toolSaverWarned && saver.bool("Notify").value) {
                notifyMessage("TOOL SAVER: MINING PAUSED (" + remaining + " LEFT)", 0xFFFFC875, 2600L);
            }
            toolSaverWarned = true;
            return false;
        }
        toolSaverWarned = false;
        return true;
    }

    private static AreaRegion areaRegion(Mod area) {
        if (area == null) return null;
        PointSetting a = area.point("Corner A"), b = area.point("Corner B");
        return AreaRegion.from(a.value, b.value, (int) Math.round(area.num("Depth").value));
    }

    private static boolean areaConfigured(Mod area) {
        AreaRegion region = areaRegion(area);
        return region != null && region.supportedSize();
    }

    private static String areaStatus(Mod area) {
        AreaRegion region = areaRegion(area);
        if (region == null) return "Area Miner: set Corner A and Corner B";
        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;
        return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | lane " + Math.min(region.navigationCells(), areaNavIndex + 1) + "/" + region.navigationCells());
    }

    private static void resetAreaRuntime() {
        areaMineTarget = null;
        areaDestroyTarget = null;
        areaDestroyStarted = false;
        areaMineWorkTicks = 0;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        areaNavIndex = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        areaMoveRequested = false;
        areaComplete = false;
        AREA_MINE_SKIPPED.clear();
    }

    private static Direction areaMiningFace(Player player, BlockPos pos) {
        double dx = player.getX() - (pos.getX() + 0.5);
        double dy = player.getEyeY() - (pos.getY() + 0.5);
        double dz = player.getZ() - (pos.getZ() + 0.5);
        double ax = Math.abs(dx), ay = Math.abs(dy), az = Math.abs(dz);
        if (ay >= ax && ay >= az) return dy >= 0.0 ? Direction.UP : Direction.DOWN;
        if (ax >= az) return dx >= 0.0 ? Direction.EAST : Direction.WEST;
        return dz >= 0.0 ? Direction.SOUTH : Direction.NORTH;
    }

    private static void continueAreaDestroy(Minecraft mc, BlockPos pos) {
        if (mc.player == null || mc.gameMode == null || pos == null || !withinVanillaBlockRange(mc, pos)) return;
        Direction face = areaMiningFace(mc.player, pos);
        if (mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(pos)) face = hit.getDirection();
        if (!areaDestroyStarted || areaDestroyTarget == null || !areaDestroyTarget.equals(pos)) {
            if (areaDestroyStarted) mc.gameMode.stopDestroyBlock();
            areaDestroyTarget = pos.immutable();
            areaDestroyStarted = mc.gameMode.startDestroyBlock(areaDestroyTarget, face);
        }
        if (areaDestroyStarted) {
            mc.gameMode.continueDestroyBlock(areaDestroyTarget, face);
        }
    }

    private static void stopAreaDestroy(Minecraft mc) {
        if (areaDestroyStarted && mc != null && mc.gameMode != null) mc.gameMode.stopDestroyBlock();
        areaDestroyStarted = false;
        areaDestroyTarget = null;
    }

    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || !region.contains(pos)) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }

    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize()) return null;
        int cells = region.navigationCells();
        if (cells <= 0 || areaNavIndex < 0 || areaNavIndex >= cells) return null;

        // AREA2: only clear the column for the current serpentine lane cell. This deliberately
        // avoids the old radius scan that could turn around and mine unrelated blocks behind/aside.
        BlockPos lane = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
        if (lane == null) return null;
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int y = region.topY; y >= region.bottomY; y--) {
            BlockPos pos = new BlockPos(lane.getX(), y, lane.getZ());
            if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;
            double px = pos.getX() + 0.5 - mc.player.getX();
            double py = pos.getY() + 0.5 - mc.player.getEyeY();
            double pz = pos.getZ() + 0.5 - mc.player.getZ();
            double d = px * px + py * py + pz * pz;
            if (d < bestSq) { bestSq = d; best = pos.immutable(); }
        }
        return best;
    }

    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        if (areaMineTarget != null || areaMineRearmTicks > 0) { areaMoveTicks = 0; return false; }
        AreaRegion region = areaRegion(area);
        if (region == null) return false;

        double px = mc.player.getX(), pz = mc.player.getZ();
        boolean outside = px < region.minX + 0.15 || px > region.maxX + 0.85
                || pz < region.minZ + 0.15 || pz > region.maxZ + 0.85;
        double goalX, goalZ;
        if (outside) {
            // Enter at the nearest point in the configured zone before taking ownership of the lane path.
            goalX = region.clampX(px) + 0.5;
            goalZ = region.clampZ(pz) + 0.5;
        } else {
            int cells = region.navigationCells();
            if (cells <= 0) return false;
            if (areaNavIndex >= cells) {
                if (areaMinedThisPass <= 0) {
                    areaComplete = true;
                    area.enabled = false;
                    save();
                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
                    appendDiagnostic("AREA_MINER complete " + region.summary());
                    return false;
                }
                // One serpentine pass exposed/mined more blocks. Start the same lanes again so
                // deeper configured blocks become reachable without ever radius-mining around the player.
                areaNavIndex = 0;
                areaMinedThisPass = 0;
                AREA_MINE_SKIPPED.clear();
            }

            BlockPos nav = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
            if (nav == null) return false;

            // Mine the current lane column before walking into it. At row boundaries navigationCell()
            // supplies the adjacent shift cell followed by the reverse lane, producing the U-turn pattern.
            BlockPos forwardBlock = findAreaMineTarget(mc, area);
            if (forwardBlock != null) {
                areaMineTarget = forwardBlock;
                areaMineAimTicks = 0;
                areaMoveTicks = 0;
                return false;
            }

            goalX = nav.getX() + 0.5;
            goalZ = nav.getZ() + 0.5;
        }

        double dx = goalX - px, dz = goalZ - pz;
        double distance = Math.sqrt(dx * dx + dz * dz);
        if (!outside && distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        if (++areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
            if (!outside) areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.45;
    }

    private static void faceHorizontal(Player player, double x, double z) {
        double dx = x - player.getX();
        double dz = z - player.getZ();
        if (dx * dx + dz * dz > 1.0E-6) player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
    }

    private static boolean validChunkMineTarget(Minecraft mc, Mod chunk, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        BlockPos origin = mc.player.blockPosition();
        if ((pos.getX() >> 4) != (origin.getX() >> 4) || (pos.getZ() >> 4) != (origin.getZ() >> 4)) return false;
        int vertical = (int) Math.round(chunk.num("Vertical").value);
        if (Math.abs(pos.getY() - origin.getY()) > vertical) return false;
        if (chunk.bool("Avoid Below").value && pos.getY() < (int) Math.floor(mc.player.getY())) return false;
        double dx = pos.getX() + 0.5 - mc.player.getX();
        double dy = pos.getY() + 0.5 - mc.player.getY();
        double dz = pos.getZ() + 0.5 - mc.player.getZ();
        double r = chunk.num("Radius").value;
        if (dx * dx + dy * dy + dz * dz > r * r) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        if (chunk.bool("Exposed Only").value && !isExposedBlock(mc, pos)) return false;
        return true;
    }

    private static boolean isExposedBlock(Minecraft mc, BlockPos pos) {
        for (Direction direction : Direction.values()) {
            if (mc.level.getBlockState(pos.relative(direction)).isAir()) return true;
        }
        return false;
    }

    private static BlockPos findChunkMineTarget(Minecraft mc, Mod chunk) {
        if (mc.player == null || mc.level == null) return null;
        BlockPos origin = mc.player.blockPosition();
        int radius = (int) Math.ceil(chunk.num("Radius").value);
        int vertical = (int) Math.round(chunk.num("Vertical").value);
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int dy = -vertical; dy <= vertical; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (CHUNK_MINE_SKIPPED.contains(pos)) continue;
                    if (!validChunkMineTarget(mc, chunk, pos)) continue;
                    double px = pos.getX() + 0.5 - mc.player.getX();
                    double py = pos.getY() + 0.5 - mc.player.getY();
                    double pz = pos.getZ() + 0.5 - mc.player.getZ();
                    double d = px * px + py * py + pz * pz;
                    if (d < bestSq) { bestSq = d; best = pos.immutable(); }
                }
            }
        }
        return best;
    }

    private static boolean validNukerTarget(Minecraft mc, Mod nuker, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        BlockPos origin = mc.player.blockPosition();
        int vertical = (int) Math.round(nuker.num("Vertical").value);
        if (Math.abs(pos.getY() - origin.getY()) > vertical) return false;
        if (nuker.bool("Avoid Below").value && pos.getY() < (int) Math.floor(mc.player.getY())) return false;
        double dx = pos.getX() + 0.5 - mc.player.getX();
        double dy = pos.getY() + 0.5 - mc.player.getY();
        double dz = pos.getZ() + 0.5 - mc.player.getZ();
        double r = nuker.num("Radius").value;
        if (dx * dx + dy * dy + dz * dz > r * r) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        if (nuker.bool("Exposed Only").value && !isExposedBlock(mc, pos)) return false;
        return true;
    }

    private static BlockPos findNukerTarget(Minecraft mc, Mod nuker) {
        if (mc.player == null || mc.level == null) return null;
        BlockPos origin = mc.player.blockPosition();
        int radius = (int) Math.ceil(nuker.num("Radius").value);
        int vertical = (int) Math.round(nuker.num("Vertical").value);
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int dy = -vertical; dy <= vertical; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (NUKER_SKIPPED.contains(pos)) continue;
                    if (!validNukerTarget(mc, nuker, pos)) continue;
                    double px = pos.getX() + 0.5 - mc.player.getX();
                    double py = pos.getY() + 0.5 - mc.player.getY();
                    double pz = pos.getZ() + 0.5 - mc.player.getZ();
                    double d = px * px + py * py + pz * pz;
                    if (d < bestSq) { bestSq = d; best = pos.immutable(); }
                }
            }
        }
        return best;
    }

    private static void faceBlock(Player player, BlockPos pos) {
        double dx = pos.getX() + 0.5 - player.getX();
        double dz = pos.getZ() + 0.5 - player.getZ();
        double dy = pos.getY() + 0.5 - player.getEyeY();
        double horizontal = Math.sqrt(dx * dx + dz * dz);
        player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        player.setXRot((float) (-Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)))));
    }

    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {
        if (mc.player == null || !validModuleTarget(clicker, target)) return false;
        if (angleFromView(mc.player, target) > clicker.num("FOV").value / 2.0) return false;
        double r = clicker.num("Range").value;
        return mc.player.distanceToSqr(target) <= r * r;
    }

    private static boolean validModuleTarget(Mod selector, Entity target) {
        if (selector == null || !(target instanceof LivingEntity) || !target.isAlive()) return false;
        if (target instanceof Player) return selector.bool("Players").value && (!target.isInvisible() || selector.bool("Invisible").value);
        if (!selector.bool("Mobs").value) return false;
        if (target.isInvisible() && !selector.bool("Invisible").value) return false;
        MobListSetting filter = selector.mobList("Target Selection");
        String id = target.getType().getDescriptionId();
        filter.touch(id);
        return filter.allows(id);
    }

    private static Entity nearestTarget(Minecraft mc, Mod selector, double range, double fov) {
        if (mc.player == null || mc.level == null) return null;
        AABB box = mc.player.getBoundingBox().inflate(range);
        Entity best = null;
        double bestSq = range * range;
        for (Entity e : mc.level.getEntities(mc.player, box, e -> e instanceof LivingEntity && e.isAlive())) {
            if (!validModuleTarget(selector, e)) continue;
            if (fov < 359.9 && angleFromView(mc.player, e) > fov / 2.0) continue;
            double d = mc.player.distanceToSqr(e);
            if (d <= bestSq) { bestSq = d; best = e; }
        }
        return best;
    }

    private static boolean compatibilityRangeGuardEnabled() {
        Mod guard = find("Compatibility Guard");
        return guard != null && guard.enabled && guard.bool("Vanilla Ranges").value;
    }

    private static boolean withinVanillaBlockRange(Minecraft mc, BlockPos pos) {
        return !compatibilityRangeGuardEnabled() || (mc.player != null && mc.player.isWithinBlockInteractionRange(pos, 0.0));
    }

    private static boolean withinVanillaEntityRange(Minecraft mc, Entity target) {
        return !compatibilityRangeGuardEnabled() || (mc.player != null && mc.player.isWithinEntityInteractionRange(target, 0.0));
    }

    private static void attack(Minecraft mc, Entity target) {
        if (mc.player == null || mc.gameMode == null || target == null || !target.isAlive()) return;
        if (!withinVanillaEntityRange(mc, target)) {
            suppressedOutOfRangeAttacks++;
            return;
        }
        mc.gameMode.attack(mc.player, target);
        mc.player.swing(InteractionHand.MAIN_HAND, mc.player.getMainHandItem().getAttackAnimation(), true);
        long now = System.currentTimeMillis();
        ATTACK_TIMES.addLast(now);
        while (!ATTACK_TIMES.isEmpty() && ATTACK_TIMES.peekFirst() < now - 1000L) ATTACK_TIMES.removeFirst();
    }

    private static Entity nearestTarget(Minecraft mc, double range, double fov, boolean players, boolean mobs, boolean invisible) {
        if (mc.player == null || mc.level == null) return null;
        AABB box = mc.player.getBoundingBox().inflate(range);
        Entity best = null;
        double bestSq = range * range;
        for (Entity e : mc.level.getEntities(mc.player, box, e -> e instanceof LivingEntity && e.isAlive())) {
            if (e instanceof Player && !players) continue;
            if (!(e instanceof Player) && !mobs) continue;
            if (e.isInvisible() && !invisible) continue;
            if (fov < 359.9 && angleFromView(mc.player, e) > fov / 2.0) continue;
            double d = mc.player.distanceToSqr(e);
            if (d <= bestSq) { bestSq = d; best = e; }
        }
        return best;
    }

    private static double angleFromView(Player player, Entity e) {
        double dx = e.getX() - player.getX();
        double dz = e.getZ() - player.getZ();
        double targetYaw = Math.toDegrees(Math.atan2(dz, dx)) - 90.0;
        double delta = targetYaw - player.getYRot();
        while (delta > 180) delta -= 360;
        while (delta < -180) delta += 360;
        return Math.abs(delta);
    }

    private static boolean validFollowTarget(Minecraft mc, Mod follow, Entity target) {
        if (mc.player == null || !(target instanceof LivingEntity) || !target.isAlive() || target == mc.player) return false;
        if (target instanceof Player) return follow.bool("Players").value;
        if (!follow.bool("Mobs").value) return false;
        MobListSetting filter = follow.mobList("Mob Selection");
        String id = target.getType().getDescriptionId();
        filter.touch(id);
        return filter.allows(id);
    }

    private static Entity nearestFollowTarget(Minecraft mc, Mod follow, double range) {
        if (mc.player == null || mc.level == null) return null;
        AABB box = mc.player.getBoundingBox().inflate(range);
        Entity best = null;
        double bestSq = range * range;
        for (Entity e : mc.level.getEntities(mc.player, box, e -> e instanceof LivingEntity && e.isAlive())) {
            if (!validFollowTarget(mc, follow, e)) continue;
            double d = mc.player.distanceToSqr(e);
            if (d <= bestSq) { bestSq = d; best = e; }
        }
        return best;
    }

    private static boolean runFollow(Minecraft mc, Mod follow) {
        if (mc.player == null) return false;
        double search = follow.num("Search Range").value;
        if (followTarget == null || !validFollowTarget(mc, follow, followTarget)
                || mc.player.distanceToSqr(followTarget) > search * search) {
            followTarget = nearestFollowTarget(mc, follow, search);
        }
        if (followTarget == null) return false;
        double dist = Math.sqrt(mc.player.distanceToSqr(followTarget));
        if (follow.bool("Face Target").value) {
            double dx = followTarget.getX() - mc.player.getX();
            double dz = followTarget.getZ() - mc.player.getZ();
            mc.player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        }
        boolean advance = dist > follow.num("Distance").value;
        if (advance && follow.bool("Sprint").value) mc.player.setSprinting(true);
        return advance;
    }


    private static void maintainFullbright(Minecraft mc) {
        if (mc.player == null) return;
        MobEffectInstance current = mc.player.getEffect(MobEffects.NIGHT_VISION);
        if (current != null && current != fullbrightInjected) { fullbrightInjected = null; return; }
        if (current == null || current.endsWithin(200)) {
            fullbrightInjected = new MobEffectInstance(MobEffects.NIGHT_VISION, 1200, 0, false, false, false);
            mc.player.addEffect(fullbrightInjected);
        }
    }

    private static void clearFullbright(Minecraft mc) {
        if (mc.player != null && fullbrightInjected != null) {
            MobEffectInstance current = mc.player.getEffect(MobEffects.NIGHT_VISION);
            if (current == fullbrightInjected) mc.player.removeEffect(MobEffects.NIGHT_VISION);
        }
        fullbrightInjected = null;
    }

    private static void toggle(Mod m) {
        m.enabled = !m.enabled;
        Minecraft mc = Minecraft.getInstance();
        if (!m.enabled && mc.player != null) {
            if ((m.name.equals("AutoWalk") || m.name.equals("Follow") || m.name.equals("Tunnel Miner") || m.name.equals("Area Miner"))
                    && !find("AutoWalk").enabled && !find("Follow").enabled
                    && !find("Tunnel Miner").enabled && !find("Area Miner").enabled && forwardForced) {
                mc.options.keyUp.setDown(false);
                forwardForced = false;
            }
            if (m.name.equals("SafeWalk") && sneakForced) {
                mc.options.keyShift.setDown(false);
                sneakForced = false;
            }
            if (m.name.equals("Fly") && flyForced) restoreFly(mc);
            if (m.name.equals("Low Health Alert")) {
                lowHealthAlerted = false;
                lowHealthCooldown = 0;
            }
            if (m.name.equals("Fullbright")) clearFullbright(mc);
            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner") || m.name.equals("Nuker") || m.name.equals("Area Miner"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && !find("Nuker").enabled
                    && !find("Area Miner").enabled && attackForced) {
                mc.options.keyAttack.setDown(false);
                attackForced = false;
                chunkMineTarget = null;
            }
            if (m.name.equals("Chunk Miner")) {
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;
                chunkMineChunkZ = Integer.MIN_VALUE;
                CHUNK_MINE_SKIPPED.clear();
            }
            if (m.name.equals("Nuker")) {
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                NUKER_SKIPPED.clear();
            }
            if (m.name.equals("Area Miner")) resetAreaRuntime();
            if (m.name.equals("Target Lock")) combatTarget = null;
        }
        notifyToggle(m);
        save();
    }

    private static void restoreFly(Minecraft mc) {
        if (mc.player != null && flyForced) {
            var a = mc.player.getAbilities();
            a.mayfly = flyPrevMayfly;
            a.flying = flyPrevFlying;
            a.setFlyingSpeed(flyPrevSpeed);
            mc.player.onUpdateAbilities();
        }
        flyForced = false;
    }

    private static void releaseCorrectionSensitiveState(Minecraft mc) {
        if (mc == null) return;
        if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
        if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
        if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
        if (attackForced) { mc.options.keyAttack.setDown(false); attackForced = false; }
        if (flyForced) restoreFly(mc);
        if (creativeAssistSpeedForced && mc.player != null) {
            mc.player.getAbilities().setFlyingSpeed(creativeAssistPrevSpeed);
            creativeAssistSpeedForced = false;
        }
        followTarget = null;
        combatTarget = null;
        chunkMineTarget = null;
        chunkMineRearmTicks = 0;
        chunkMineAimTicks = 0;
        CHUNK_MINE_SKIPPED.clear();
        nukerTarget = null;
        nukerRearmTicks = 0;
        nukerAimTicks = 0;
        NUKER_SKIPPED.clear();
        resetAreaRuntime();
        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
    }

    private static void releaseRuntimeState(Minecraft mc) {
        if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
        if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
        if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
        if (attackForced) { mc.options.keyAttack.setDown(false); attackForced = false; }
        if (flyForced) restoreFly(mc);
        clearFullbright(mc);
        followTarget = null;
        combatTarget = null;
        chunkMineTarget = null;
        chunkMineRearmTicks = 0;
        chunkMineAimTicks = 0;
        chunkMineChunkX = Integer.MIN_VALUE;
        chunkMineChunkZ = Integer.MIN_VALUE;
        CHUNK_MINE_SKIPPED.clear();
        nukerTarget = null;
        nukerRearmTicks = 0;
        nukerAimTicks = 0;
        NUKER_SKIPPED.clear();
        resetAreaRuntime();
        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
        toolSaverWarned = false;
        lowHealthAlerted = false;
        lowHealthCooldown = 0;
        creativeAssistWarned = false;
        if (creativeAssistSpeedForced && mc.player != null && !find("Fly").enabled) mc.player.getAbilities().setFlyingSpeed(creativeAssistPrevSpeed);
        creativeAssistSpeedForced = false;
    }

    private static void panic(Minecraft mc) {
        releaseRuntimeState(mc);
        for (Mod m : MODS) m.enabled = false;
        save();
        notifyMessage("PANIC: ALL MODULES OFF", 0xFFFFB36B, 2500L);
    }

    private static void resetModuleSettings(Mod m) {
        for (Setting setting : m.settings) {
            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
            else if (setting instanceof MobListSetting ml) ml.reset();
            else if (setting instanceof PointSetting point) point.reset();
        }
    }

    private static void resetAllSettings() {
        for (Mod m : MODS) resetModuleSettings(m);
    }

    private static String validateModel() {
        Set<String> categories = Set.of("Combat", "Movement", "Player", "Render", "World", "Mining", "Misc");
        Set<String> slugs = new HashSet<>();
        int settingCount = 0;
        for (Mod m : MODS) {
            if (!categories.contains(m.category)) throw new IllegalStateException("Unknown category: " + m.category);
            if (MOD_INDEX.get(m.name.toLowerCase(Locale.ROOT)) != m) throw new IllegalStateException("Module index mismatch: " + m.name);
            if (!slugs.add(slug(m.name))) throw new IllegalStateException("Duplicate key slug: " + slug(m.name));
            Set<String> names = new HashSet<>();
            for (Setting setting : m.settings) {
                settingCount++;
                if (!names.add(setting.name.toLowerCase(Locale.ROOT))) throw new IllegalStateException("Duplicate setting: " + m.name + "/" + setting.name);
                if (setting instanceof NumSetting n && (n.step <= 0.0 || n.min > n.max || n.defaultValue < n.min || n.defaultValue > n.max))
                    throw new IllegalStateException("Invalid numeric setting: " + m.name + "/" + n.name);
            }
        }
        return "model=OK modules=" + MODS.size() + " settings=" + settingCount + " categories=" + categories.size();
    }

    private static int enabledCount() {
        int count = 0;
        for (Mod m : MODS) if (m.enabled) count++;
        return count;
    }

    private static int notificationColor = 0xFF66D69B;

    private static void notifyMessage(String text, int color, long millis) {
        notificationText = text;
        notificationColor = color;
        notificationUntil = System.currentTimeMillis() + Math.max(250L, millis);
    }

    private static void notifyToggle(Mod m) {
        Mod n = find("Notifications");
        if (n == null || !n.enabled) return;
        if (!m.enabled && !n.bool("Show Disable").value) return;
        notifyMessage(m.name + (m.enabled ? " enabled" : " disabled"), m.enabled ? 0xFF66D69B : 0xFFCC6B6B,
                (long) (n.num("Seconds").value * 1000.0));
    }

    private static void hud(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        int y = 5;
        g.text(mc.font, "Eio", 5, y, 0xFF8CCDF2, true); y += 11;
        if (find("Session Info").enabled) {
            String info = "v" + VERSION + " / MC 26.3";
            if (find("Session Info").bool("Build ID").value) info += " / " + BUILD_ID;
            g.text(mc.font, info, 5, y, 0xFF8795A3, false); y += 10;
        }
        if (find("Coordinates").enabled) {
            int decimals = (int) Math.round(find("Coordinates").num("Decimals").value);
            String format = "XYZ %." + decimals + "f  %." + decimals + "f  %." + decimals + "f";
            g.text(mc.font, String.format(Locale.ROOT, format, mc.player.getX(), mc.player.getY(), mc.player.getZ()), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("FPS").enabled) { g.text(mc.font, "FPS " + mc.getFps(), 5, y, 0xFFD9E0E6, true); y += 11; }
        if (find("Health").enabled) {
            g.text(mc.font, String.format(Locale.ROOT, "Health %.1f / %.1f", mc.player.getHealth(), mc.player.getMaxHealth()), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Speed").enabled && find("Speed").bool("Show HUD").value) {
            var velocity = mc.player.getDeltaMovement();
            double bps = Math.sqrt(velocity.x * velocity.x + velocity.z * velocity.z) * 20.0;
            g.text(mc.font, String.format(Locale.ROOT, "Speed %.2f b/s  x%.1f", bps, find("Speed").num("Multiplier").value), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Facing").enabled) {
            int dir = Math.floorMod((int) Math.floor((mc.player.getYRot() + 45.0f) / 90.0f), 4);
            String facing = switch (dir) { case 0 -> "South"; case 1 -> "West"; case 2 -> "North"; default -> "East"; };
            g.text(mc.font, "Facing " + facing, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Rotation").enabled) {
            g.text(mc.font, String.format(Locale.ROOT, "Yaw %.1f  Pitch %.1f", mc.player.getYRot(), mc.player.getXRot()), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Memory").enabled) {
            Runtime runtime = Runtime.getRuntime();
            long usedMb = (runtime.totalMemory() - runtime.freeMemory()) / (1024L * 1024L);
            long maxMb = runtime.maxMemory() / (1024L * 1024L);
            g.text(mc.font, "Memory " + usedMb + "/" + maxMb + " MB", 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Clock").enabled) {
            g.text(mc.font, "Time " + LocalTime.now().format(CLOCK_FORMATTER), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("CPS").enabled) {
            g.text(mc.font, "CPS " + currentCps(), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Keystrokes").enabled) {
            String keys = (mc.options.keyUp.isDown() ? "W" : "-") + " " + (mc.options.keyLeft.isDown() ? "A" : "-")
                    + " " + (mc.options.keyDown.isDown() ? "S" : "-") + " " + (mc.options.keyRight.isDown() ? "D" : "-")
                    + (mc.options.keyJump.isDown() ? " JUMP" : "") + (mc.player.isSprinting() ? " SPRINT" : "");
            g.text(mc.font, "Keys " + keys, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Held Item").enabled) {
            ItemStack held = mc.player.getInventory().getSelectedItem();
            if (!held.isEmpty()) {
                String text = "Held " + held.getHoverName().getString() + " x" + held.getCount();
                g.text(mc.font, text, 5, y, 0xFFD9E0E6, true); y += 11;
            }
        }
        if (find("Session Timer").enabled) {
            long seconds = Math.max(0L, (System.nanoTime() - sessionStartedNanos) / 1_000_000_000L);
            long hours = seconds / 3600L, minutes = (seconds % 3600L) / 60L, secs = seconds % 60L;
            g.text(mc.font, String.format(Locale.ROOT, "Session %02d:%02d:%02d", hours, minutes, secs), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Chunk Info").enabled) {
            int cx = Math.floorDiv((int) Math.floor(mc.player.getX()), 16), cz = Math.floorDiv((int) Math.floor(mc.player.getZ()), 16);
            g.text(mc.font, "Chunk " + cx + ", " + cz, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Inventory Info").enabled) {
            var items = mc.player.getInventory().getNonEquipmentItems(); int used = 0;
            for (ItemStack stack : items) if (!stack.isEmpty()) used++;
            g.text(mc.font, "Inventory " + used + "/" + items.size() + " slots", 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Durability HUD").enabled) {
            ItemStack held = mc.player.getInventory().getSelectedItem();
            if (!held.isEmpty() && held.isDamageableItem()) {
                int remaining = held.getMaxDamage() - held.getDamageValue();
                g.text(mc.font, held.getHoverName().getString() + " " + remaining + "/" + held.getMaxDamage(), 5, y, 0xFFD9E0E6, true); y += 11;
            }
        }
        if (find("Waypoints").enabled && !WAYPOINTS.isEmpty()) {
            Waypoint nearest = null; double best = Double.MAX_VALUE;
            for (Waypoint wp : WAYPOINTS.values()) {
                double dx = wp.x - mc.player.getX(), dy = wp.y - mc.player.getY(), dz = wp.z - mc.player.getZ();
                double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
                if (d < best) { best = d; nearest = wp; }
            }
            if (nearest != null) { g.text(mc.font, "WP " + nearest.name + " " + Math.round(best) + "m", 5, y, 0xFF9DD9FF, true); y += 11; }
        }
        if (find("Mining HUD").enabled) {
            Mod miningHud = find("Mining HUD");
            if (miningHud.bool("Target").value) {
                BlockPos miningPos = areaMineTarget != null ? areaMineTarget : (nukerTarget != null ? nukerTarget : chunkMineTarget);
                if (miningPos == null && mc.hitResult instanceof BlockHitResult hit) miningPos = hit.getBlockPos();
                if (miningPos != null) {
                    g.text(mc.font, "Mining " + miningPos.getX() + " " + miningPos.getY() + " " + miningPos.getZ(), 5, y, 0xFFE9C67B, true);
                    y += 11;
                }
            }
            if (find("Area Miner").enabled || areaComplete) {
                g.text(mc.font, areaStatus(find("Area Miner")), 5, y, 0xFF8FDCC0, true);
                y += 11;
            }
            if (miningHud.bool("Tool").value) {
                ItemStack held = mc.player.getInventory().getSelectedItem();
                if (!held.isEmpty() && held.isDamageableItem()) {
                    int remaining = held.getMaxDamage() - held.getDamageValue();
                    g.text(mc.font, "Tool " + remaining + "/" + held.getMaxDamage(), 5, y, 0xFFE9C67B, true);
                    y += 11;
                }
            }
        }

        if (find("Reach").enabled) {
            Mod reach = find("Reach");
            Entity rt = nearestTarget(mc, reach, reach.num("Range").value, 360.0);
            if (rt != null) {
                double rd = Math.sqrt(mc.player.distanceToSqr(rt));
                g.text(mc.font, "Reach " + rt.getDisplayName().getString() + " " + String.format(Locale.ROOT, "%.1fm", rd), 5, y, 0xFF9DD9FF, true);
                y += 11;
            }
        }
        if (find("Target HUD").enabled) {
            Entity t = combatTarget != null ? combatTarget : followTarget;
            if (t == null && mc.hitResult instanceof EntityHitResult hit) t = hit.getEntity();
            if (t != null && t.isAlive()) {
                String text = "Target " + t.getDisplayName().getString() + " " + String.format(Locale.ROOT, "%.1fm", Math.sqrt(mc.player.distanceToSqr(t)));
                g.text(mc.font, text, 5, y, 0xFFF0C987, true); y += 11;
            }
        }
        if (find("Active Modules").enabled) {
            int max = (int) Math.round(find("Active Modules").num("Max").value);
            int shown = 0, total = 0;
            for (Mod m : MODS) if (m.enabled && !m.name.equals("Active Modules")) {
                total++;
                if (shown < max) { g.text(mc.font, m.name, 5, y, 0xFF91BDD8, true); y += 10; shown++; }
            }
            if (total > shown) { g.text(mc.font, "+" + (total - shown) + " more", 5, y, 0xFF657887, false); y += 10; }
        }
        if (!notificationText.isEmpty() && System.currentTimeMillis() < notificationUntil) {
            int ny = Math.max(18, y + 2), boxW = mc.font.width(notificationText) + 12;
            g.fill(3, ny - 3, 3 + boxW, ny + 11, 0xB8121720);
            g.text(mc.font, notificationText, 9, ny, notificationColor, true);
        }
    }

    private static void drawBrand(GuiGraphicsExtractor g, int width) {
        String text = "MADE BY EIO";
        int scale = 2;
        int pixelWidth = 0;
        for (int i = 0; i < text.length(); i++) pixelWidth += (text.charAt(i) == ' ' ? 2 : 4) * scale;
        ClickGui.drawRainbowBlockBrand(g, width - pixelWidth - 8, 8, scale);
    }

    private static Mod find(String name) { return name == null ? null : MOD_INDEX.get(name.toLowerCase(Locale.ROOT)); }
    private static String summary() { StringJoiner j = new StringJoiner(" | "); for (Mod m : MODS) j.add(m.name + ":" + (m.enabled ? "ON" : "OFF")); return j.toString(); }
    private static String waypointSummary() {
        if (WAYPOINTS.isEmpty()) return "No waypoints saved";
        StringJoiner j = new StringJoiner(" | "); for (Waypoint w : WAYPOINTS.values()) j.add(w.name + " @ " + Math.round(w.x) + "," + Math.round(w.y) + "," + Math.round(w.z)); return j.toString();
    }

    private static void load() {
        Properties props = new Properties();
        boolean loaded = false;
        String source = "defaults";
        if (Files.exists(CONFIG)) {
            try (InputStream in = Files.newInputStream(CONFIG)) { props.load(in); loaded = true; source = "primary"; } catch (Exception ignored) {}
        }
        if (!loaded && Files.exists(CONFIG_BACKUP)) {
            props.clear();
            try (InputStream in = Files.newInputStream(CONFIG_BACKUP)) { props.load(in); loaded = true; source = "backup"; } catch (Exception ignored) { props.clear(); }
        }
        applyProperties(props, source);
    }

    private static void save() {
        Properties p = snapshotProperties();
        try {
            Files.createDirectories(CONFIG.getParent());
            if (Files.exists(CONFIG)) {
                try { Files.copy(CONFIG, CONFIG_BACKUP, StandardCopyOption.REPLACE_EXISTING); } catch (Exception ignored) {}
            }
            Path tmp = CONFIG.resolveSibling(CONFIG.getFileName().toString() + ".tmp");
            try (OutputStream out = Files.newOutputStream(tmp, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
                p.store(out, "Eio Client " + VERSION);
            }
            try {
                Files.move(tmp, CONFIG, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException ex) {
                Files.move(tmp, CONFIG, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (Exception ignored) {}
    }

    private static abstract class Setting {
        final String name, description;
        Setting(String name, String description) { this.name = name; this.description = description; }
    }
    private static final class BoolSetting extends Setting {
        final boolean defaultValue;
        boolean value;
        BoolSetting(String name, boolean value, String description) { super(name, description); this.defaultValue = value; this.value = value; }
    }
    private static final class NumSetting extends Setting {
        final double defaultValue;
        double value, min, max, step;
        NumSetting(String name, double value, double min, double max, double step, String description) { super(name, description); this.defaultValue = value; this.min = min; this.max = max; this.step = step; set(value); }
        void set(double v) { v = Math.max(min, Math.min(max, v)); value = Math.round(v / step) * step; value = Math.max(min, Math.min(max, value)); }
        String display() { return step < 0.1 ? String.format(Locale.ROOT, "%.2f", value) : String.format(Locale.ROOT, "%.1f", value); }
    }
    private static final class PointSetting extends Setting {
        BlockPos value;
        PointSetting(String name, String description) { super(name, description); }
        void set(BlockPos pos) { value = pos == null ? null : pos.immutable(); }
        void reset() { value = null; }
        String csv() { return value == null ? "" : value.getX() + "," + value.getY() + "," + value.getZ(); }
        void load(String raw) {
            reset();
            if (raw == null || raw.isBlank()) return;
            try {
                String[] p = raw.split(",");
                if (p.length == 3) value = new BlockPos(Integer.parseInt(p[0].trim()), Integer.parseInt(p[1].trim()), Integer.parseInt(p[2].trim()));
            } catch (Exception ignored) {}
        }
        String display() { return value == null ? "SET HERE" : value.getX() + " " + value.getY() + " " + value.getZ(); }
    }

    private static final class MobListSetting extends Setting {
        final LinkedHashMap<String, Boolean> values = new LinkedHashMap<>();
        MobListSetting(String name, String[] ids, String description) {
            super(name, description);
            for (String id : ids) values.put(id, true);
        }
        void touch(String id) { if (id != null && !id.isBlank()) values.putIfAbsent(id, true); }
        boolean allows(String id) { touch(id); return values.getOrDefault(id, true); }
        void set(String id, boolean value) { touch(id); values.put(id, value); }
        void setAll(boolean value) { for (String id : new ArrayList<>(values.keySet())) values.put(id, value); }
        void reset() { setAll(true); }
        List<String> ids() { List<String> ids = new ArrayList<>(values.keySet()); ids.sort(Comparator.comparing(MobListSetting::label)); return ids; }
        int enabledCount() { int n = 0; for (boolean value : values.values()) if (value) n++; return n; }
        String disabledCsv() { StringJoiner j = new StringJoiner(","); for (var e : values.entrySet()) if (!e.getValue()) j.add(e.getKey()); return j.toString(); }
        void loadDisabledCsv(String csv) {
            reset();
            if (csv == null || csv.isBlank()) return;
            for (String raw : csv.split(",")) { String id = raw.trim(); if (!id.isEmpty()) set(id, false); }
        }
        static String label(String id) {
            String raw = id == null ? "Unknown" : id.substring(id.lastIndexOf('.') + 1).replace('_', ' ');
            StringBuilder out = new StringBuilder();
            boolean cap = true;
            for (int i = 0; i < raw.length(); i++) {
                char c = raw.charAt(i);
                out.append(cap ? Character.toUpperCase(c) : c);
                cap = c == ' ';
            }
            return out.toString();
        }
    }
    private static final class Mod {
        final String name, category, description; final int defaultKey; boolean enabled; KeyMapping bind; final List<Setting> settings = new ArrayList<>();
        Mod(String name, String category, String description, int defaultKey) { this.name = name; this.category = category; this.description = description; this.defaultKey = defaultKey; }
        Mod bool(String name, boolean value) { return bool(name, value, name); }
        Mod bool(String name, boolean value, String description) { settings.add(new BoolSetting(name, value, description)); return this; }
        Mod num(String name, double value, double min, double max, double step) { return num(name, value, min, max, step, name); }
        Mod num(String name, double value, double min, double max, double step, String description) { settings.add(new NumSetting(name, value, min, max, step, description)); return this; }
        Mod mobList(String name, String[] ids, String description) { settings.add(new MobListSetting(name, ids, description)); return this; }
        Mod point(String name, String description) { settings.add(new PointSetting(name, description)); return this; }
        BoolSetting bool(String name) { for (Setting s : settings) if (s instanceof BoolSetting b && b.name.equals(name)) return b; throw new IllegalArgumentException(name); }
        NumSetting num(String name) { for (Setting s : settings) if (s instanceof NumSetting n && n.name.equals(name)) return n; throw new IllegalArgumentException(name); }
        MobListSetting mobList(String name) { for (Setting s : settings) if (s instanceof MobListSetting ml && ml.name.equals(name)) return ml; throw new IllegalArgumentException(name); }
        PointSetting point(String name) { for (Setting s : settings) if (s instanceof PointSetting point && point.name.equals(name)) return point; throw new IllegalArgumentException(name); }
    }
    private static final class Waypoint { final String name; final double x, y, z; Waypoint(String name, double x, double y, double z) { this.name = name; this.x = x; this.y = y; this.z = z; } }

    public static final class ClickGui extends Screen {
        private static final String[] CATEGORIES = {"Active", "Combat", "Movement", "Player", "Render", "World", "Mining", "Misc"};
        private static final int MOB_PAGE_SIZE = 8;
        private String selectedCategory = "Combat";
        private Mod selectedMod;
        private int mobPage;
        private int settingsScroll;
        private int modulesScroll;
        private int categoriesScroll;
        private static final int MOB_SELECTOR_HEIGHT = 130;

        ClickGui() { super(Component.literal("Eio Client")); }
        @Override public boolean isPauseScreen() { return false; }
        @Override public void added() {
            super.added();
            guiOpen = true;
            if (selectedMod == null) selectedMod = firstInCategory(selectedCategory);
            settingsScroll = 0;
            modulesScroll = 0;
            categoriesScroll = 0;
        }
        @Override public void removed() { guiOpen = false; save(); super.removed(); }
        @Override public void onClose() { guiOpen = false; save(); super.onClose(); }

        private boolean categoryMatches(Mod m, String category) {
            return "Active".equals(category) ? m.enabled : m.category.equals(category);
        }

        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (categoryMatches(m, category)) return m;
            return null;
        }

        private int panelW() { return Math.max(450, Math.min(760, width - 16)); }
        private int panelH() { return Math.max(280, Math.min(430, height - 16)); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }
        private int categoryCount(String category) { int count = 0; for (Mod m : MODS) if (categoryMatches(m, category)) count++; return count; }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int accent = categoryColor(selectedCategory);
            String help = selectedMod == null ? "Choose a module" : selectedMod.description;

            g.fill(0, 0, width, height, 0x04000000);
            g.fill(x + 5, y + 7, x + bw + 5, y + bh + 7, 0x12000000);
            g.fill(x, y, x + bw, y + bh, 0x4A090E14);
            g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x12131A22);
            g.fill(x + 2, y + 2, x + bw - 2, y + 3, 0x26384A58);
            g.fill(x, y, x + bw, y + 31, 0x700C131B);
            g.fill(x, y + 30, x + bw, y + 31, 0x3A405260);
            g.fill(x + 3, y + 30, x + Math.min(110, Math.max(60, bw / 5)), y + 32, accent);
            g.fill(x, y, x + 3, y + bh, accent);

            g.text(font, "EIO", x + 13, y + 10, 0xFFF4F8FB, true);
            g.text(font, "CLIENT  /  " + VERSION, x + 39, y + 10, 0xFF7C8B97, false);
            String status = runtimeSafeMode ? "SAFE MODE" : enabledCount() + " ACTIVE";
            int statusW = font.width(status) + 12;
            g.fill(x + bw - statusW - 61, y + 7, x + bw - 61, y + 24, runtimeSafeMode ? 0x665D3424 : 0x6030483C);
            g.text(font, status, x + bw - statusW - 55, y + 12, runtimeSafeMode ? 0xFFFFAD7D : 0xFF79DCAA, false);
            g.text(font, "RSHIFT", x + bw - 49, y + 11, 0xFF667682, false);

            int bodyY = y + 39;
            int footerY = y + bh - 25;
            int railX = x + 10, railW = 122;
            int modsX = railX + railW + 8, modsW = Math.min(210, Math.max(160, bw / 3 - 22));
            int detailX = modsX + modsW + 8;
            int detailW = x + bw - 10 - detailX;

            g.fill(railX, bodyY, railX + railW, footerY - 6, 0x2410171F);
            g.fill(modsX, bodyY, modsX + modsW, footerY - 6, 0x1C10171F);
            g.fill(detailX, bodyY, detailX + detailW, footerY - 6, 0x2210171F);

            g.text(font, "NAVIGATION", railX + 8, bodyY + 8, 0xFF738592, false);
            int categoryTop = bodyY + 23;
            int categoryBottom = footerY - 9;
            int categoryViewport = Math.max(1, categoryBottom - categoryTop);
            int categoryMax = Math.max(0, CATEGORIES.length * 28 - categoryViewport);
            categoriesScroll = clampScroll(categoriesScroll, categoryMax);
            int cy = categoryTop - categoriesScroll;
            for (String category : CATEGORIES) {
                boolean active = category.equals(selectedCategory);
                boolean visible = cy + 25 > categoryTop && cy < categoryBottom;
                boolean fullyVisible = cy >= categoryTop && cy + 25 <= categoryBottom;
                boolean hover = fullyVisible && in(mx, my, railX + 5, cy, railW - 10, 25);
                if (visible) {
                    int drawTop = Math.max(cy, categoryTop);
                    int drawBottom = Math.min(cy + 25, categoryBottom);
                    if (hover || active) g.fill(railX + 5, drawTop, railX + railW - 5, drawBottom,
                            active ? 0x761B2731 : 0x3818232C);
                    if (active) g.fill(railX + 5, Math.max(drawTop, cy + 5), railX + 8, Math.min(drawBottom, cy + 20), accent);
                    if (fullyVisible) {
                        g.text(font, shortCat(category), railX + 14, cy + 8, active ? 0xFFF4F8FA : 0xFFABB7BF, active);
                        String count = Integer.toString(categoryCount(category));
                        int badgeX = railX + railW - font.width(count) - 15;
                        g.fill(badgeX - 4, cy + 5, railX + railW - 7, cy + 20, active ? 0x402B3A44 : 0x261A232A);
                        g.text(font, count, badgeX, cy + 8, active ? accent : 0xFF667681, false);
                        if (hover) help = "Open " + category + " modules";
                    }
                }
                cy += 28;
            }
            drawScrollBar(g, railX + railW - 3, categoryTop, categoryViewport, categoriesScroll, categoryMax, accent);

            g.text(font, selectedCategory.toUpperCase(Locale.ROOT), modsX + 8, bodyY + 8, accent, true);
            int moduleTop = bodyY + 23;
            int moduleBottom = footerY - 9;
            int moduleMax = Math.max(0, categoryCount(selectedCategory) * 22 - Math.max(1, moduleBottom - moduleTop));
            modulesScroll = clampScroll(modulesScroll, moduleMax);
            int myCard = moduleTop - modulesScroll;
            for (Mod m : MODS) if (categoryMatches(m, selectedCategory)) {
                boolean visible = myCard + 20 > moduleTop && myCard < moduleBottom;
                if (visible) {
                    boolean selected = m == selectedMod;
                    boolean hover = in(mx, my, modsX + 5, Math.max(myCard, moduleTop), modsW - 10,
                            Math.max(0, Math.min(myCard + 20, moduleBottom) - Math.max(myCard, moduleTop)));
                    int drawTop = Math.max(myCard, moduleTop);
                    int drawBottom = Math.min(myCard + 20, moduleBottom);
                    if (drawBottom > drawTop) {
                        g.fill(modsX + 5, drawTop, modsX + modsW - 5, drawBottom,
                                selected ? 0x741D2A34 : (hover ? 0x4518232C : 0x1C11161C));
                        if (selected) g.fill(modsX + 5, drawTop, modsX + 7, drawBottom, accent);
                    }
                    if (myCard >= moduleTop && myCard + 20 <= moduleBottom) {
                        g.fill(modsX + 12, myCard + 8, modsX + 16, myCard + 12, m.enabled ? 0xFF6FE0A5 : 0xFF55636D);
                        g.text(font, trim(m.name, Math.max(10, (modsW - 49) / 6)), modsX + 22, myCard + 6,
                                selected ? 0xFFF2F6F8 : 0xFFC2CCD3, false);
                        String state = m.enabled ? "ON" : "";
                        if (!state.isEmpty()) g.text(font, state, modsX + modsW - font.width(state) - 11, myCard + 6, 0xFF77DDA9, false);
                        if (hover) help = m.description;
                    }
                }
                myCard += 22;
            }
            drawScrollBar(g, modsX + modsW - 3, moduleTop, Math.max(1, moduleBottom - moduleTop), modulesScroll, moduleMax, accent);

            if (selectedMod == null) {
                g.centeredText(font, "Select a module", detailX + detailW / 2, bodyY + 18, 0xFF83919C);
            } else {
                int sx = detailX + 9, sw = detailW - 18, sy = bodyY + 8;
                g.text(font, selectedMod.name, sx, sy, 0xFFF4F7F9, true);
                String category = selectedMod.category.toUpperCase(Locale.ROOT);
                g.text(font, category, sx, sy + 12, accent, false);

                int toggleW = 42, toggleX = sx + sw - toggleW;
                boolean toggleHover = in(mx, my, toggleX, sy, toggleW, 19);
                g.fill(toggleX, sy, toggleX + toggleW, sy + 19, selectedMod.enabled ? 0xB12F7558 : (toggleHover ? 0x78505A62 : 0x60414A51));
                int knobX = selectedMod.enabled ? toggleX + 25 : toggleX + 4;
                g.fill(knobX, sy + 4, knobX + 13, sy + 15, selectedMod.enabled ? 0xFFF2FFF8 : 0xFFB9C2C8);
                if (toggleHover) help = "Toggle " + selectedMod.name;
                sy += 31;

                boolean bindHover = in(mx, my, sx, sy, sw, 22);
                g.fill(sx, sy, sx + sw, sy + 22, bindHover ? 0x681A2731 : 0x35121920);
                g.text(font, "KEYBIND", sx + 7, sy + 7, 0xFF80909C, false);
                String key = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "NONE" : selectedMod.bind.getTranslatedKeyMessage().getString();
                String keyText = "[ " + trim(key, 13) + " ]";
                g.text(font, keyText, sx + sw - font.width(keyText) - 7, sy + 7, 0xFF9EDCFA, false);
                if (bindHover) help = "Open Minecraft Controls to change this keybind";
                sy += 30;

                g.text(font, "SETTINGS", sx, sy, 0xFF647581, false);
                sy += 12;
                int settingsTop = sy;
                int settingsBottom = footerY - 9;
                int settingsViewport = Math.max(1, settingsBottom - settingsTop);
                int settingsMax = Math.max(0, settingsContentHeight(selectedMod) - settingsViewport);
                settingsScroll = clampScroll(settingsScroll, settingsMax);
                sy -= settingsScroll;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        help = renderMobSelector(g, mx, my, sx, sy, sw - 5, ml, help, accent, settingsTop, settingsBottom);
                        sy += MOB_SELECTOR_HEIGHT;
                        continue;
                    }
                    boolean visible = sy + 22 > settingsTop && sy < settingsBottom;
                    if (visible) {
                        int drawTop = Math.max(sy, settingsTop);
                        int drawBottom = Math.min(sy + 22, settingsBottom);
                        boolean fullyVisible = sy >= settingsTop && sy + 22 <= settingsBottom;
                        boolean hover = fullyVisible && in(mx, my, sx, sy, sw - 5, 22);
                        if (drawBottom > drawTop) g.fill(sx, drawTop, sx + sw - 5, drawBottom, hover ? 0x471A252E : 0x1E11161C);
                        if (fullyVisible && setting instanceof BoolSetting b) {
                            g.text(font, trim(b.name, 18), sx + 7, sy + 7, 0xFFD4DCE2, false);
                            int tx = sx + sw - 39;
                            g.fill(tx, sy + 5, tx + 28, sy + 17, b.value ? 0x93347459 : 0x50424A51);
                            int kx = b.value ? tx + 17 : tx + 3;
                            g.fill(kx, sy + 7, kx + 8, sy + 15, b.value ? 0xFFF1FFF7 : 0xFFB9C1C7);
                        } else if (fullyVisible && setting instanceof PointSetting point) {
                            g.text(font, trim(point.name, 13), sx + 7, sy + 7, 0xFFD4DCE2, false);
                            String value = point.display();
                            int buttonW = point.value == null ? 58 : Math.min(116, font.width(value) + 12);
                            int bx = sx + sw - buttonW - 10;
                            g.fill(bx, sy + 4, sx + sw - 10, sy + 18, hover ? 0x6A31566B : 0x46304758);
                            g.centeredText(font, trim(value, 18), bx + buttonW / 2, sy + 7, point.value == null ? 0xFF9EDCFA : 0xFFB9E8D1);
                        } else if (fullyVisible && setting instanceof NumSetting n) {
                            double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                            g.text(font, trim(n.name, 15), sx + 7, sy + 5, 0xFFD4DCE2, false);
                            String value = n.display() + (Math.abs(n.value - n.defaultValue) > 1.0E-9 ? "*" : "");
                            g.text(font, value, sx + sw - font.width(value) - 12, sy + 5, 0xFF9DDCFA, false);
                            g.fill(sx + 7, sy + 17, sx + sw - 12, sy + 19, 0x45505E68);
                            g.fill(sx + 7, sy + 17, sx + 7 + (int) ((sw - 19) * ratio), sy + 19, accent);
                        }
                        if (hover) help = setting.description;
                    }
                    sy += 24;
                }
                drawScrollBar(g, sx + sw - 3, settingsTop, settingsViewport, settingsScroll, settingsMax, accent);
            }

            g.fill(x + 10, footerY, x + bw - 10, y + bh - 7, 0x2810171F);
            String footer = trim(help, Math.max(40, (bw - 40) / 6));
            g.text(font, footer, x + 15, footerY + 6, 0xFF7D8B96, false);
            String hint = "WHEEL panel scroll  •  LMB select/set  •  RMB reset/clear";
            g.text(font, hint, x + bw - font.width(hint) - 15, footerY + 6, 0xFF566671, false);

            super.extractRenderState(g, mx, my, delta);
        }

        private String renderMobSelector(GuiGraphicsExtractor g, int mx, int my, int sx, int sy, int sw,
                                         MobListSetting ml, String help, int accent, int clipTop, int clipBottom) {
            List<String> ids = ml.ids();
            int pages = Math.max(1, (ids.size() + MOB_PAGE_SIZE - 1) / MOB_PAGE_SIZE);
            mobPage = Math.max(0, Math.min(mobPage, pages - 1));
            int boxTop = Math.max(sy, clipTop), boxBottom = Math.min(sy + MOB_SELECTOR_HEIGHT, clipBottom);
            if (boxBottom > boxTop) g.fill(sx, boxTop, sx + sw, boxBottom, 0x24111820);
            if (sy >= clipTop && sy + 18 <= clipBottom) {
                g.fill(sx, sy, sx + sw, sy + 1, accent);
                g.text(font, "MOB FILTER", sx + 7, sy + 7, 0xFFE4EAF0, true);
                String count = ml.enabledCount() + "/" + ids.size();
                g.text(font, count, sx + sw - font.width(count) - 7, sy + 7, 0xFF82DDB0, false);
            }

            int actionY = sy + 19;
            int allX = sx + 7, noneX = allX + 39;
            boolean actionsVisible = actionY >= clipTop && actionY + 15 <= clipBottom;
            boolean allHover = actionsVisible && in(mx, my, allX, actionY, 34, 15);
            boolean noneHover = actionsVisible && in(mx, my, noneX, actionY, 42, 15);
            if (actionsVisible) {
                g.fill(allX, actionY, allX + 34, actionY + 15, allHover ? 0x62508365 : 0x39304E3E);
                g.fill(noneX, actionY, noneX + 42, actionY + 15, noneHover ? 0x62744949 : 0x394B3232);
                g.centeredText(font, "ALL", allX + 17, actionY + 5, 0xFFBFEBD4);
                g.centeredText(font, "NONE", noneX + 21, actionY + 5, 0xFFF0B8B8);
                if (allHover) help = "Allow every listed mob type";
                if (noneHover) help = "Block every listed mob type";
            }

            String page = (mobPage + 1) + "/" + pages;
            int pageX = sx + sw - 71;
            if (actionsVisible) {
                g.fill(pageX, actionY, pageX + 18, actionY + 15, 0x39303B44);
                g.fill(pageX + 53, actionY, pageX + 71, actionY + 15, 0x39303B44);
                g.centeredText(font, "<", pageX + 9, actionY + 5, 0xFFB8C7D1);
                g.centeredText(font, ">", pageX + 62, actionY + 5, 0xFFB8C7D1);
                g.centeredText(font, page, pageX + 35, actionY + 5, 0xFF71818D);
            }

            int listY = sy + 39;
            int gap = 5;
            int cellW = (sw - 14 - gap) / 2;
            int start = mobPage * MOB_PAGE_SIZE;
            for (int i = 0; i < MOB_PAGE_SIZE; i++) {
                int idx = start + i;
                if (idx >= ids.size()) break;
                String id = ids.get(idx);
                int col = i % 2, row = i / 2;
                int cx = sx + 7 + col * (cellW + gap);
                int cy = listY + row * 22;
                boolean on = ml.allows(id);
                boolean visible = cy >= clipTop && cy + 18 <= clipBottom;
                boolean hover = visible && in(mx, my, cx, cy, cellW, 18);
                if (visible) {
                    g.fill(cx, cy, cx + cellW, cy + 18, on ? (hover ? 0x77507C64 : 0x4E315A47) : (hover ? 0x61603D3D : 0x37332228));
                    g.fill(cx + 5, cy + 7, cx + 9, cy + 11, on ? 0xFF75DDA8 : 0xFF80595D);
                    String label = MobListSetting.label(id);
                    g.text(font, trim(label, Math.max(8, (cellW - 20) / 6)), cx + 14, cy + 5, on ? 0xFFE2ECE6 : 0xFFB6A5A8, false);
                    if (hover) help = (on ? "Following allowed: " : "Following blocked: ") + label;
                }
            }
            return help;
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            boolean leftClick = e.button() == InputConstants.MOUSE_BUTTON_LEFT;
            boolean rightClick = e.button() == InputConstants.MOUSE_BUTTON_RIGHT;
            if (!leftClick && !rightClick) return super.mouseClicked(e, doubled);

            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int bodyY = y + 39;
            int footerY = y + bh - 25;
            int railX = x + 10, railW = 122;
            int modsX = railX + railW + 8, modsW = Math.min(210, Math.max(160, bw / 3 - 22));
            int detailX = modsX + modsW + 8;
            int detailW = x + bw - 10 - detailX;

            int categoryTop = bodyY + 23;
            int categoryBottom = footerY - 9;
            int categoryViewport = Math.max(1, categoryBottom - categoryTop);
            int categoryMax = Math.max(0, CATEGORIES.length * 28 - categoryViewport);
            categoriesScroll = clampScroll(categoriesScroll, categoryMax);
            int cy = categoryTop - categoriesScroll;
            for (String category : CATEGORIES) {
                if (leftClick && cy >= categoryTop && cy + 25 <= categoryBottom
                        && in(e.x(), e.y(), railX + 5, cy, railW - 10, 25)) {
                    selectedCategory = category;
                    selectedMod = firstInCategory(category);
                    mobPage = 0;
                    settingsScroll = 0;
                    modulesScroll = 0;
                    return true;
                }
                cy += 28;
            }

            int moduleTop = bodyY + 23;
            int moduleBottom = footerY - 9;
            int moduleMax = Math.max(0, categoryCount(selectedCategory) * 22 - Math.max(1, moduleBottom - moduleTop));
            modulesScroll = clampScroll(modulesScroll, moduleMax);
            int myCard = moduleTop - modulesScroll;
            for (Mod m : MODS) if (categoryMatches(m, selectedCategory)) {
                if (myCard >= moduleTop && myCard + 20 <= moduleBottom && in(e.x(), e.y(), modsX + 5, myCard, modsW - 10, 20)) {
                    if (leftClick) {
                        if (selectedMod == m) {
                            toggle(m);
                            if ("Active".equals(selectedCategory) && !m.enabled) {
                                selectedMod = firstInCategory("Active");
                                mobPage = 0;
                                settingsScroll = 0;
                            }
                        } else { selectedMod = m; mobPage = 0; settingsScroll = 0; }
                    } else {
                        resetModuleSettings(m);
                        save();
                        notifyMessage(m.name + " settings reset", 0xFF9DD9FF, 1800L);
                    }
                    return true;
                }
                myCard += 22;
            }

            if (selectedMod != null) {
                int sx = detailX + 9, sw = detailW - 18, sy = bodyY + 8;
                int toggleX = sx + sw - 42;
                if (leftClick && in(e.x(), e.y(), toggleX, sy, 42, 19)) {
                    Mod toggled = selectedMod;
                    toggle(toggled);
                    if ("Active".equals(selectedCategory) && !toggled.enabled) {
                        selectedMod = firstInCategory("Active");
                        mobPage = 0;
                        settingsScroll = 0;
                    }
                    return true;
                }
                sy += 31;
                if (leftClick && in(e.x(), e.y(), sx, sy, sw, 22)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 42;
                int settingsTop = sy;
                int settingsBottom = footerY - 9;
                int settingsMax = Math.max(0, settingsContentHeight(selectedMod) - Math.max(1, settingsBottom - settingsTop));
                settingsScroll = clampScroll(settingsScroll, settingsMax);
                sy -= settingsScroll;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        if (handleMobSelectorClick(e, leftClick, rightClick, sx, sy, sw - 5, ml, settingsTop, settingsBottom)) return true;
                        sy += MOB_SELECTOR_HEIGHT;
                        continue;
                    }
                    if (sy >= settingsTop && sy + 22 <= settingsBottom && in(e.x(), e.y(), sx, sy, sw - 5, 22)) {
                        if (rightClick) {
                            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                            else if (setting instanceof PointSetting point) { point.reset(); resetAreaRuntime(); }
                        } else if (leftClick) {
                            if (setting instanceof BoolSetting b) b.value = !b.value;
                            else if (setting instanceof PointSetting point) {
                                Minecraft mc = Minecraft.getInstance();
                                if (mc.player != null) { point.set(mc.player.blockPosition()); resetAreaRuntime(); }
                            }
                            else if (setting instanceof NumSetting n) {
                                double ratio = (e.x() - (sx + 7.0)) / Math.max(1.0, sw - 14.0);
                                ratio = Math.max(0.0, Math.min(1.0, ratio));
                                n.set(n.min + ratio * (n.max - n.min));
                            }
                        }
                        save();
                        if (selectedMod.name.equals("Follow")) followTarget = null;
                        return true;
                    }
                    sy += 24;
                }
            }
            return super.mouseClicked(e, doubled);
        }

        private boolean handleMobSelectorClick(MouseButtonEvent e, boolean leftClick, boolean rightClick,
                                               int sx, int sy, int sw, MobListSetting ml, int clipTop, int clipBottom) {
            List<String> ids = ml.ids();
            int pages = Math.max(1, (ids.size() + MOB_PAGE_SIZE - 1) / MOB_PAGE_SIZE);
            mobPage = Math.max(0, Math.min(mobPage, pages - 1));
            int actionY = sy + 19;
            int allX = sx + 7, noneX = allX + 39;
            boolean actionsVisible = actionY >= clipTop && actionY + 15 <= clipBottom;
            if (leftClick && actionsVisible && in(e.x(), e.y(), allX, actionY, 34, 15)) { ml.setAll(true); followTarget = null; save(); return true; }
            if (leftClick && actionsVisible && in(e.x(), e.y(), noneX, actionY, 42, 15)) { ml.setAll(false); followTarget = null; save(); return true; }
            int pageX = sx + sw - 71;
            if (leftClick && actionsVisible && in(e.x(), e.y(), pageX, actionY, 18, 15)) { mobPage = (mobPage - 1 + pages) % pages; return true; }
            if (leftClick && actionsVisible && in(e.x(), e.y(), pageX + 53, actionY, 18, 15)) { mobPage = (mobPage + 1) % pages; return true; }
            if (rightClick && sy >= clipTop && sy + 18 <= clipBottom && in(e.x(), e.y(), sx, sy, sw, 18)) { ml.reset(); mobPage = 0; followTarget = null; save(); return true; }

            int gap = 5, cellW = (sw - 14 - gap) / 2, listY = sy + 39;
            int start = mobPage * MOB_PAGE_SIZE;
            for (int i = 0; i < MOB_PAGE_SIZE; i++) {
                int idx = start + i;
                if (idx >= ids.size()) break;
                int col = i % 2, row = i / 2;
                int cx = sx + 7 + col * (cellW + gap), cy = listY + row * 22;
                if (leftClick && cy >= clipTop && cy + 18 <= clipBottom && in(e.x(), e.y(), cx, cy, cellW, 18)) {
                    String id = ids.get(idx);
                    ml.set(id, !ml.allows(id));
                    followTarget = null;
                    save();
                    return true;
                }
            }
            return false;
        }

        @Override
        public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int bodyY = y + 39;
            int footerY = y + bh - 25;
            int railX = x + 10, railW = 122;
            int modsX = railX + railW + 8, modsW = Math.min(210, Math.max(160, bw / 3 - 22));
            int detailX = modsX + modsW + 8;
            int detailW = x + bw - 10 - detailX;
            int step = Math.max(18, (int) Math.round(Math.abs(scrollY) * 28.0));
            if (scrollY == 0.0) return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);

            int categoryTop = bodyY + 23, categoryBottom = footerY - 9;
            if (in(mouseX, mouseY, railX, bodyY, railW, Math.max(1, footerY - 6 - bodyY))) {
                int max = Math.max(0, CATEGORIES.length * 28 - Math.max(1, categoryBottom - categoryTop));
                categoriesScroll = clampScroll(categoriesScroll + (scrollY < 0.0 ? step : -step), max);
                return true;
            }

            int moduleTop = bodyY + 23, moduleBottom = footerY - 9;
            if (in(mouseX, mouseY, modsX, bodyY, modsW, Math.max(1, footerY - 6 - bodyY))) {
                int max = Math.max(0, categoryCount(selectedCategory) * 22 - Math.max(1, moduleBottom - moduleTop));
                modulesScroll = clampScroll(modulesScroll + (scrollY < 0.0 ? step : -step), max);
                return true;
            }

            if (selectedMod != null && in(mouseX, mouseY, detailX, bodyY, detailW, Math.max(1, footerY - 6 - bodyY))) {
                int settingsTop = bodyY + 81;
                int settingsBottom = footerY - 9;
                int max = Math.max(0, settingsContentHeight(selectedMod) - Math.max(1, settingsBottom - settingsTop));
                settingsScroll = clampScroll(settingsScroll + (scrollY < 0.0 ? step : -step), max);
                return true;
            }
            return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
        }

        private int settingsContentHeight(Mod mod) {
            if (mod == null) return 0;
            int h = 0;
            for (Setting setting : mod.settings) h += setting instanceof MobListSetting ? MOB_SELECTOR_HEIGHT : 24;
            return h;
        }

        private static int clampScroll(int value, int max) {
            return Math.max(0, Math.min(Math.max(0, max), value));
        }

        private static void drawScrollBar(GuiGraphicsExtractor g, int x, int y, int height, int value, int max, int accent) {
            if (max <= 0 || height <= 8) return;
            g.fill(x, y, x + 2, y + height, 0x302D3943);
            int thumb = Math.max(18, (int) Math.round(height * (height / (double) (height + max))));
            int travel = Math.max(1, height - thumb);
            int top = y + (int) Math.round(travel * (value / (double) max));
            g.fill(x, top, x + 2, top + thumb, accent);
        }

        static void drawRainbowBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale) {
            String text = "MADE BY EIO";
            int px = x;
            long now = System.currentTimeMillis();
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                if (c == ' ') { px += 2 * scale; continue; }
                float hue = ((now % 7000L) / 7000f + i * 0.065f) % 1f;
                int rgb = 0xFF000000 | Color.HSBtoRGB(hue, 0.55f, 1.0f);
                String[] pixels = pattern(c);
                for (int row = 0; row < pixels.length; row++) for (int col = 0; col < pixels[row].length(); col++)
                    if (pixels[row].charAt(col) == '#') g.fill(px + col * scale, y + row * scale, px + (col + 1) * scale, y + (row + 1) * scale, rgb);
                px += 4 * scale;
            }
        }

        private static int categoryColor(String category) {
            return switch (category) {
                case "Active" -> 0xFF72D7A0;
                case "Combat" -> 0xFFE87979;
                case "Movement" -> 0xFF67C8F2;
                case "Player" -> 0xFF72D7A0;
                case "Render" -> 0xFFC195F1;
                case "World" -> 0xFFEEC36F;
                case "Mining" -> 0xFFE0B767;
                default -> 0xFF82B8D6;
            };
        }

        private static String[] pattern(char c) {
            return switch (c) {
                case 'M' -> new String[]{"#.#","###","###","#.#","#.#"};
                case 'A' -> new String[]{".#.","#.#","###","#.#","#.#"};
                case 'D' -> new String[]{"##.","#.#","#.#","#.#","##."};
                case 'E' -> new String[]{"###","#..","##.","#..","###"};
                case 'B' -> new String[]{"##.","#.#","##.","#.#","##."};
                case 'Y' -> new String[]{"#.#","#.#",".#.",".#.",".#."};
                case 'I' -> new String[]{"###",".#.",".#.",".#.","###"};
                case 'O' -> new String[]{".#.","#.#","#.#","#.#",".#."};
                default -> new String[]{"...","...","...","...","..."};
            };
        }

        private static String shortCat(String c) {
            return switch (c) { case "Movement" -> "Movement"; case "Testing" -> "Testing"; default -> c; };
        }
        private static boolean in(double mx, double my, int x, int y, int w, int h) { return mx >= x && mx < x + w && my >= y && my < y + h; }
        private static String trim(String text, int max) { return text.length() <= max ? text : text.substring(0, Math.max(0, max - 1)) + "…"; }
    }
}
