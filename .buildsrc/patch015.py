from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label} patch target not found')
    s = s.replace(old, new, 1)

replace_once('public static final String VERSION = "0.14.0";\n    public static final String BUILD_ID = "EIO-014-QA1";',
             'public static final String VERSION = "0.15.0";\n    public static final String BUILD_ID = "EIO-015-QA1";',
             'version/build id')

replace_once('import java.time.Instant;\nimport java.util.*;',
             'import java.time.Instant;\nimport java.time.LocalTime;\nimport java.time.format.DateTimeFormatter;\nimport java.util.*;',
             'time imports')

replace_once('''    private static final List<Mod> MODS = new ArrayList<>();
    private static final Map<String, Waypoint> WAYPOINTS = new LinkedHashMap<>();''',
'''    private static final List<Mod> MODS = new ArrayList<>();
    private static final Map<String, Mod> MOD_INDEX = new LinkedHashMap<>();
    private static final Map<String, Waypoint> WAYPOINTS = new LinkedHashMap<>();''',
'module index')

replace_once('''    private static boolean jumpForced;
    private static boolean sneakForced;
    private static final long sessionStartedNanos = System.nanoTime();''',
'''    private static boolean jumpForced;
    private static boolean sneakForced;
    private static boolean forwardForced;
    private static boolean flyForced;
    private static boolean flyPrevMayfly;
    private static boolean flyPrevFlying;
    private static boolean lowHealthAlerted;
    private static int lowHealthCooldown;
    private static String configSource = "defaults";
    private static final long sessionStartedNanos = System.nanoTime();
    private static final DateTimeFormatter CLOCK_FORMATTER = DateTimeFormatter.ofPattern("HH:mm:ss", Locale.ROOT);''',
'runtime quality state')

replace_once('''                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.");''',
'''                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.");''',
'auto clicker require attack')

replace_once('''        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
        mod("Inventory Info", "Player", "Shows occupied inventory slots on the HUD.", -1);
        mod("Durability HUD", "Player", "Shows durability of the selected item.", -1);''',
'''        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
        mod("Low Health Alert", "Player", "Shows an urgent HUD alert when your health drops below a configurable threshold.", -1)
                .num("Threshold", 6.0, 1.0, 20.0, 0.5, "Health value that triggers the warning.")
                .num("Cooldown", 10.0, 2.0, 60.0, 1.0, "Minimum seconds between repeated low-health warnings.");
        mod("Inventory Info", "Player", "Shows occupied inventory slots on the HUD.", -1);
        mod("Durability HUD", "Player", "Shows durability of the selected item.", -1);''',
'low health module')

replace_once('''        mod("Coordinates", "Render", "Shows your XYZ position.", -1);
        mod("FPS", "Render", "Shows current FPS.", -1);
        mod("Active Modules", "Render", "Lists enabled modules on the HUD.", -1);''',
'''        mod("Coordinates", "Render", "Shows your XYZ position.", -1)
                .num("Decimals", 1.0, 0.0, 3.0, 1.0, "Number of decimal places used for coordinates.");
        mod("FPS", "Render", "Shows current FPS.", -1);
        mod("Active Modules", "Render", "Lists enabled modules on the HUD.", -1)
                .num("Max", 12.0, 3.0, 20.0, 1.0, "Maximum number of enabled modules shown before collapsing the rest.");''',
'render controls')

replace_once('''        mod("Facing", "Render", "Shows the cardinal direction you are facing.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);''',
'''        mod("Facing", "Render", "Shows the cardinal direction you are facing.", -1);
        mod("Rotation", "Render", "Shows your current yaw and pitch.", -1);
        mod("Memory", "Render", "Shows JVM memory currently used by Minecraft.", -1);
        mod("Clock", "Render", "Shows your local 24-hour clock.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);''',
'advanced render telemetry')

replace_once('''        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1);
        mod("Session Timer", "Misc", "Shows how long the current Eio client session has been running.", -1);
        mod("Notifications", "Misc", "Shows a small upper-left card when modules are toggled.", -1)
                .num("Seconds", 2.0, 0.5, 5.0, 0.5, "How long toggle notifications remain visible.");''',
'''        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1)
                .bool("Build ID", false, "Also show the exact Eio QA build identifier.");
        mod("Session Timer", "Misc", "Shows how long the current Eio client session has been running.", -1);
        mod("Notifications", "Misc", "Shows a small upper-left card when modules are toggled.", -1)
                .num("Seconds", 2.0, 0.5, 5.0, 0.5, "How long toggle notifications remain visible.")
                .bool("Show Disable", true, "Show notifications when a module is disabled as well as enabled.");''',
'misc controls')

replace_once('''    private static Mod mod(String name, String category, String description, int defaultKey) {
        Mod m = new Mod(name, category, description, defaultKey);
        MODS.add(m);
        return m;
    }''',
'''    private static Mod mod(String name, String category, String description, int defaultKey) {
        Mod m = new Mod(name, category, description, defaultKey);
        String indexKey = name.toLowerCase(Locale.ROOT);
        if (MOD_INDEX.putIfAbsent(indexKey, m) != null) throw new IllegalStateException("Duplicate module: " + name);
        MODS.add(m);
        return m;
    }''',
'indexed module registration')

