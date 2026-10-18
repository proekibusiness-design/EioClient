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
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;

import java.awt.Color;
import java.io.*;
import java.nio.file.*;
import java.time.Instant;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public final class EioClient implements ClientModInitializer {
    public static final String VERSION = "0.16.0";
    public static final String BUILD_ID = "EIO-016-QA1";
    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path CONFIG_BACKUP = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties.bak");
    private static final Path PROFILE_DIR = FabricLoader.getInstance().getConfigDir().resolve("eio").resolve("profiles");
    private static final Path DIAGNOSTIC_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-diagnostics.log");
    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");
    private static final List<Mod> MODS = new ArrayList<>();
    private static final Map<String, Mod> MOD_INDEX = new LinkedHashMap<>();
    private static final Map<String, Waypoint> WAYPOINTS = new LinkedHashMap<>();
    private static KeyMapping.Category keyCategory;
    private static KeyMapping guiKey;
    private static boolean guiOpen;
    private static double clickAccumulator;
    private static int auraCooldown;
    private static int testAttackCooldown;
    private static int testCycleTicks;
    private static int testJumpTicks;
    private static int testPhase;
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
    private static boolean lowHealthAlerted;
    private static int lowHealthCooldown;
    private static String configSource = "defaults";
    private static final ArrayDeque<Long> ATTACK_TIMES = new ArrayDeque<>();
    private static boolean runtimeSafeMode;
    private static int runtimeFaults;
    private static String lastRuntimeFault = "none";
    private static final long sessionStartedNanos = System.nanoTime();
    private static final DateTimeFormatter CLOCK_FORMATTER = DateTimeFormatter.ofPattern("HH:mm:ss", Locale.ROOT);

    static {
        mod("Kill Aura", "Combat", "Attacks the nearest allowed living target inside the configured range.", InputConstants.KEY_K)
                .num("Range", 4.0, 1.0, 6.0, 0.25, "Maximum distance at which a target can be selected.")
                .num("Delay", 5.0, 1.0, 20.0, 1.0, "Ticks between attack attempts. Lower values attack more often.")
                .num("FOV", 180.0, 30.0, 360.0, 15.0, "Horizontal field of view in degrees used for target selection.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible living targets.");
        mod("Auto Clicker", "Combat", "Automatically attacks a valid target near your crosshair at the configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Attack attempts per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance used when selecting a click target.")
                .num("FOV", 18.0, 5.0, 90.0, 1.0, "Maximum angle from your crosshair used when selecting a target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.");

        mod("Sprint", "Movement", "Automatically sprints while moving forward.", InputConstants.KEY_R)
                .bool("Hunger Check", true, "Only sprint when your food level is high enough.");
        mod("AutoWalk", "Movement", "Keeps moving forward until disabled.", InputConstants.KEY_G);
        mod("Follow", "Movement", "Follows a selected or nearby living entity while keeping a configurable distance.", InputConstants.KEY_H)
                .num("Search Range", 24.0, 4.0, 64.0, 1.0, "Maximum distance used when finding a follow target.")
                .num("Distance", 3.0, 1.0, 12.0, 0.5, "Distance to maintain behind the follow target.")
                .bool("Players", true, "Allow following players.")
                .bool("Mobs", true, "Allow following non-player living entities.")
                .bool("Face Target", true, "Turn your view toward the follow target.")
                .bool("Sprint", true, "Sprint while closing distance to the target.");
        mod("Fly", "Movement", "Creative-style client flight with adjustable speed.", InputConstants.KEY_F)
                .num("Speed", 0.10, 0.05, 1.00, 0.05, "Local flying speed while the module is enabled.");
        mod("SafeWalk", "Movement", "Automatically sneaks while moving on the ground to reduce edge falls.", -1);
        mod("Auto Jump", "Movement", "Jumps automatically when you run into a horizontal obstacle.", -1);
        mod("Auto Swim", "Movement", "Holds jump while you are in water so swimming upward is effortless.", -1);

        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
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
        mod("Speed", "Render", "Shows horizontal movement speed in blocks per second.", -1);
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

        mod("Test Profile", "Testing", "Runs obvious, repeatable stress patterns for private anti-cheat evaluation and writes a local test-session log.", -1)
                .num("Level", 1.0, 1.0, 5.0, 1.0, "Stress level. Higher levels use faster fixed combat timing and larger rotation snaps.")
                .num("Cycle Seconds", 4.0, 2.0, 12.0, 1.0, "How often the test profile advances or emits a test event.")
                .bool("Auto Sweep", true, "Cycle levels 1 through 5 automatically.")
                .bool("Combat", true, "Generate fixed-rate attack attempts against a nearby valid target.")
                .bool("Movement", true, "Generate an obvious jump pulse during each test cycle.")
                .bool("Rotation", true, "Generate a fixed-angle view snap during each test cycle.");

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
                                    + " bound=" + bound + " | GUI=438x254 | config=" + configSource
                                    + " | backup=" + Files.exists(CONFIG_BACKUP) + " | safeMode=" + runtimeSafeMode
                                    + " | faults=" + runtimeFaults + " | lastFault=" + lastRuntimeFault;
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
                        .then(ClientCommands.literal("test")
                                .then(ClientCommands.literal("status").executes(c -> {
                                    Mod t = find("Test Profile");
                                    c.getSource().sendFeedback(Component.literal("Test Profile " + (t.enabled ? "ON" : "OFF") + " level " + (int) t.num("Level").value));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("mark")
                                        .then(ClientCommands.argument("note", StringArgumentType.greedyString()).executes(c -> {
                                            String note = StringArgumentType.getString(c, "note");
                                            appendTestLog("MARK " + note);
                                            c.getSource().sendFeedback(Component.literal("Test marker written"));
                                            return 1;
                                        }))))
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
        try {
            hud(g, dt);
        } catch (Throwable t) {
            enterSafeMode("hud", t, Minecraft.getInstance());
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
            }
        }
        p.setProperty("_schema", "4");
        p.setProperty("_lastVersion", VERSION);
        for (Waypoint w : WAYPOINTS.values()) p.setProperty("wp." + w.name, w.x + "," + w.y + "," + w.z);
        return p;
    }

    private static void applyProperties(Properties p, String source) {
        configSource = source;
        for (Mod m : MODS) {
            String enabledDefault = m.name.equals("Notifications") ? "true" : "false";
            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, enabledDefault));
            for (Setting setting : m.settings) {
                if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                else if (setting instanceof NumSetting n) n.set(n.defaultValue);
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
            followTarget = null;
            flyForced = false;
            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            return;
        }

        Mod walk = find("AutoWalk");
        Mod sprint = find("Sprint");
        Mod follow = find("Follow");
        Mod fly = find("Fly");
        Mod safe = find("SafeWalk");
        Mod autoJump = find("Auto Jump");
        Mod autoSwim = find("Auto Swim");
        Mod respawn = find("Auto Respawn");
        Mod lowHealth = find("Low Health Alert");
        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod bright = find("Fullbright");
        Mod test = find("Test Profile");

        boolean shouldForceForward = walk.enabled;
        if (follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (shouldForceForward) {
            mc.options.keyUp.setDown(true);
            forwardForced = true;
        } else if (forwardForced) {
            mc.options.keyUp.setDown(false);
            forwardForced = false;
        }

        if (sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            boolean hungerOk = !sprint.bool("Hunger Check").value || mc.player.getFoodData().getFoodLevel() > 6;
            if (hungerOk) mc.player.setSprinting(true);
        }
        boolean movingForSafeWalk = mc.options.keyUp.isDown() || mc.options.keyDown.isDown()
                || mc.options.keyLeft.isDown() || mc.options.keyRight.isDown();
        boolean shouldForceSneak = safe.enabled && movingForSafeWalk && mc.player.onGround();
        if (shouldForceSneak) {
            mc.options.keyShift.setDown(true);
            sneakForced = true;
        } else if (sneakForced) {
            mc.options.keyShift.setDown(false);
            sneakForced = false;
        }

        if (fly.enabled) {
            var a = mc.player.getAbilities();
            if (!flyForced) {
                flyPrevMayfly = a.mayfly;
                flyPrevFlying = a.flying;
                flyForced = true;
            }
            a.mayfly = true;
            a.flying = true;
            a.setFlyingSpeed((float) fly.num("Speed").value);
        } else if (flyForced) {
            restoreFly(mc);
        }
        if (respawn.enabled && mc.player.isDeadOrDying()) mc.player.respawn();

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

        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();
        if (clicker.enabled && clickAllowed) {
            double cps = Math.max(1.0, Math.min(20.0, clicker.num("CPS").value));
            clickAccumulator = Math.min(2.0, clickAccumulator + cps / 20.0);
            if (clickAccumulator >= 1.0) {
                clickAccumulator -= 1.0;
                Entity clickTarget = null;
                if (mc.hitResult instanceof EntityHitResult hit && validClickTarget(mc, clicker, hit.getEntity())) {
                    clickTarget = hit.getEntity();
                }
                if (clickTarget == null) {
                    clickTarget = nearestTarget(mc, clicker.num("Range").value, clicker.num("FOV").value,
                            clicker.bool("Players").value, clicker.bool("Mobs").value, clicker.bool("Invisible").value);
                }
                if (clickTarget != null) attack(mc, clickTarget);
            }
        } else clickAccumulator = 0.0;

        if (aura.enabled) {
            if (auraCooldown-- <= 0) {
                auraCooldown = Math.max(1, (int) Math.round(aura.num("Delay").value));
                Entity target = nearestTarget(mc, aura.num("Range").value, aura.num("FOV").value,
                        aura.bool("Players").value, aura.bool("Mobs").value, aura.bool("Invisible").value);
                if (target != null) attack(mc, target);
            }
        } else auraCooldown = 0;

        if (test.enabled) runTestProfile(mc, test);
        else {
            testAttackCooldown = 0;
            testCycleTicks = 0;
            testJumpTicks = 0;
        }
        boolean shouldForceJump = (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater())
                || (test.enabled && testJumpTicks > 0);
        if (shouldForceJump) {
            mc.options.keyJump.setDown(true);
            jumpForced = true;
        } else if (jumpForced) {
            mc.options.keyJump.setDown(false);
            jumpForced = false;
        }
        if (testJumpTicks > 0) testJumpTicks--;

        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);
    }

    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {
        if (!(target instanceof LivingEntity) || !target.isAlive() || mc.player == null) return false;
        if (target instanceof Player && !clicker.bool("Players").value) return false;
        if (!(target instanceof Player) && !clicker.bool("Mobs").value) return false;
        if (target.isInvisible() && !clicker.bool("Invisible").value) return false;
        if (angleFromView(mc.player, target) > clicker.num("FOV").value / 2.0) return false;
        double r = clicker.num("Range").value;
        return mc.player.distanceToSqr(target) <= r * r;
    }

    private static void attack(Minecraft mc, Entity target) {
        if (mc.player == null || mc.gameMode == null || target == null || !target.isAlive()) return;
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

    private static boolean runFollow(Minecraft mc, Mod follow) {
        if (mc.player == null) return false;
        double search = follow.num("Search Range").value;
        if (followTarget == null || !followTarget.isAlive() || mc.player.distanceToSqr(followTarget) > search * search) {
            followTarget = nearestTarget(mc, search, 360.0, follow.bool("Players").value, follow.bool("Mobs").value, true);
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

    private static void runTestProfile(Minecraft mc, Mod test) {
        if (mc.player == null) return;
        int cycle = Math.max(40, (int) Math.round(test.num("Cycle Seconds").value * 20.0));
        if (++testCycleTicks >= cycle) {
            testCycleTicks = 0;
            if (test.bool("Auto Sweep").value) {
                testPhase = (testPhase % 5) + 1;
                test.num("Level").set(testPhase);
            }
            int level = (int) Math.round(test.num("Level").value);
            if (test.bool("Movement").value) testJumpTicks = 2;
            if (test.bool("Rotation").value) mc.player.setYRot(mc.player.getYRot() + 15.0f * level);
            appendTestLog("PROFILE level=" + level + " combat=" + test.bool("Combat").value
                    + " movement=" + test.bool("Movement").value + " rotation=" + test.bool("Rotation").value
                    + " xyz=" + String.format(Locale.ROOT, "%.1f,%.1f,%.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
        }
        if (test.bool("Combat").value) {
            int level = (int) Math.round(test.num("Level").value);
            if (testAttackCooldown-- <= 0) {
                testAttackCooldown = Math.max(1, 6 - level);
                Entity t = nearestTarget(mc, 5.5, 360.0, true, true, true);
                if (t != null) attack(mc, t);
            }
        } else testAttackCooldown = 0;
    }

    private static void appendTestLog(String line) {
        try {
            Files.createDirectories(TEST_LOG.getParent());
            Files.writeString(TEST_LOG, Instant.now() + " " + line + System.lineSeparator(),
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception ignored) {}
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
            if ((m.name.equals("AutoWalk") || m.name.equals("Follow"))
                    && !find("AutoWalk").enabled && !find("Follow").enabled && forwardForced) {
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
            if (m.name.equals("Test Profile")) appendTestLog("SESSION STOP");
        }
        if (m.enabled && m.name.equals("Test Profile")) appendTestLog("SESSION START Eio=" + VERSION);
        notifyToggle(m);
        save();
    }

    private static void restoreFly(Minecraft mc) {
        if (mc.player != null && flyForced) {
            var a = mc.player.getAbilities();
            a.mayfly = flyPrevMayfly;
            a.flying = flyPrevFlying;
            a.setFlyingSpeed(0.05f);
            mc.player.onUpdateAbilities();
        }
        flyForced = false;
    }

    private static void releaseRuntimeState(Minecraft mc) {
        if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
        if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
        if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
        if (flyForced) restoreFly(mc);
        clearFullbright(mc);
        followTarget = null;
        clickAccumulator = 0.0;
        auraCooldown = 0;
        testAttackCooldown = 0;
        testCycleTicks = 0;
        testJumpTicks = 0;
        lowHealthAlerted = false;
        lowHealthCooldown = 0;
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
        }
    }

    private static void resetAllSettings() {
        for (Mod m : MODS) resetModuleSettings(m);
    }

    private static String validateModel() {
        Set<String> categories = Set.of("Combat", "Movement", "Player", "Render", "World", "Testing", "Misc");
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
        if (find("Speed").enabled) {
            var velocity = mc.player.getDeltaMovement();
            double bps = Math.sqrt(velocity.x * velocity.x + velocity.z * velocity.z) * 20.0;
            g.text(mc.font, String.format(Locale.ROOT, "Speed %.2f b/s", bps), 5, y, 0xFFD9E0E6, true); y += 11;
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
        if (find("Target HUD").enabled) {
            Entity t = followTarget;
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
    private static final class Mod {
        final String name, category, description; final int defaultKey; boolean enabled; KeyMapping bind; final List<Setting> settings = new ArrayList<>();
        Mod(String name, String category, String description, int defaultKey) { this.name = name; this.category = category; this.description = description; this.defaultKey = defaultKey; }
        Mod bool(String name, boolean value) { return bool(name, value, name); }
        Mod bool(String name, boolean value, String description) { settings.add(new BoolSetting(name, value, description)); return this; }
        Mod num(String name, double value, double min, double max, double step) { return num(name, value, min, max, step, name); }
        Mod num(String name, double value, double min, double max, double step, String description) { settings.add(new NumSetting(name, value, min, max, step, description)); return this; }
        BoolSetting bool(String name) { for (Setting s : settings) if (s instanceof BoolSetting b && b.name.equals(name)) return b; throw new IllegalArgumentException(name); }
        NumSetting num(String name) { for (Setting s : settings) if (s instanceof NumSetting n && n.name.equals(name)) return n; throw new IllegalArgumentException(name); }
    }
    private static final class Waypoint { final String name; final double x, y, z; Waypoint(String name, double x, double y, double z) { this.name = name; this.x = x; this.y = y; this.z = z; } }

    public static final class ClickGui extends Screen {
        private static final String[] CATEGORIES = {"Combat", "Movement", "Player", "Render", "World", "Testing", "Misc"};
        private String selectedCategory = "Combat";
        private Mod selectedMod;

        ClickGui() { super(Component.literal("Eio Client")); }
        @Override public boolean isPauseScreen() { return false; }
        @Override public void added() { super.added(); guiOpen = true; if (selectedMod == null) selectedMod = firstInCategory(selectedCategory); }
        @Override public void removed() { guiOpen = false; save(); super.removed(); }
        @Override public void onClose() { guiOpen = false; save(); super.onClose(); }

        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (m.category.equals(category)) return m;
            return null;
        }

        private int panelW() { return Math.min(438, width - 14); }
        private int panelH() { return Math.min(254, height - 14); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int accent = categoryColor(selectedCategory);
            String help = selectedMod == null ? "Choose a module" : selectedMod.description;

            // Very light dimming, soft shadow, then translucent glass shell.
            g.fill(0, 0, width, height, 0x0A000000);
            g.fill(x + 3, y + 4, x + bw + 3, y + bh + 4, 0x35000000);
            g.fill(x, y, x + bw, y + bh, 0xA0080D13);
            g.fill(x, y, x + bw, y + 22, 0xC0101720);
            g.fill(x, y + 21, x + bw, y + 22, 0x88475562);
            g.fill(x, y, x + 2, y + bh, accent);

            g.text(font, "Eio", x + 9, y + 7, 0xFFF3F8FB, true);
            g.text(font, VERSION, x + 31, y + 7, 0xFF64727E, false);
            String enabledStatus = enabledCount() + "/" + MODS.size() + (runtimeSafeMode ? " SAFE" : "");
            g.text(font, enabledStatus, x + 76, y + 7, runtimeSafeMode ? 0xFFFFA071 : 0xFF6F8898, false);
            String closeHint = "RSHIFT";
            g.text(font, closeHint, x + bw - font.width(closeHint) - 8, y + 7, 0xFF64727E, false);

            // Slim horizontal categories - no large sidebar.
            int tabsX = x + 7, tabsY = y + 27;
            int gap = 2;
            int tabW = (bw - 14 - gap * (CATEGORIES.length - 1)) / CATEGORIES.length;
            for (int i = 0; i < CATEGORIES.length; i++) {
                String category = CATEGORIES[i];
                int tx = tabsX + i * (tabW + gap);
                boolean active = category.equals(selectedCategory);
                boolean hover = in(mx, my, tx, tabsY, tabW, 15);
                g.fill(tx, tabsY, tx + tabW, tabsY + 15, active ? 0xB51A2731 : (hover ? 0x71151F27 : 0x3510151B));
                if (active) g.fill(tx + 4, tabsY + 13, tx + tabW - 4, tabsY + 15, accent);
                g.centeredText(font, shortCat(category), tx + tabW / 2, tabsY + 5, active ? 0xFFF0F6FA : 0xFF8D9AA5);
                if (hover) help = "Category: " + category;
            }

            int bodyY = y + 47;
            int footerY = y + bh - 22;
            int modulesX = x + 7;
            int modulesW = 232;
            int settingsX = modulesX + modulesW + 7;
            int settingsW = x + bw - 7 - settingsX;

            g.fill(modulesX, bodyY, modulesX + modulesW, footerY - 4, 0x480D1218);
            g.fill(settingsX, bodyY, settingsX + settingsW, footerY - 4, 0x480D1218);

            // Dense two-column module cards.
            int cardGap = 4;
            int cardW = (modulesW - 12 - cardGap) / 2;
            int index = 0;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                int col = index % 2;
                int row = index / 2;
                int cx = modulesX + 4 + col * (cardW + cardGap);
                int cy = bodyY + 5 + row * 24;
                boolean selected = m == selectedMod;
                boolean hover = in(mx, my, cx, cy, cardW, 20);
                g.fill(cx, cy, cx + cardW, cy + 20, selected ? 0xA01B2B35 : (hover ? 0x7217212A : 0x3511161C));
                if (m.enabled) g.fill(cx, cy, cx + 2, cy + 20, 0xFF62D39B);
                g.text(font, trim(m.name, 13), cx + 6, cy + 6, m.enabled ? 0xFFF3F7F9 : 0xFFC3CDD5, false);
                String state = m.enabled ? "ON" : "";
                if (!state.isEmpty()) g.text(font, state, cx + cardW - font.width(state) - 5, cy + 6, 0xFF72DDA5, false);
                if (hover) help = m.description;
                index++;
            }

            if (selectedMod == null) {
                g.text(font, "Choose a module", settingsX + 8, bodyY + 10, 0xFFD7E0E8, false);
            } else {
                int sx = settingsX + 6;
                int sw = settingsW - 12;
                int sy = bodyY + 6;

                // Header row doubles as the compact enable switch.
                boolean hoverToggle = in(mx, my, sx, sy, sw, 18);
                g.fill(sx, sy, sx + sw, sy + 18, selectedMod.enabled ? 0x8E1A4A39 : (hoverToggle ? 0x6219222A : 0x3B11171D));
                g.text(font, trim(selectedMod.name, 18), sx + 6, sy + 5, 0xFFF0F4F7, true);
                String state = selectedMod.enabled ? "ON" : "OFF";
                g.text(font, state, sx + sw - font.width(state) - 6, sy + 5, selectedMod.enabled ? 0xFF73DFA7 : 0xFF86929C, false);
                if (hoverToggle) help = "Toggle " + selectedMod.name;
                sy += 21;

                // Key row opens vanilla Controls, preserving Minecraft's native rebinding behavior.
                boolean hoverBind = in(mx, my, sx, sy, sw, 17);
                g.fill(sx, sy, sx + sw, sy + 17, hoverBind ? 0x661A2530 : 0x3511161C);
                String key = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "NONE" : selectedMod.bind.getTranslatedKeyMessage().getString();
                g.text(font, "Keybind", sx + 5, sy + 5, 0xFFBBC5CD, false);
                String keyTrim = trim(key, 10);
                g.text(font, keyTrim, sx + sw - font.width(keyTrim) - 5, sy + 5, 0xFF94D8F6, false);
                if (hoverBind) help = "Open Minecraft Controls to change this keybind";
                sy += 20;

                // Every current module setting fits without hidden/unclickable rows.
                for (Setting setting : selectedMod.settings) {
                    boolean hover = in(mx, my, sx, sy, sw, 18);
                    g.fill(sx, sy, sx + sw, sy + 18, hover ? 0x6119232C : 0x3011161C);
                    if (setting instanceof BoolSetting b) {
                        g.text(font, trim(b.name, 14), sx + 5, sy + 5, 0xFFD5DDE4, false);
                        String value = (b.value ? "ON" : "OFF") + (b.value != b.defaultValue ? "*" : "");
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 5, b.value ? 0xFF69D99B : 0xFFC87575, false);
                    } else if (setting instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        g.text(font, trim(n.name, 12), sx + 5, sy + 3, 0xFFD5DDE4, false);
                        String value = n.display() + (Math.abs(n.value - n.defaultValue) > 1.0E-9 ? "*" : "");
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 3, 0xFF9DD9FF, false);
                        g.fill(sx + 4, sy + 15, sx + sw - 4, sy + 17, 0x55303C47);
                        g.fill(sx + 4, sy + 15, sx + 4 + (int) ((sw - 8) * ratio), sy + 17, accent);
                    }
                    if (hover) help = setting.description;
                    sy += 19;
                }
            }

            // Fixed help/status footer avoids popups covering controls.
            g.fill(x + 7, footerY, x + bw - 7, y + bh - 6, 0x3210151B);
            String footerHelp = help + "  |  RMB setting/module = reset";
            g.text(font, trim(footerHelp, 66), x + 11, footerY + 5, 0xFF82909B, false);

            super.extractRenderState(g, mx, my, delta);
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            boolean leftClick = e.button() == InputConstants.MOUSE_BUTTON_LEFT;
            boolean rightClick = e.button() == InputConstants.MOUSE_BUTTON_RIGHT;
            if (!leftClick && !rightClick) return super.mouseClicked(e, doubled);

            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int tabsX = x + 7, tabsY = y + 27;
            int gap = 2;
            int tabW = (bw - 14 - gap * (CATEGORIES.length - 1)) / CATEGORIES.length;
            for (int i = 0; i < CATEGORIES.length; i++) {
                int tx = tabsX + i * (tabW + gap);
                if (in(e.x(), e.y(), tx, tabsY, tabW, 15)) {
                    selectedCategory = CATEGORIES[i];
                    selectedMod = firstInCategory(selectedCategory);
                    return true;
                }
            }

            int bodyY = y + 47;
            int modulesX = x + 7;
            int modulesW = 232;
            int settingsX = modulesX + modulesW + 7;
            int settingsW = x + bw - 7 - settingsX;
            int cardGap = 4;
            int cardW = (modulesW - 12 - cardGap) / 2;

            int index = 0;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                int col = index % 2;
                int row = index / 2;
                int cx = modulesX + 4 + col * (cardW + cardGap);
                int cy = bodyY + 5 + row * 24;
                if (in(e.x(), e.y(), cx, cy, cardW, 20)) {
                    selectedMod = m;
                    if (leftClick) toggle(m);
                    else if (rightClick) {
                        resetModuleSettings(m);
                        save();
                        notifyMessage(m.name + " settings reset", 0xFF9DD9FF, 1800L);
                    }
                    return true;
                }
                index++;
            }

            if (selectedMod != null) {
                int sx = settingsX + 6;
                int sw = settingsW - 12;
                int sy = bodyY + 6;
                if (leftClick && in(e.x(), e.y(), sx, sy, sw, 18)) {
                    toggle(selectedMod);
                    return true;
                }
                sy += 21;
                if (leftClick && in(e.x(), e.y(), sx, sy, sw, 17)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 20;
                for (Setting setting : selectedMod.settings) {
                    if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                        if (rightClick) {
                            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                        } else if (leftClick) {
                            if (setting instanceof BoolSetting b) {
                                b.value = !b.value;
                            } else if (setting instanceof NumSetting n) {
                                double ratio = (e.x() - (sx + 4.0)) / Math.max(1.0, sw - 8.0);
                                ratio = Math.max(0.0, Math.min(1.0, ratio));
                                n.set(n.min + ratio * (n.max - n.min));
                            }
                        }
                        save();
                        return true;
                    }
                    sy += 19;
                }
            }

            return super.mouseClicked(e, doubled);
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
                for (int row = 0; row < pixels.length; row++) {
                    for (int col = 0; col < pixels[row].length(); col++) {
                        if (pixels[row].charAt(col) == '#') {
                            g.fill(px + col * scale, y + row * scale,
                                    px + (col + 1) * scale, y + (row + 1) * scale, rgb);
                        }
                    }
                }
                px += 4 * scale;
            }
        }

        private static int categoryColor(String category) {
            return switch (category) {
                case "Combat" -> 0xFFE97979;
                case "Movement" -> 0xFF6AC7F0;
                case "Player" -> 0xFF79D69A;
                case "Render" -> 0xFFC497F3;
                case "World" -> 0xFFF0C778;
                case "Testing" -> 0xFFF09A68;
                default -> 0xFF83B7D4;
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
            return switch (c) {
                case "Movement" -> "Move";
                case "Testing" -> "Test";
                default -> c;
            };
        }

        private static boolean in(double mx, double my, int x, int y, int w, int h) {
            return mx >= x && mx < x + w && my >= y && my < y + h;
        }

        private static String trim(String text, int max) {
            return text.length() <= max ? text : text.substring(0, Math.max(0, max - 1)) + "…";
        }
    }
}
