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
import java.util.*;

public final class EioClient implements ClientModInitializer {
    public static final String VERSION = "0.9.0";
    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");
    private static final List<Mod> MODS = new ArrayList<>();
    private static final Map<String, Waypoint> WAYPOINTS = new LinkedHashMap<>();
    private static KeyMapping.Category keyCategory;
    private static KeyMapping guiKey;
    private static boolean guiOpen;
    private static int clickCooldown;
    private static int auraCooldown;
    private static int testAttackCooldown;
    private static int testCycleTicks;
    private static int testJumpTicks;
    private static int testPhase;
    private static MobEffectInstance fullbrightInjected;
    private static String notificationText = "";
    private static long notificationUntil;
    private static Entity followTarget;

    static {
        mod("Kill Aura", "Combat", "Attacks the nearest allowed living target inside the configured range.", InputConstants.KEY_K)
                .num("Range", 4.0, 1.0, 6.0, 0.25, "Maximum distance at which a target can be selected.")
                .num("Delay", 5.0, 1.0, 20.0, 1.0, "Ticks between attack attempts. Lower values attack more often.")
                .num("FOV", 180.0, 30.0, 360.0, 15.0, "Horizontal field of view in degrees used for target selection.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible living targets.");
        mod("Auto Clicker", "Combat", "Automatically attacks the entity under your crosshair at a fixed configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Fixed clicks per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance to the crosshair target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.");

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

        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
        mod("Inventory Info", "Player", "Shows occupied inventory slots on the HUD.", -1);
        mod("Durability HUD", "Player", "Shows durability of the selected item.", -1);

        mod("Coordinates", "Render", "Shows your XYZ position.", -1);
        mod("FPS", "Render", "Shows current FPS.", -1);
        mod("Active Modules", "Render", "Lists enabled modules on the HUD.", -1);
        mod("Target HUD", "Render", "Shows the current crosshair or Follow target and its distance.", -1);
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

        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1);
        mod("Notifications", "Misc", "Shows a small upper-left card when modules are toggled.", -1)
                .num("Seconds", 2.0, 0.5, 5.0, 0.5, "How long toggle notifications remain visible.");
    }

    private static Mod mod(String name, String category, String description, int defaultKey) {
        Mod m = new Mod(name, category, description, defaultKey);
        MODS.add(m);
        return m;
    }

    @Override
    public void onInitializeClient() {
        load();
        keyCategory = KeyMapping.Category.register(Identifier.fromNamespaceAndPath("eioclient", "general"));
        guiKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
                "key.eioclient.v090.clickgui", InputConstants.Type.KEYBOARD, InputConstants.KEY_RSHIFT, keyCategory));
        for (Mod m : MODS) {
            int key = m.defaultKey < 0 ? InputConstants.UNKNOWN.getValue() : m.defaultKey;
            m.bind = KeyMappingHelper.registerKeyMapping(new KeyMapping(
                    "key.eioclient.v090." + slug(m.name), InputConstants.Type.KEYBOARD, key, keyCategory));
        }

        ClientTickEvents.END_CLIENT_TICK.register(EioClient::tick);
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient", "hud"), EioClient::hud);
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

    private static void tick(Minecraft mc) {
        while (guiKey != null && guiKey.consumeClick()) {
            if (!guiOpen) openGui();
        }
        for (Mod m : MODS) {
            if (m.bind != null) while (m.bind.consumeClick()) {
                if (!guiOpen && mc.player != null) toggle(m);
            }
        }
        if (mc.player == null) return;

        Mod walk = find("AutoWalk");
        Mod sprint = find("Sprint");
        Mod follow = find("Follow");
        Mod fly = find("Fly");
        Mod safe = find("SafeWalk");
        Mod autoJump = find("Auto Jump");
        Mod respawn = find("Auto Respawn");
        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod bright = find("Fullbright");
        Mod test = find("Test Profile");

        if (walk.enabled) mc.options.keyUp.setDown(true);
        if (sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            boolean hungerOk = !sprint.bool("Hunger Check").value || mc.player.getFoodData().getFoodLevel() > 6;
            if (hungerOk) mc.player.setSprinting(true);
        }
        if (safe.enabled) {
            boolean moving = mc.options.keyUp.isDown() || mc.options.keyDown.isDown()
                    || mc.options.keyLeft.isDown() || mc.options.keyRight.isDown();
            mc.options.keyShift.setDown(moving && mc.player.onGround());
        }
        if (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround()) mc.options.keyJump.setDown(true);
        else if (!test.enabled || testJumpTicks <= 0) mc.options.keyJump.setDown(false);

        if (follow.enabled) runFollow(mc, follow);

        if (fly.enabled) {
            var a = mc.player.getAbilities();
            a.mayfly = true;
            a.flying = true;
            a.setFlyingSpeed((float) fly.num("Speed").value);
        }
        if (respawn.enabled && mc.player.isDeadOrDying()) mc.player.respawn();

        if (clicker.enabled) {
            if (clickCooldown-- <= 0) {
                int cps = Math.max(1, (int) Math.round(clicker.num("CPS").value));
                clickCooldown = Math.max(1, 20 / cps);
                if (mc.hitResult instanceof EntityHitResult hit && validClickTarget(mc, clicker, hit.getEntity())) attack(mc, hit.getEntity());
            }
        } else clickCooldown = 0;

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
        if (testJumpTicks > 0) {
            mc.options.keyJump.setDown(true);
            testJumpTicks--;
        }

        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);
    }

    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {
        if (!(target instanceof LivingEntity) || !target.isAlive() || mc.player == null) return false;
        if (target instanceof Player && !clicker.bool("Players").value) return false;
        if (!(target instanceof Player) && !clicker.bool("Mobs").value) return false;
        double r = clicker.num("Range").value;
        return mc.player.distanceToSqr(target) <= r * r;
    }

    private static void attack(Minecraft mc, Entity target) {
        if (mc.player == null || mc.gameMode == null || target == null || !target.isAlive()) return;
        mc.gameMode.attack(mc.player, target);
        mc.player.swing(InteractionHand.MAIN_HAND, mc.player.getMainHandItem().getAttackAnimation(), true);
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

    private static void runFollow(Minecraft mc, Mod follow) {
        if (mc.player == null) return;
        double search = follow.num("Search Range").value;
        if (followTarget == null || !followTarget.isAlive() || mc.player.distanceToSqr(followTarget) > search * search) {
            followTarget = nearestTarget(mc, search, 360.0, follow.bool("Players").value, follow.bool("Mobs").value, true);
        }
        if (followTarget == null) {
            if (!find("AutoWalk").enabled) mc.options.keyUp.setDown(false);
            return;
        }
        double dist = Math.sqrt(mc.player.distanceToSqr(followTarget));
        if (follow.bool("Face Target").value) {
            double dx = followTarget.getX() - mc.player.getX();
            double dz = followTarget.getZ() - mc.player.getZ();
            mc.player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        }
        boolean advance = dist > follow.num("Distance").value;
        mc.options.keyUp.setDown(advance || find("AutoWalk").enabled);
        if (advance && follow.bool("Sprint").value) mc.player.setSprinting(true);
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
            if (m.name.equals("AutoWalk") && !find("Follow").enabled) mc.options.keyUp.setDown(false);
            if (m.name.equals("Follow") && !find("AutoWalk").enabled) mc.options.keyUp.setDown(false);
            if (m.name.equals("SafeWalk")) mc.options.keyShift.setDown(false);
            if (m.name.equals("Auto Jump")) mc.options.keyJump.setDown(false);
            if (m.name.equals("Fly")) {
                var a = mc.player.getAbilities();
                boolean legit = mc.player.isCreative() || mc.player.isSpectator();
                a.mayfly = legit;
                if (!legit) a.flying = false;
                a.setFlyingSpeed(0.05f);
                mc.player.onUpdateAbilities();
            }
            if (m.name.equals("Fullbright")) clearFullbright(mc);
            if (m.name.equals("Test Profile")) appendTestLog("SESSION STOP");
        }
        if (m.enabled && m.name.equals("Test Profile")) appendTestLog("SESSION START Eio=" + VERSION);
        notifyToggle(m);
        save();
    }

    private static void notifyToggle(Mod m) {
        Mod n = find("Notifications");
        if (n == null || !n.enabled) return;
        notificationText = m.name + (m.enabled ? " enabled" : " disabled");
        notificationUntil = System.currentTimeMillis() + (long) (n.num("Seconds").value * 1000.0);
    }

    private static void hud(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        int y = 5;
        g.text(mc.font, "Eio", 5, y, 0xFF8CCDF2, true); y += 11;
        if (find("Session Info").enabled) { g.text(mc.font, "v" + VERSION + " / MC 26.3", 5, y, 0xFF8795A3, false); y += 10; }
        if (find("Coordinates").enabled) { g.text(mc.font, String.format(Locale.ROOT, "XYZ %.1f  %.1f  %.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()), 5, y, 0xFFD9E0E6, true); y += 11; }
        if (find("FPS").enabled) { g.text(mc.font, "FPS " + mc.getFps(), 5, y, 0xFFD9E0E6, true); y += 11; }
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
            for (Mod m : MODS) if (m.enabled && !m.name.equals("Active Modules")) { g.text(mc.font, m.name, 5, y, 0xFF91BDD8, true); y += 10; }
        }
        if (!notificationText.isEmpty() && System.currentTimeMillis() < notificationUntil) {
            int ny = Math.max(18, y + 2), boxW = mc.font.width(notificationText) + 12;
            int color = notificationText.endsWith("enabled") ? 0xFF66D69B : 0xFFCC6B6B;
            g.fill(3, ny - 3, 3 + boxW, ny + 11, 0xB8121720);
            g.text(mc.font, notificationText, 9, ny, color, true);
        }
    }

    private static void drawBrand(GuiGraphicsExtractor g, int width) {
        Minecraft mc = Minecraft.getInstance();
        String text = "Made by Eio";
        int x = width - mc.font.width(text) - 7, y = 7;
        long now = System.currentTimeMillis();
        for (int i = 0; i < text.length(); i++) {
            String ch = text.substring(i, i + 1);
            float hue = ((now % 8000L) / 8000f + i * .035f) % 1f;
            int rgb = Color.HSBtoRGB(hue, .32f, 1f);
            g.text(mc.font, ch, x, y, 0xFF000000 | rgb, false);
            x += mc.font.width(ch);
        }
    }

    private static Mod find(String name) { for (Mod m : MODS) if (m.name.equalsIgnoreCase(name)) return m; return null; }
    private static String summary() { StringJoiner j = new StringJoiner(" | "); for (Mod m : MODS) j.add(m.name + ":" + (m.enabled ? "ON" : "OFF")); return j.toString(); }
    private static String waypointSummary() {
        if (WAYPOINTS.isEmpty()) return "No waypoints saved";
        StringJoiner j = new StringJoiner(" | "); for (Waypoint w : WAYPOINTS.values()) j.add(w.name + " @ " + Math.round(w.x) + "," + Math.round(w.y) + "," + Math.round(w.z)); return j.toString();
    }

    private static void load() {
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); } catch (Exception ignored) {}
        for (Mod m : MODS) {
            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, "false"));
            for (Setting s : m.settings) {
                String v = p.getProperty("setting." + m.name + "." + s.name); if (v == null) continue;
                try { if (s instanceof BoolSetting b) b.value = Boolean.parseBoolean(v); if (s instanceof NumSetting n) n.set(Double.parseDouble(v)); } catch (Exception ignored) {}
            }
        }
        WAYPOINTS.clear();
        for (String key : p.stringPropertyNames()) if (key.startsWith("wp.")) {
            String name = key.substring(3);
            try { String[] a = p.getProperty(key).split(","); if (a.length == 3) WAYPOINTS.put(name, new Waypoint(name, Double.parseDouble(a[0]), Double.parseDouble(a[1]), Double.parseDouble(a[2]))); } catch (Exception ignored) {}
        }
    }

    private static void save() {
        Properties p = new Properties();
        for (Mod m : MODS) {
            p.setProperty("enabled." + m.name, Boolean.toString(m.enabled));
            for (Setting s : m.settings) {
                if (s instanceof BoolSetting b) p.setProperty("setting." + m.name + "." + s.name, Boolean.toString(b.value));
                if (s instanceof NumSetting n) p.setProperty("setting." + m.name + "." + s.name, Double.toString(n.value));
            }
        }
        for (Waypoint w : WAYPOINTS.values()) p.setProperty("wp." + w.name, w.x + "," + w.y + "," + w.z);
        try { Files.createDirectories(CONFIG.getParent()); try (OutputStream out = Files.newOutputStream(CONFIG)) { p.store(out, "Eio Client " + VERSION); } } catch (Exception ignored) {}
    }

    private static abstract class Setting {
        final String name, description;
        Setting(String name, String description) { this.name = name; this.description = description; }
    }
    private static final class BoolSetting extends Setting {
        boolean value;
        BoolSetting(String name, boolean value, String description) { super(name, description); this.value = value; }
    }
    private static final class NumSetting extends Setting {
        double value, min, max, step;
        NumSetting(String name, double value, double min, double max, double step, String description) { super(name, description); this.min = min; this.max = max; this.step = step; set(value); }
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
        @Override public void added() { super.added(); guiOpen = true; }
        @Override public void removed() { guiOpen = false; save(); super.removed(); }
        @Override public void onClose() { guiOpen = false; save(); super.onClose(); }
        @Override public void tick() { super.tick(); }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            String tooltip = null;
            g.fill(0, 0, width, height, 0x35070A0E);
            int bw = Math.min(700, width - 24), bh = Math.min(390, height - 24);
            int x = (width - bw) / 2, y = (height - bh) / 2;
            g.fill(x, y, x + bw, y + bh, 0xD9121720);
            g.fill(x, y, x + bw, y + 29, 0xE0171E29);
            g.fill(x, y, x + 2, y + bh, 0xFF4D9FCB);
            g.text(font, "Eio", x + 13, y + 10, 0xFF8CCDF2, true);
            g.text(font, VERSION, x + 36, y + 10, 0xFF687584, false);
            g.text(font, "Right Shift", x + bw - 70, y + 10, 0xFF596675, false);

            int side = 112, cy = y + 45;
            g.fill(x, y + 29, x + side, y + bh, 0xC80D1118);
            for (String c : CATEGORIES) {
                boolean active = c.equals(selectedCategory), hover = in(mx, my, x + 6, cy - 5, side - 12, 20);
                if (active || hover) g.fill(x + 6, cy - 5, x + side - 6, cy + 15, active ? 0xD9183746 : 0xB8151C25);
                g.text(font, c, x + 14, cy + 1, active ? 0xFF8CCDF2 : 0xFFB7C0CA, false);
                if (hover) tooltip = "Show " + c + " modules.";
                cy += 24;
            }
            drawBlockBrand(g, x + 11, y + bh - 22, 2, 0xFF7CAFD0);

            int lx = x + side + 11, ly = y + 42, lw = 205, ry = ly + 7;
            g.text(font, selectedCategory.toUpperCase(Locale.ROOT), lx, ly - 7, 0xFF738292, false);
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                boolean hover = in(mx, my, lx, ry, lw, 28), chosen = m == selectedMod;
                g.fill(lx, ry, lx + lw, ry + 26, chosen ? 0xD91C3140 : (hover ? 0xD01A222D : 0xB8141A22));
                if (m.enabled) g.fill(lx, ry, lx + 3, ry + 26, 0xFF55B7E8);
                g.text(font, m.name, lx + 8, ry + 6, m.enabled ? 0xFFFFFFFF : 0xFFD1D6DC, false);
                String state = m.enabled ? "ON" : "OFF";
                g.text(font, state, lx + lw - font.width(state) - 8, ry + 6, m.enabled ? 0xFF66D69B : 0xFF66717E, false);
                String key = m.bind == null || m.bind.isUnbound() ? "No bind" : m.bind.getTranslatedKeyMessage().getString();
                g.text(font, key, lx + 8, ry + 16, 0xFF6E8191, false);
                if (hover) tooltip = m.description;
                ry += 31;
            }

            int dx = lx + lw + 13, dw = x + bw - 11 - dx;
            g.fill(dx, ly, dx + dw, y + bh - 13, 0xB80F141B);
            if (selectedMod == null) {
                g.text(font, "Select a module", dx + 14, ly + 16, 0xFFDCE4EB, false);
                g.text(font, "Left click toggles. Right click selects.", dx + 14, ly + 34, 0xFF71808F, false);
            } else {
                g.text(font, selectedMod.name, dx + 14, ly + 15, 0xFFFFFFFF, true);
                g.text(font, trim(selectedMod.description, 48), dx + 14, ly + 34, 0xFFAEB9C4, false);
                int sy = ly + 58;
                boolean hEnable = in(mx, my, dx + 14, sy, dw - 28, 24);
                g.fill(dx + 14, sy, dx + dw - 14, sy + 24, selectedMod.enabled ? 0xD9176B4B : 0xD926303B);
                g.centeredText(font, selectedMod.enabled ? "ENABLED" : "DISABLED", dx + dw / 2, sy + 8, 0xFFFFFFFF);
                if (hEnable) tooltip = "Toggle " + selectedMod.name + ".";
                sy += 30;
                g.fill(dx + 14, sy, dx + dw - 14, sy + 24, 0xCC1B2631);
                String bindText = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "KEYBIND: NONE" : "KEYBIND: " + selectedMod.bind.getTranslatedKeyMessage().getString();
                g.centeredText(font, bindText, dx + dw / 2, sy + 8, 0xFFDCE4EB);
                if (in(mx, my, dx + 14, sy, dw - 28, 24)) tooltip = "Current keybind. Use Open Keybinds to change it.";
                sy += 30;
                g.fill(dx + 14, sy, dx + dw - 14, sy + 22, 0xCC16212C);
                g.centeredText(font, "OPEN KEYBINDS", dx + dw / 2, sy + 7, 0xFF9DD9FF);
                if (in(mx, my, dx + 14, sy, dw - 28, 22)) tooltip = "Open Minecraft's controls screen for all Eio keybinds.";
                sy += 29;

                for (Setting s : selectedMod.settings) {
                    boolean hs = in(mx, my, dx + 14, sy, dw - 28, 23);
                    if (s instanceof BoolSetting b) {
                        g.fill(dx + 14, sy, dx + dw - 14, sy + 23, hs ? 0xD019222C : 0xB8141B23);
                        g.text(font, b.name, dx + 21, sy + 7, 0xFFDCE4EB, false);
                        String v = b.value ? "ON" : "OFF";
                        g.text(font, v, dx + dw - 21 - font.width(v), sy + 7, b.value ? 0xFF66D69B : 0xFFCC6B6B, false);
                    } else if (s instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        int left = dx + 14, right = dx + dw - 14;
                        g.fill(left, sy, right, sy + 23, hs ? 0xD019222C : 0xB8141B23);
                        g.fill(left, sy + 20, left + (int) ((right - left) * ratio), sy + 23, 0xFF4D9FCB);
                        g.text(font, n.name, dx + 21, sy + 7, 0xFFDCE4EB, false);
                        String v = n.display();
                        g.text(font, v, dx + dw - 21 - font.width(v), sy + 7, 0xFF9DD9FF, false);
                    }
                    if (hs) tooltip = s.description;
                    sy += 27;
                }
                if (selectedMod.name.equals("Follow")) {
                    g.text(font, "Look at entity: /eio followtarget", dx + 16, sy + 1, 0xFF71808F, false);
                } else if (selectedMod.name.equals("Waypoints")) {
                    g.text(font, "/eio waypoint add <name>", dx + 16, sy + 1, 0xFF71808F, false);
                } else if (selectedMod.name.equals("Test Profile")) {
                    g.text(font, "Log: config/eio-test-session.log", dx + 16, sy + 1, 0xFF71808F, false);
                }
            }

            if (tooltip != null && !tooltip.isEmpty()) {
                int tw = Math.min(bw - 24, font.width(trim(tooltip, 80)) + 14);
                int tx = Math.max(x + 7, Math.min(mx + 10, x + bw - tw - 7));
                int ty = Math.max(y + 32, Math.min(my + 12, y + bh - 24));
                g.fill(tx, ty, tx + tw, ty + 18, 0xE70A0E13);
                g.text(font, trim(tooltip, 80), tx + 7, ty + 6, 0xFFE2E8EE, false);
            }
            super.extractRenderState(g, mx, my, delta);
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            int bw = Math.min(700, width - 24), bh = Math.min(390, height - 24);
            int x = (width - bw) / 2, y = (height - bh) / 2, cy = y + 45;
            boolean leftClick = e.button() == InputConstants.MOUSE_BUTTON_LEFT;
            for (String c : CATEGORIES) {
                if (in(e.x(), e.y(), x + 6, cy - 5, 100, 20)) { selectedCategory = c; selectedMod = null; return true; }
                cy += 24;
            }
            int lx = x + 123, ly = y + 42, ry = ly + 7, lw = 205;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                if (in(e.x(), e.y(), lx, ry, lw, 26)) { selectedMod = m; if (leftClick) toggle(m); return true; }
                ry += 31;
            }
            if (selectedMod != null) {
                int dx = lx + lw + 13, dw = x + bw - 11 - dx, sy = ly + 58;
                if (leftClick && in(e.x(), e.y(), dx + 14, sy, dw - 28, 24)) { toggle(selectedMod); return true; }
                sy += 30;
                sy += 30;
                if (leftClick && in(e.x(), e.y(), dx + 14, sy, dw - 28, 22)) {
                    Minecraft mc = Minecraft.getInstance(); mc.setScreenAndShow(new KeyBindsScreen(this, mc.options)); return true;
                }
                sy += 29;
                for (Setting s : selectedMod.settings) {
                    if (leftClick && in(e.x(), e.y(), dx + 14, sy, dw - 28, 23)) {
                        if (s instanceof BoolSetting b) b.value = !b.value;
                        if (s instanceof NumSetting n) {
                            double ratio = (e.x() - (dx + 14.0)) / Math.max(1.0, dw - 28.0);
                            n.set(n.min + Math.max(0.0, Math.min(1.0, ratio)) * (n.max - n.min));
                        }
                        save(); return true;
                    }
                    sy += 27;
                }
            }
            return super.mouseClicked(e, doubled);
        }

        private static void drawBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale, int color) {
            String text = "MADE BY EIO"; int px = x;
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                if (c == ' ') { px += 2 * scale; continue; }
                String[] p = pattern(c);
                for (int row = 0; row < p.length; row++) for (int col = 0; col < p[row].length(); col++) if (p[row].charAt(col) == '#')
                    g.fill(px + col * scale, y + row * scale, px + (col + 1) * scale, y + (row + 1) * scale, color);
                px += 4 * scale;
            }
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
        private static boolean in(double mx, double my, int x, int y, int w, int h) { return mx >= x && mx < x + w && my >= y && my < y + h; }
        private static String trim(String s, int max) { return s.length() <= max ? s : s.substring(0, max - 1) + "…"; }
    }
}