replace_once('''    public void onInitializeClient() {
        load();''',
'''    public void onInitializeClient() {
        validateModel();
        load();''',
'startup model validation')

replace_once('''                        .then(ClientCommands.literal("doctor").executes(c -> {
                            long enabled = MODS.stream().filter(m -> m.enabled).count();
                            long bound = MODS.stream().filter(m -> m.bind != null && !m.bind.isUnbound()).count();
                            String report = "Eio " + VERSION + " [" + BUILD_ID + "] | modules=" + MODS.size() + " enabled=" + enabled
                                    + " bound=" + bound + " | GUI=438x254 | config=" + CONFIG.toAbsolutePath()
                                    + " | backup=" + Files.exists(CONFIG_BACKUP);
                            c.getSource().sendFeedback(Component.literal(report));
                            return 1;
                        }))''',
'''                        .then(ClientCommands.literal("doctor").executes(c -> {
                            long bound = MODS.stream().filter(m -> m.bind != null && !m.bind.isUnbound()).count();
                            String report = validateModel() + " | Eio " + VERSION + " [" + BUILD_ID + "] | enabled=" + enabledCount()
                                    + " bound=" + bound + " | GUI=438x254 | config=" + configSource
                                    + " | backup=" + Files.exists(CONFIG_BACKUP);
                            c.getSource().sendFeedback(Component.literal(report));
                            return 1;
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
                        }))''',
'diagnostics and recovery commands')

