from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label} patch target not found')
    s = s.replace(old, new, 1)

replace_once('public static final String VERSION = "0.13.0";',
             'public static final String VERSION = "0.14.0";\n    public static final String BUILD_ID = "EIO-014-QA1";',
             'version/build id')

replace_once(
'''    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");''',
'''    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path CONFIG_BACKUP = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties.bak");
    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");''',
'config backup path')

replace_once('    private static int clickCooldown;', '    private static double clickAccumulator;', 'click accumulator')
replace_once(
'''    private static Entity followTarget;
    private static boolean jumpForced;''',
'''    private static Entity followTarget;
    private static boolean jumpForced;
    private static boolean sneakForced;
    private static final long sessionStartedNanos = System.nanoTime();''',
'runtime state')

replace_once(
'''        mod("SafeWalk", "Movement", "Automatically sneaks while moving on the ground to reduce edge falls.", -1);
        mod("Auto Jump", "Movement", "Jumps automatically when you run into a horizontal obstacle.", -1);''',
'''        mod("SafeWalk", "Movement", "Automatically sneaks while moving on the ground to reduce edge falls.", -1);
        mod("Auto Jump", "Movement", "Jumps automatically when you run into a horizontal obstacle.", -1);
        mod("Auto Swim", "Movement", "Holds jump while you are in water so swimming upward is effortless.", -1);''',
'auto swim module')

replace_once(
'''        mod("Target HUD", "Render", "Shows the current crosshair or Follow target and its distance.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);''',
'''        mod("Target HUD", "Render", "Shows the current crosshair or Follow target and its distance.", -1);
        mod("Health", "Render", "Shows current and maximum health on the HUD.", -1);
        mod("Speed", "Render", "Shows horizontal movement speed in blocks per second.", -1);
        mod("Facing", "Render", "Shows the cardinal direction you are facing.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);''',
'render telemetry modules')

replace_once(
'''        mod("Chunk Info", "World", "Shows your current chunk coordinates.", -1);
        mod("Waypoints", "World", "Shows your nearest saved waypoint and distance.", -1);''',
'''        mod("Chunk Info", "World", "Shows your current chunk coordinates.", -1);
        mod("World Time", "World", "Shows the current in-game world time as a 24-hour clock.", -1);
        mod("Waypoints", "World", "Shows your nearest saved waypoint and distance.", -1);''',
'world time module')

replace_once(
'''        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1);
        mod("Notifications", "Misc", "Shows a small upper-left card when modules are toggled.", -1)''',
'''        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1);
        mod("Session Timer", "Misc", "Shows how long the current Eio client session has been running.", -1);
        mod("Notifications", "Misc", "Shows a small upper-left card when modules are toggled.", -1)''',
'session timer module')

replace_once(
'''                            String report = "Eio " + VERSION + " | modules=" + MODS.size() + " enabled=" + enabled
                                    + " bound=" + bound + " | GUI=438x254 | config=" + CONFIG.toAbsolutePath();''',
'''                            String report = "Eio " + VERSION + " [" + BUILD_ID + "] | modules=" + MODS.size() + " enabled=" + enabled
                                    + " bound=" + bound + " | GUI=438x254 | config=" + CONFIG.toAbsolutePath()
                                    + " | backup=" + Files.exists(CONFIG_BACKUP);''',
'doctor build id')

replace_once(
'''        if (mc.player == null) {
            if (jumpForced) {
                mc.options.keyJump.setDown(false);
                jumpForced = false;
            }
            return;
        }''',
'''        if (mc.player == null) {
            if (jumpForced) {
                mc.options.keyJump.setDown(false);
                jumpForced = false;
            }
            if (sneakForced) {
                mc.options.keyShift.setDown(false);
                sneakForced = false;
            }
            return;
        }''',
'worldless forced input cleanup')

replace_once(
'''        Mod autoJump = find("Auto Jump");
        Mod respawn = find("Auto Respawn");''',
'''        Mod autoJump = find("Auto Jump");
        Mod autoSwim = find("Auto Swim");
        Mod respawn = find("Auto Respawn");''',
'auto swim tick lookup')

