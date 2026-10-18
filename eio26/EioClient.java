package com.eio.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.*;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
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
import java.util.*;

public final class EioClient implements ClientModInitializer {
    public static final String VERSION = "0.8.0";
    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final List<Mod> MODS = new ArrayList<>();
    private static final Map<String, Waypoint> WAYPOINTS = new LinkedHashMap<>();
    private static KeyMapping.Category keyCategory;
    private static boolean guiOpen;
    private static boolean guiGlobalPrev;
    private static boolean guiLocalPrev;
    private static int clickCooldown;
    private static int auraCooldown;
    private static MobEffectInstance fullbrightInjected;
    private static String notificationText = "";
    private static long notificationUntil;

    static {
        mod("Kill Aura", "Combat", "Attacks the nearest living target in range. No anti-cheat bypass logic.", -1)
                .num("Range", 4.0, 1.0, 6.0, 0.25)
                .num("Delay", 5.0, 1.0, 20.0, 1.0)
                .bool("Players", true)
                .bool("Mobs", true);
        mod("Auto Clicker", "Combat", "Automatically attacks the entity under your crosshair.", -1)
                .num("CPS", 10.0, 1.0, 20.0, 1.0);

        mod("Sprint", "Movement", "Automatically sprints while moving forward.", InputConstants.KEY_R)
                .bool("Hunger Check", true);
        mod("AutoWalk", "Movement", "Keeps moving forward until disabled.", InputConstants.KEY_G);
        mod("Fly", "Movement", "Creative-style client flight with adjustable speed.", InputConstants.KEY_F)
                .num("Speed", 0.10, 0.05, 1.00, 0.05);
        mod("SafeWalk", "Movement", "Automatically sneaks while moving on the ground to reduce edge falls.", -1);

        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
        mod("Inventory Info", "Player", "Shows occupied inventory slots on the HUD.", -1);
        mod("Durability HUD", "Player", "Shows durability of the selected item.", -1);

        mod("Coordinates", "Render", "Shows your XYZ position.", -1);
        mod("FPS", "Render", "Shows current FPS.", -1);
        mod("Active Modules", "Render", "Lists enabled modules on the HUD.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);

        mod("Chunk Info", "World", "Shows your current chunk coordinates.", -1);
        mod("Waypoints", "World", "Shows your nearest saved waypoint and distance.", -1);

        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1);
        mod("Notifications", "Misc", "Shows a small HUD message when modules are toggled.", -1)
                .num("Seconds", 2.0, 0.5, 5.0, 0.5);
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
        for (Mod m : MODS) {
            m.bind = KeyMappingHelper.registerKeyMapping(new KeyMapping(
                    "key.eioclient." + slug(m.name), InputConstants.Type.KEYBOARD, m.defaultKey, keyCategory));
        }

        ClientTickEvents.END_CLIENT_TICK.register(EioClient::tick);
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient", "hud"), EioClient::hud);
        ScreenEvents.AFTER_INIT.register((client, screen, w, h) -> {
            if (screen instanceof TitleScreen) {
                ScreenEvents.afterExtract(screen).register((s, g, mx, my, delta) -> drawBrand(g, s.width));
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
        boolean rshift = InputConstants.isKeyDown(InputConstants.KEY_RSHIFT);
        if (rshift && !guiGlobalPrev && !guiOpen) openGui();
        guiGlobalPrev = rshift;

        for (Mod m : MODS) {
            if (m.bind != null) {
                while (m.bind.consumeClick()) {
                    if (!guiOpen && mc.player != null) toggle(m);
                }
            }
        }

        if (mc.player == null) return;

        Mod walk = find("AutoWalk");
        Mod sprint = find("Sprint");
        Mod fly = find("Fly");
        Mod safe = find("SafeWalk");
        Mod respawn = find("Auto Respawn");
        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod bright = find("Fullbright");

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
                if (mc.hitResult instanceof EntityHitResult hit) attack(mc, hit.getEntity());
            }
        } else clickCooldown = 0;

        if (aura.enabled) {
            if (auraCooldown-- <= 0) {
                auraCooldown = Math.max(1, (int) Math.round(aura.num("Delay").value));
                Entity target = nearestTarget(mc, aura);
                if (target != null) attack(mc, target);
            }
        } else auraCooldown = 0;

        if (bright.enabled) maintainFullbright(mc);
        else clearFullbright(mc);
    }

    private static void attack(Minecraft mc, Entity target) {
        if (mc.player == null || mc.gameMode == null || target == null || !target.isAlive()) return;
        mc.gameMode.attack(mc.player, target);
        mc.player.swing(InteractionHand.MAIN_HAND);
    }

    private static Entity nearestTarget(Minecraft mc, Mod aura) {
        if (mc.player == null || mc.level == null) return null;
        double range = aura.num("Range").value;
        boolean players = aura.bool("Players").value;
        boolean mobs = aura.bool("Mobs").value;
        AABB box = mc.player.getBoundingBox().inflate(range);
        Entity best = null;
        double bestSq = range * range;
        for (Entity e : mc.level.getEntities(mc.player, box, e -> e instanceof LivingEntity && e.isAlive())) {
            if (e instanceof Player && !players) continue;
            if (!(e instanceof Player) && !mobs) continue;
            double d = mc.player.distanceToSqr(e);
            if (d <= bestSq) { bestSq = d; best = e; }
        }
        return best;
    }

    private static void maintainFullbright(Minecraft mc) {
        if (mc.player == null) return;
        MobEffectInstance current = mc.player.getEffect(MobEffects.NIGHT_VISION);
        if (current != null && current != fullbrightInjected) {
            fullbrightInjected = null;
            return;
        }
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
            if (m.name.equals("AutoWalk")) mc.options.keyUp.setDown(false);
            if (m.name.equals("SafeWalk")) mc.options.keyShift.setDown(false);
            if (m.name.equals("Fly")) {
                var a = mc.player.getAbilities();
                boolean legit = mc.player.isCreative() || mc.player.isSpectator();
                a.mayfly = legit;
                if (!legit) a.flying = false;
                a.setFlyingSpeed(0.05f);
                mc.player.onUpdateAbilities();
            }
            if (m.name.equals("Fullbright")) clearFullbright(mc);
        }
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

        if (find("Session Info").enabled) {
            g.text(mc.font, "v" + VERSION + " / MC 26.3", 5, y, 0xFF8795A3, false); y += 10;
        }
        if (find("Coordinates").enabled) {
            g.text(mc.font, String.format(Locale.ROOT, "XYZ %.1f  %.1f  %.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("FPS").enabled) {
            g.text(mc.font, "FPS " + mc.getFps(), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Chunk Info").enabled) {
            int cx = Math.floorDiv((int) Math.floor(mc.player.getX()), 16);
            int cz = Math.floorDiv((int) Math.floor(mc.player.getZ()), 16);
            g.text(mc.font, "Chunk " + cx + ", " + cz, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Inventory Info").enabled) {
            var items = mc.player.getInventory().getNonEquipmentItems();
            int used = 0;
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
            Waypoint nearest = null;
            double best = Double.MAX_VALUE;
            for (Waypoint wp : WAYPOINTS.values()) {
                double dx = wp.x - mc.player.getX(), dy = wp.y - mc.player.getY(), dz = wp.z - mc.player.getZ();
                double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
                if (d < best) { best = d; nearest = wp; }
            }
            if (nearest != null) {
                g.text(mc.font, "WP " + nearest.name + " " + Math.round(best) + "m", 5, y, 0xFF9DD9FF, true); y += 11;
            }
        }
        if (find("Active Modules").enabled) {
            for (Mod m : MODS) if (m.enabled && !m.name.equals("Active Modules")) {
                g.text(mc.font, m.name, 5, y, 0xFF91BDD8, true); y += 10;
            }
        }
        if (!notificationText.isEmpty() && System.currentTimeMillis() < notificationUntil) {
            int x = Math.max(5, (g.guiWidth() - mc.font.width(notificationText)) / 2);
            g.text(mc.font, notificationText, x, 8, 0xFFFFFFFF, true);
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

    private static Mod find(String name) {
        for (Mod m : MODS) if (m.name.equalsIgnoreCase(name)) return m;
        return null;
    }

    private static String summary() {
        StringJoiner j = new StringJoiner(" | ");
        for (Mod m : MODS) j.add(m.name + ":" + (m.enabled ? "ON" : "OFF"));
        return j.toString();
    }

    private static String waypointSummary() {
        if (WAYPOINTS.isEmpty()) return "No waypoints saved";
        StringJoiner j = new StringJoiner(" | ");
        for (Waypoint w : WAYPOINTS.values()) j.add(w.name + " @ " + Math.round(w.x) + "," + Math.round(w.y) + "," + Math.round(w.z));
        return j.toString();
    }

    private static void load() {
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); } catch (Exception ignored) {}
        for (Mod m : MODS) {
            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, "false"));
            for (Setting s : m.settings) {
                String v = p.getProperty("setting." + m.name + "." + s.name);
                if (v == null) continue;
                try {
                    if (s instanceof BoolSetting b) b.value = Boolean.parseBoolean(v);
                    if (s instanceof NumSetting n) n.set(Double.parseDouble(v));
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
        try {
            Files.createDirectories(CONFIG.getParent());
            try (OutputStream out = Files.newOutputStream(CONFIG)) { p.store(out, "Eio Client " + VERSION); }
        } catch (Exception ignored) {}
    }

    private static abstract class Setting {
        final String name;
        Setting(String name) { this.name = name; }
    }

    private static final class BoolSetting extends Setting {
        boolean value;
        BoolSetting(String name, boolean value) { super(name); this.value = value; }
    }

    private static final class NumSetting extends Setting {
        double value, min, max, step;
        NumSetting(String name, double value, double min, double max, double step) {
            super(name); this.min = min; this.max = max; this.step = step; set(value);
        }
        void set(double v) {
            v = Math.max(min, Math.min(max, v));
            value = Math.round(v / step) * step;
            value = Math.max(min, Math.min(max, value));
        }
        String display() { return step < 0.1 ? String.format(Locale.ROOT, "%.2f", value) : String.format(Locale.ROOT, "%.1f", value); }
    }

    private static final class Mod {
        final String name, category, description;
        final int defaultKey;
        boolean enabled;
        KeyMapping bind;
        final List<Setting> settings = new ArrayList<>();
        Mod(String name, String category, String description, int defaultKey) {
            this.name = name; this.category = category; this.description = description; this.defaultKey = defaultKey;
        }
        Mod bool(String name, boolean value) { settings.add(new BoolSetting(name, value)); return this; }
        Mod num(String name, double value, double min, double max, double step) { settings.add(new NumSetting(name, value, min, max, step)); return this; }
        BoolSetting bool(String name) { for (Setting s : settings) if (s instanceof BoolSetting b && b.name.equals(name)) return b; throw new IllegalArgumentException(name); }
        NumSetting num(String name) { for (Setting s : settings) if (s instanceof NumSetting n && n.name.equals(name)) return n; throw new IllegalArgumentException(name); }
    }

    private static final class Waypoint {
        final String name; final double x, y, z;
        Waypoint(String name, double x, double y, double z) { this.name = name; this.x = x; this.y = y; this.z = z; }
    }

    public static final class ClickGui extends Screen {
        private static final String[] CATEGORIES = {"Combat", "Movement", "Player", "Render", "World", "Misc"};
        private String selectedCategory = "Combat";
        private Mod selectedMod;

        ClickGui() { super(Component.literal("Eio Client")); }
        @Override public boolean isPauseScreen() { return false; }
        @Override public void added() {
            super.added();
            guiOpen = true;
            guiLocalPrev = InputConstants.isKeyDown(InputConstants.KEY_RSHIFT);
        }
        @Override public void removed() {
            guiOpen = false;
            save();
            super.removed();
        }
        @Override public void onClose() {
            guiOpen = false;
            save();
            super.onClose();
        }
        @Override public void tick() {
            super.tick();
            boolean down = InputConstants.isKeyDown(InputConstants.KEY_RSHIFT);
            if (down && !guiLocalPrev) { onClose(); return; }
            guiLocalPrev = down;
        }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            g.fill(0, 0, width, height, 0x78070A0E);
            int bw = Math.min(760, width - 24), bh = Math.min(430, height - 24);
            int x = (width - bw) / 2, y = (height - bh) / 2;
            g.fill(x, y, x + bw, y + bh, 0xF3121720);
            g.fill(x, y, x + bw, y + 30, 0xFF171E29);
            g.fill(x, y, x + 2, y + bh, 0xFF4D9FCB);
            g.text(font, "Eio", x + 14, y + 10, 0xFF8CCDF2, true);
            g.text(font, VERSION, x + 37, y + 10, 0xFF687584, false);
            g.text(font, "Right Shift", x + bw - 70, y + 10, 0xFF596675, false);

            int side = 120, cy = y + 47;
            g.fill(x, y + 30, x + side, y + bh, 0xFF0D1118);
            for (String c : CATEGORIES) {
                boolean active = c.equals(selectedCategory), hover = in(mx, my, x + 7, cy - 5, side - 14, 22);
                if (active || hover) g.fill(x + 7, cy - 5, x + side - 7, cy + 17, active ? 0xFF183746 : 0xFF151C25);
                g.text(font, c, x + 16, cy + 2, active ? 0xFF8CCDF2 : 0xFFB7C0CA, false);
                cy += 27;
            }
            g.text(font, "Made by Eio", x + 13, y + bh - 17, 0xFF71808F, false);

            int lx = x + side + 13, ly = y + 45, lw = 235, ry = ly + 8;
            g.text(font, selectedCategory.toUpperCase(Locale.ROOT), lx, ly - 8, 0xFF738292, false);
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                boolean hover = in(mx, my, lx, ry, lw, 36), chosen = m == selectedMod;
                g.fill(lx, ry, lx + lw, ry + 32, chosen ? 0xFF1C3140 : (hover ? 0xFF1A222D : 0xFF141A22));
                if (m.enabled) g.fill(lx, ry, lx + 3, ry + 32, 0xFF55B7E8);
                g.text(font, m.name, lx + 9, ry + 7, m.enabled ? 0xFFFFFFFF : 0xFFD1D6DC, false);
                String state = m.enabled ? "ON" : "OFF";
                g.text(font, state, lx + lw - font.width(state) - 9, ry + 7, m.enabled ? 0xFF66D69B : 0xFF66717E, false);
                String key = m.bind == null || m.bind.isUnbound() ? "No bind" : m.bind.getTranslatedKeyMessage().getString();
                g.text(font, key, lx + 9, ry + 19, 0xFF6E8191, false);
                ry += 38;
            }

            int dx = lx + lw + 16, dw = x + bw - 13 - dx;
            g.fill(dx, ly, dx + dw, y + bh - 17, 0xFF0F141B);
            if (selectedMod == null) {
                g.text(font, "Select a module", dx + 16, ly + 17, 0xFFDCE4EB, false);
                g.text(font, "Left click toggles. Right click selects.", dx + 16, ly + 36, 0xFF71808F, false);
            } else {
                g.text(font, selectedMod.name, dx + 16, ly + 17, 0xFFFFFFFF, true);
                g.text(font, trim(selectedMod.description, 46), dx + 16, ly + 38, 0xFFAEB9C4, false);
                int sy = ly + 65;
                g.fill(dx + 16, sy, dx + dw - 16, sy + 27, selectedMod.enabled ? 0xFF176B4B : 0xFF26303B);
                g.centeredText(font, selectedMod.enabled ? "ENABLED" : "DISABLED", dx + dw / 2, sy + 9, 0xFFFFFFFF);
                sy += 34;
                g.fill(dx + 16, sy, dx + dw - 16, sy + 27, 0xFF1B2631);
                String bindText = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "KEYBIND: NONE" : "KEYBIND: " + selectedMod.bind.getTranslatedKeyMessage().getString();
                g.centeredText(font, bindText, dx + dw / 2, sy + 9, 0xFFDCE4EB);
                sy += 34;
                g.fill(dx + 16, sy, dx + dw - 16, sy + 25, 0xFF16212C);
                g.centeredText(font, "OPEN KEYBINDS", dx + dw / 2, sy + 8, 0xFF9DD9FF);
                sy += 34;

                for (Setting s : selectedMod.settings) {
                    if (s instanceof BoolSetting b) {
                        g.fill(dx + 16, sy, dx + dw - 16, sy + 25, 0xFF141B23);
                        g.text(font, b.name, dx + 24, sy + 8, 0xFFDCE4EB, false);
                        String v = b.value ? "ON" : "OFF";
                        g.text(font, v, dx + dw - 24 - font.width(v), sy + 8, b.value ? 0xFF66D69B : 0xFFCC6B6B, false);
                    } else if (s instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / (n.max - n.min);
                        int left = dx + 16, right = dx + dw - 16;
                        g.fill(left, sy, right, sy + 25, 0xFF141B23);
                        g.fill(left, sy + 22, left + (int) ((right - left) * ratio), sy + 25, 0xFF4D9FCB);
                        g.text(font, n.name, dx + 24, sy + 8, 0xFFDCE4EB, false);
                        String v = n.display();
                        g.text(font, v, dx + dw - 24 - font.width(v), sy + 8, 0xFF9DD9FF, false);
                    }
                    sy += 30;
                }
                if (selectedMod.name.equals("Waypoints")) {
                    g.text(font, "/eio waypoint add <name>", dx + 18, sy + 2, 0xFF71808F, false);
                    g.text(font, "/eio waypoint list", dx + 18, sy + 14, 0xFF71808F, false);
                }
            }
            super.extractRenderState(g, mx, my, delta);
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            int bw = Math.min(760, width - 24), bh = Math.min(430, height - 24);
            int x = (width - bw) / 2, y = (height - bh) / 2, cy = y + 47;
            boolean leftClick = e.button() == InputConstants.MOUSE_BUTTON_LEFT;
            boolean rightClick = e.button() == InputConstants.MOUSE_BUTTON_RIGHT;

            for (String c : CATEGORIES) {
                if (in(e.x(), e.y(), x + 7, cy - 5, 106, 22)) {
                    selectedCategory = c; selectedMod = null; return true;
                }
                cy += 27;
            }

            int lx = x + 133, ly = y + 45, ry = ly + 8, lw = 235;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                if (in(e.x(), e.y(), lx, ry, lw, 32)) {
                    selectedMod = m;
                    if (leftClick) toggle(m);
                    return true;
                }
                ry += 38;
            }

            if (selectedMod != null) {
                int dx = lx + lw + 16, dw = x + bw - 13 - dx, sy = ly + 65;
                if (leftClick && in(e.x(), e.y(), dx + 16, sy, dw - 32, 27)) {
                    toggle(selectedMod); return true;
                }
                sy += 34;
                sy += 34;
                if (leftClick && in(e.x(), e.y(), dx + 16, sy, dw - 32, 25)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 34;
                for (Setting s : selectedMod.settings) {
                    if (leftClick && in(e.x(), e.y(), dx + 16, sy, dw - 32, 25)) {
                        if (s instanceof BoolSetting b) b.value = !b.value;
                        if (s instanceof NumSetting n) {
                            double ratio = (e.x() - (dx + 16.0)) / Math.max(1.0, dw - 32.0);
                            n.set(n.min + Math.max(0.0, Math.min(1.0, ratio)) * (n.max - n.min));
                        }
                        save();
                        return true;
                    }
                    sy += 30;
                }
            }
            return super.mouseClicked(e, doubled);
        }

        private static boolean in(double mx, double my, int x, int y, int w, int h) {
            return mx >= x && mx < x + w && my >= y && my < y + h;
        }
        private static String trim(String s, int max) { return s.length() <= max ? s : s.substring(0, max - 1) + "…"; }
    }
}