replace_once('''        if (mc.player == null) {
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
'''        if (mc.player == null) {
            if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
            if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
            if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
            followTarget = null;
            flyForced = false;
            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            return;
        }''',
'worldless owned-input cleanup')

replace_once('''        Mod respawn = find("Auto Respawn");
        Mod clicker = find("Auto Clicker");''',
'''        Mod respawn = find("Auto Respawn");
        Mod lowHealth = find("Low Health Alert");
        Mod clicker = find("Auto Clicker");''',
'low health lookup')

old_movement = '''        if (walk.enabled) mc.options.keyUp.setDown(true);
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
        // Jump forcing is resolved after Test Profile updates so ordinary Space input is not cancelled globally.

        if (follow.enabled) runFollow(mc, follow);

        if (fly.enabled) {
            var a = mc.player.getAbilities();
            a.mayfly = true;
            a.flying = true;
            a.setFlyingSpeed((float) fly.num("Speed").value);
        }
        if (respawn.enabled && mc.player.isDeadOrDying()) mc.player.respawn();'''
new_movement = '''        boolean shouldForceForward = walk.enabled;
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
        }'''
replace_once(old_movement, new_movement, 'owned movement and safety runtime')

replace_once('''        if (clicker.enabled) {
            double cps = Math.max(1.0, Math.min(20.0, clicker.num("CPS").value));''',
'''        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();
        if (clicker.enabled && clickAllowed) {
            double cps = Math.max(1.0, Math.min(20.0, clicker.num("CPS").value));''',
'auto clicker activation guard')

old_follow = '''    private static void runFollow(Minecraft mc, Mod follow) {
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
    }'''
new_follow = '''    private static boolean runFollow(Minecraft mc, Mod follow) {
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
    }'''
replace_once(old_follow, new_follow, 'follow input ownership')

old_toggle_cleanup = '''            if (m.name.equals("AutoWalk") && !find("Follow").enabled) mc.options.keyUp.setDown(false);
            if (m.name.equals("Follow") && !find("AutoWalk").enabled) mc.options.keyUp.setDown(false);
            if (m.name.equals("SafeWalk") && sneakForced) {
                mc.options.keyShift.setDown(false);
                sneakForced = false;
            }
            if (m.name.equals("Auto Swim") && jumpForced) {
                mc.options.keyJump.setDown(false);
                jumpForced = false;
            }
            if (m.name.equals("Auto Jump")) mc.options.keyJump.setDown(false);
            if (m.name.equals("Fly")) {
                var a = mc.player.getAbilities();
                boolean legit = mc.player.isCreative() || mc.player.isSpectator();
                a.mayfly = legit;
                if (!legit) a.flying = false;
                a.setFlyingSpeed(0.05f);
                mc.player.onUpdateAbilities();
            }'''
new_toggle_cleanup = '''            if ((m.name.equals("AutoWalk") || m.name.equals("Follow"))
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
            }'''
replace_once(old_toggle_cleanup, new_toggle_cleanup, 'toggle cleanup ownership')

insert_before_notify = '''    private static void notifyToggle(Mod m) {'''
helpers = '''    private static void restoreFly(Minecraft mc) {
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

    private static void resetAllSettings() {
        for (Mod m : MODS) for (Setting setting : m.settings) {
            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
        }
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

'''
if insert_before_notify not in s:
    raise SystemExit('notification helper insertion target not found')
s = s.replace(insert_before_notify, helpers + insert_before_notify, 1)

replace_once('''    private static void notifyToggle(Mod m) {
        Mod n = find("Notifications");
        if (n == null || !n.enabled) return;
        notificationText = m.name + (m.enabled ? " enabled" : " disabled");
        notificationUntil = System.currentTimeMillis() + (long) (n.num("Seconds").value * 1000.0);
    }''',
'''    private static void notifyToggle(Mod m) {
        Mod n = find("Notifications");
        if (n == null || !n.enabled) return;
        if (!m.enabled && !n.bool("Show Disable").value) return;
        notifyMessage(m.name + (m.enabled ? " enabled" : " disabled"), m.enabled ? 0xFF66D69B : 0xFFCC6B6B,
                (long) (n.num("Seconds").value * 1000.0));
    }''',
'notification options')

replace_once('''        if (find("Session Info").enabled) { g.text(mc.font, "v" + VERSION + " / MC 26.3", 5, y, 0xFF8795A3, false); y += 10; }
        if (find("Coordinates").enabled) { g.text(mc.font, String.format(Locale.ROOT, "XYZ %.1f  %.1f  %.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()), 5, y, 0xFFD9E0E6, true); y += 11; }''',
'''        if (find("Session Info").enabled) {
            String info = "v" + VERSION + " / MC 26.3";
            if (find("Session Info").bool("Build ID").value) info += " / " + BUILD_ID;
            g.text(mc.font, info, 5, y, 0xFF8795A3, false); y += 10;
        }
        if (find("Coordinates").enabled) {
            int decimals = (int) Math.round(find("Coordinates").num("Decimals").value);
            String format = "XYZ %." + decimals + "f  %." + decimals + "f  %." + decimals + "f";
            g.text(mc.font, String.format(Locale.ROOT, format, mc.player.getX(), mc.player.getY(), mc.player.getZ()), 5, y, 0xFFD9E0E6, true); y += 11;
        }''',
'hud session and coordinate controls')

replace_once('''        if (find("Facing").enabled) {
            int dir = Math.floorMod((int) Math.floor((mc.player.getYRot() + 45.0f) / 90.0f), 4);
            String facing = switch (dir) { case 0 -> "South"; case 1 -> "West"; case 2 -> "North"; default -> "East"; };
            g.text(mc.font, "Facing " + facing, 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Session Timer").enabled) {''',
'''        if (find("Facing").enabled) {
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
        if (find("Session Timer").enabled) {''',
'advanced telemetry hud')

replace_once('''        if (find("Active Modules").enabled) {
            for (Mod m : MODS) if (m.enabled && !m.name.equals("Active Modules")) { g.text(mc.font, m.name, 5, y, 0xFF91BDD8, true); y += 10; }
        }
        if (!notificationText.isEmpty() && System.currentTimeMillis() < notificationUntil) {
            int ny = Math.max(18, y + 2), boxW = mc.font.width(notificationText) + 12;
            int color = notificationText.endsWith("enabled") ? 0xFF66D69B : 0xFFCC6B6B;
            g.fill(3, ny - 3, 3 + boxW, ny + 11, 0xB8121720);
            g.text(mc.font, notificationText, 9, ny, color, true);
        }''',
'''        if (find("Active Modules").enabled) {
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
        }''',
'active module cap and notification color')

replace_once('''    private static Mod find(String name) { for (Mod m : MODS) if (m.name.equalsIgnoreCase(name)) return m; return null; }''',
'''    private static Mod find(String name) { return name == null ? null : MOD_INDEX.get(name.toLowerCase(Locale.ROOT)); }''',
'indexed find')

replace_once('''    private static void load() {
        Properties p = new Properties();
        boolean loaded = false;
        if (Files.exists(CONFIG)) {
            try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); loaded = true; } catch (Exception ignored) {}
        }
        if (!loaded && Files.exists(CONFIG_BACKUP)) {
            p.clear();
            try (InputStream in = Files.newInputStream(CONFIG_BACKUP)) { p.load(in); } catch (Exception ignored) { p.clear(); }
        }''',
'''    private static void load() {
        Properties p = new Properties();
        boolean loaded = false;
        configSource = "defaults";
        if (Files.exists(CONFIG)) {
            try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); loaded = true; configSource = "primary"; } catch (Exception ignored) {}
        }
        if (!loaded && Files.exists(CONFIG_BACKUP)) {
            p.clear();
            try (InputStream in = Files.newInputStream(CONFIG_BACKUP)) { p.load(in); loaded = true; configSource = "backup"; } catch (Exception ignored) { p.clear(); }
        }''',
'config source diagnostics')

replace_once('''        p.setProperty("_schema", "2");''', '        p.setProperty("_schema", "3");', 'config schema')

replace_once('''            g.text(font, VERSION, x + 31, y + 7, 0xFF64727E, false);
            String closeHint = "RSHIFT";''',
'''            g.text(font, VERSION, x + 31, y + 7, 0xFF64727E, false);
            String enabledStatus = enabledCount() + "/" + MODS.size();
            g.text(font, enabledStatus, x + 76, y + 7, 0xFF6F8898, false);
            String closeHint = "RSHIFT";''',
'gui live module status')

p.write_text(s)
print('EioClient 0.15.0 advanced quality patch applied')