replace_once(
'''        if (safe.enabled) {
            boolean moving = mc.options.keyUp.isDown() || mc.options.keyDown.isDown()
                    || mc.options.keyLeft.isDown() || mc.options.keyRight.isDown();
            mc.options.keyShift.setDown(moving && mc.player.onGround());
        }''',
'''        boolean movingForSafeWalk = mc.options.keyUp.isDown() || mc.options.keyDown.isDown()
                || mc.options.keyLeft.isDown() || mc.options.keyRight.isDown();
        boolean shouldForceSneak = safe.enabled && movingForSafeWalk && mc.player.onGround();
        if (shouldForceSneak) {
            mc.options.keyShift.setDown(true);
            sneakForced = true;
        } else if (sneakForced) {
            mc.options.keyShift.setDown(false);
            sneakForced = false;
        }''',
'safe walk controlled sneak')

replace_once(
'''        if (clicker.enabled) {
            if (clickCooldown-- <= 0) {
                int cps = Math.max(1, (int) Math.round(clicker.num("CPS").value));
                clickCooldown = Math.max(1, (int) Math.round(20.0 / cps));
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
        } else clickCooldown = 0;''',
'''        if (clicker.enabled) {
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
        } else clickAccumulator = 0.0;''',
'precise clicker timing')

replace_once(
'''        boolean shouldForceJump = (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (test.enabled && testJumpTicks > 0);''',
'''        boolean shouldForceJump = (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater())
                || (test.enabled && testJumpTicks > 0);''',
'auto swim jump integration')

replace_once(
'''            if (m.name.equals("SafeWalk")) mc.options.keyShift.setDown(false);''',
'''            if (m.name.equals("SafeWalk") && sneakForced) {
                mc.options.keyShift.setDown(false);
                sneakForced = false;
            }
            if (m.name.equals("Auto Swim") && jumpForced) {
                mc.options.keyJump.setDown(false);
                jumpForced = false;
            }''',
'toggle forced input cleanup')

replace_once(
'''        if (find("FPS").enabled) { g.text(mc.font, "FPS " + mc.getFps(), 5, y, 0xFFD9E0E6, true); y += 11; }
        if (find("Chunk Info").enabled) {''',
'''        if (find("FPS").enabled) { g.text(mc.font, "FPS " + mc.getFps(), 5, y, 0xFFD9E0E6, true); y += 11; }
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
        if (find("Session Timer").enabled) {
            long seconds = Math.max(0L, (System.nanoTime() - sessionStartedNanos) / 1_000_000_000L);
            long hours = seconds / 3600L, minutes = (seconds % 3600L) / 60L, secs = seconds % 60L;
            g.text(mc.font, String.format(Locale.ROOT, "Session %02d:%02d:%02d", hours, minutes, secs), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Chunk Info").enabled) {''',
'hud telemetry')

replace_once(
'''        if (find("Chunk Info").enabled) {
            int cx = Math.floorDiv((int) Math.floor(mc.player.getX()), 16), cz = Math.floorDiv((int) Math.floor(mc.player.getZ()), 16);
            g.text(mc.font, "Chunk " + cx + ", " + cz, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Inventory Info").enabled) {''',
'''        if (find("Chunk Info").enabled) {
            int cx = Math.floorDiv((int) Math.floor(mc.player.getX()), 16), cz = Math.floorDiv((int) Math.floor(mc.player.getZ()), 16);
            g.text(mc.font, "Chunk " + cx + ", " + cz, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("World Time").enabled && mc.level != null) {
            long ticks = Math.floorMod(mc.level.getDayTime(), 24000L);
            long totalMinutes = (ticks * 60L / 1000L + 360L) % 1440L;
            g.text(mc.font, String.format(Locale.ROOT, "World %02d:%02d", totalMinutes / 60L, totalMinutes % 60L), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Inventory Info").enabled) {''',
'world time hud')

# Recover from a damaged primary config using the last good backup.
replace_once(
'''    private static void load() {
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); } catch (Exception ignored) {}''',
'''    private static void load() {
        Properties p = new Properties();
        boolean loaded = false;
        if (Files.exists(CONFIG)) {
            try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); loaded = true; } catch (Exception ignored) {}
        }
        if (!loaded && Files.exists(CONFIG_BACKUP)) {
            p.clear();
            try (InputStream in = Files.newInputStream(CONFIG_BACKUP)) { p.load(in); } catch (Exception ignored) { p.clear(); }
        }''',
'config recovery')

replace_once(
'''        for (Waypoint w : WAYPOINTS.values()) p.setProperty("wp." + w.name, w.x + "," + w.y + "," + w.z);
        try {
            Files.createDirectories(CONFIG.getParent());
            Path tmp = CONFIG.resolveSibling(CONFIG.getFileName().toString() + ".tmp");''',
'''        p.setProperty("_schema", "2");
        p.setProperty("_lastVersion", VERSION);
        for (Waypoint w : WAYPOINTS.values()) p.setProperty("wp." + w.name, w.x + "," + w.y + "," + w.z);
        try {
            Files.createDirectories(CONFIG.getParent());
            if (Files.exists(CONFIG)) {
                try { Files.copy(CONFIG, CONFIG_BACKUP, StandardCopyOption.REPLACE_EXISTING); } catch (Exception ignored) {}
            }
            Path tmp = CONFIG.resolveSibling(CONFIG.getFileName().toString() + ".tmp");''',
'config backup save')

# Settings remember defaults so right-click can reset one setting instantly.
replace_once(
'''    private static final class BoolSetting extends Setting {
        boolean value;
        BoolSetting(String name, boolean value, String description) { super(name, description); this.value = value; }
    }
    private static final class NumSetting extends Setting {
        double value, min, max, step;
        NumSetting(String name, double value, double min, double max, double step, String description) { super(name, description); this.min = min; this.max = max; this.step = step; set(value); }''',
'''    private static final class BoolSetting extends Setting {
        final boolean defaultValue;
        boolean value;
        BoolSetting(String name, boolean value, String description) { super(name, description); this.defaultValue = value; this.value = value; }
    }
    private static final class NumSetting extends Setting {
        final double defaultValue;
        double value, min, max, step;
        NumSetting(String name, double value, double min, double max, double step, String description) { super(name, description); this.defaultValue = value; this.min = min; this.max = max; this.step = step; set(value); }''',
'setting defaults')

# Show changed-setting markers and document right-click reset in the compact help footer.
s = s.replace('String value = b.value ? "ON" : "OFF";\n                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 5, b.value ? 0xFF69D99B : 0xFFC87575, false);',
'''String value = (b.value ? "ON" : "OFF") + (b.value != b.defaultValue ? "*" : "");
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 5, b.value ? 0xFF69D99B : 0xFFC87575, false);''')
s = s.replace('String value = n.display();\n                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 3, 0xFF9DD9FF, false);',
'''String value = n.display() + (Math.abs(n.value - n.defaultValue) > 1.0E-9 ? "*" : "");
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 3, 0xFF9DD9FF, false);''')
replace_once(
'''            g.text(font, trim(help, 66), x + 11, footerY + 5, 0xFF82909B, false);''',
'''            String footerHelp = help + "  |  RMB setting = reset";
            g.text(font, trim(footerHelp, 66), x + 11, footerY + 5, 0xFF82909B, false);''',
'footer reset hint')

# Mouse interaction: left-click edits/toggles; right-click selects modules or resets individual settings.
replace_once(
'''        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            if (e.button() != InputConstants.MOUSE_BUTTON_LEFT) return super.mouseClicked(e, doubled);

            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();''',
'''        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            boolean leftClick = e.button() == InputConstants.MOUSE_BUTTON_LEFT;
            boolean rightClick = e.button() == InputConstants.MOUSE_BUTTON_RIGHT;
            if (!leftClick && !rightClick) return super.mouseClicked(e, doubled);

            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();''',
'mouse buttons')

replace_once(
'''                if (in(e.x(), e.y(), cx, cy, cardW, 20)) {
                    selectedMod = m;
                    toggle(m);
                    return true;
                }''',
'''                if (in(e.x(), e.y(), cx, cy, cardW, 20)) {
                    selectedMod = m;
                    if (leftClick) toggle(m);
                    return true;
                }''',
'module select/toggle')

replace_once(
'''                if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                    toggle(selectedMod);
                    return true;
                }''',
'''                if (leftClick && in(e.x(), e.y(), sx, sy, sw, 18)) {
                    toggle(selectedMod);
                    return true;
                }''',
'header left toggle')

replace_once(
'''                if (in(e.x(), e.y(), sx, sy, sw, 17)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }''',
'''                if (leftClick && in(e.x(), e.y(), sx, sy, sw, 17)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }''',
'keybind left open')

replace_once(
'''                    if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                        if (setting instanceof BoolSetting b) {
                            b.value = !b.value;
                        } else if (setting instanceof NumSetting n) {
                            double ratio = (e.x() - (sx + 4.0)) / Math.max(1.0, sw - 8.0);
                            ratio = Math.max(0.0, Math.min(1.0, ratio));
                            n.set(n.min + ratio * (n.max - n.min));
                        }
                        save();
                        return true;
                    }''',
'''                    if (in(e.x(), e.y(), sx, sy, sw, 18)) {
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
                    }''',
'setting right reset')

p.write_text(s)
print('EioClient 0.14.0 quality/regression patch applied')
