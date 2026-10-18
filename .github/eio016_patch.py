from pathlib import Path
import json

p = Path('eio26/EioClient.java')
s = p.read_text()

def rep(old: str, new: str, label: str) -> None:
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, 1)

rep('public static final String VERSION = "0.15.0";', 'public static final String VERSION = "0.16.0";', 'version')
rep('public static final String BUILD_ID = "EIO-015-QA2";', 'public static final String BUILD_ID = "EIO-016-QA1";', 'build id')

rep('''    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path CONFIG_BACKUP = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties.bak");
    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");''', '''    private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");
    private static final Path CONFIG_BACKUP = FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties.bak");
    private static final Path PROFILE_DIR = FabricLoader.getInstance().getConfigDir().resolve("eio").resolve("profiles");
    private static final Path DIAGNOSTIC_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-diagnostics.log");
    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");''', 'paths')

rep('''    private static String configSource = "defaults";
    private static final long sessionStartedNanos = System.nanoTime();''', '''    private static String configSource = "defaults";
    private static final ArrayDeque<Long> ATTACK_TIMES = new ArrayDeque<>();
    private static boolean runtimeSafeMode;
    private static int runtimeFaults;
    private static String lastRuntimeFault = "none";
    private static final long sessionStartedNanos = System.nanoTime();''', 'runtime fields')

rep('''        mod("Clock", "Render", "Shows your local 24-hour clock.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);''', '''        mod("Clock", "Render", "Shows your local 24-hour clock.", -1);
        mod("CPS", "Render", "Shows attacks performed by Eio during the last rolling second.", -1);
        mod("Keystrokes", "Render", "Shows live movement, jump and sprint input state.", -1);
        mod("Held Item", "Render", "Shows the selected item name and stack count.", -1);
        mod("Fullbright", "Render", "Uses a client night-vision effect without replacing an existing effect.", -1);''', 'render modules')

rep('''        ClientTickEvents.END_CLIENT_TICK.register(EioClient::tick);
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient", "hud"), EioClient::hud);''', '''        ClientTickEvents.END_CLIENT_TICK.register(EioClient::guardedTick);
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient", "hud"), EioClient::guardedHud);''', 'guard registrations')

rep('''                        .then(ClientCommands.literal("doctor").executes(c -> {
                            long bound = MODS.stream().filter(m -> m.bind != null && !m.bind.isUnbound()).count();
                            String report = validateModel() + " | Eio " + VERSION + " [" + BUILD_ID + "] | enabled=" + enabledCount()
                                    + " bound=" + bound + " | GUI=438x254 | config=" + configSource
                                    + " | backup=" + Files.exists(CONFIG_BACKUP);
                            c.getSource().sendFeedback(Component.literal(report));
                            return 1;
                        }))''', '''                        .then(ClientCommands.literal("doctor").executes(c -> {
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
                        }))''', 'doctor/selftest')

rep('''                        .then(ClientCommands.literal("reloadconfig").executes(c -> {
                            releaseRuntimeState(Minecraft.getInstance());
                            load();
                            c.getSource().sendFeedback(Component.literal("Eio config reloaded from " + configSource));
                            return 1;
                        }))''', '''                        .then(ClientCommands.literal("reloadconfig").executes(c -> {
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
                                })))''', 'recovery/profiles')

marker = '    private static void tick(Minecraft mc) {'
helpers = '''    private static void guardedTick(Minecraft mc) {
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
        String message = t.getMessage() == null ? "" : t.getMessage().replace('\\n', ' ').replace('\\r', ' ');
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

'''
rep(marker, helpers + marker, 'helpers')

rep('''        mc.gameMode.attack(mc.player, target);
        mc.player.swing(InteractionHand.MAIN_HAND, mc.player.getMainHandItem().getAttackAnimation(), true);''', '''        mc.gameMode.attack(mc.player, target);
        mc.player.swing(InteractionHand.MAIN_HAND, mc.player.getMainHandItem().getAttackAnimation(), true);
        long now = System.currentTimeMillis();
        ATTACK_TIMES.addLast(now);
        while (!ATTACK_TIMES.isEmpty() && ATTACK_TIMES.peekFirst() < now - 1000L) ATTACK_TIMES.removeFirst();''', 'attack cps')

rep('''    private static void resetAllSettings() {
        for (Mod m : MODS) for (Setting setting : m.settings) {
            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
        }
    }''', '''    private static void resetModuleSettings(Mod m) {
        for (Setting setting : m.settings) {
            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
        }
    }

    private static void resetAllSettings() {
        for (Mod m : MODS) resetModuleSettings(m);
    }''', 'reset helper')

rep('''        if (find("Clock").enabled) {
            g.text(mc.font, "Time " + LocalTime.now().format(CLOCK_FORMATTER), 5, y, 0xFFD9E0E6, true); y += 11;
        }
        if (find("Session Timer").enabled) {''', '''        if (find("Clock").enabled) {
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
        if (find("Session Timer").enabled) {''', 'hud modules')

rep('''    private static void load() {
        Properties p = new Properties();
        boolean loaded = false;
        configSource = "defaults";
        if (Files.exists(CONFIG)) {
            try (InputStream in = Files.newInputStream(CONFIG)) { p.load(in); loaded = true; configSource = "primary"; } catch (Exception ignored) {}
        }
        if (!loaded && Files.exists(CONFIG_BACKUP)) {
            p.clear();
            try (InputStream in = Files.newInputStream(CONFIG_BACKUP)) { p.load(in); loaded = true; configSource = "backup"; } catch (Exception ignored) { p.clear(); }
        }
        for (Mod m : MODS) {
            String enabledDefault = m.name.equals("Notifications") ? "true" : "false";
            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, enabledDefault));
            for (Setting s : m.settings) {
                if (s instanceof BoolSetting b) b.value = b.defaultValue;
                else if (s instanceof NumSetting n) n.set(n.defaultValue);
                String v = p.getProperty("setting." + m.name + "." + s.name);
                if (v == null) continue;
                try {
                    if (s instanceof BoolSetting b) b.value = Boolean.parseBoolean(v);
                    else if (s instanceof NumSetting n) n.set(Double.parseDouble(v));
                } catch (Exception ignored) {}
            }
        }
        WAYPOINTS.clear();
        for (String key : p.stringPropertyNames()) if (key.startsWith("wp.")) {
            String name = key.substring(3);
            try { String[] a = p.getProperty(key).split(","); if (a.length == 3) WAYPOINTS.put(name, new Waypoint(name, Double.parseDouble(a[0]), Double.parseDouble(a[1]), Double.parseDouble(a[2]))); } catch (Exception ignored) {}
        }
    }''', '''    private static void load() {
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
    }''', 'load refactor')

rep('''    private static void save() {
        Properties p = new Properties();
        for (Mod m : MODS) {
            p.setProperty("enabled." + m.name, Boolean.toString(m.enabled));
            for (Setting s : m.settings) {
                if (s instanceof BoolSetting b) p.setProperty("setting." + m.name + "." + s.name, Boolean.toString(b.value));
                if (s instanceof NumSetting n) p.setProperty("setting." + m.name + "." + s.name, Double.toString(n.value));
            }
        }
        p.setProperty("_schema", "3");
        p.setProperty("_lastVersion", VERSION);
        for (Waypoint w : WAYPOINTS.values()) p.setProperty("wp." + w.name, w.x + "," + w.y + "," + w.z);''', '''    private static void save() {
        Properties p = snapshotProperties();''', 'save refactor')

rep('''            String enabledStatus = enabledCount() + "/" + MODS.size();
            g.text(font, enabledStatus, x + 76, y + 7, 0xFF6F8898, false);''', '''            String enabledStatus = enabledCount() + "/" + MODS.size() + (runtimeSafeMode ? " SAFE" : "");
            g.text(font, enabledStatus, x + 76, y + 7, runtimeSafeMode ? 0xFFFFA071 : 0xFF6F8898, false);''', 'safe gui status')

rep('''                if (in(e.x(), e.y(), cx, cy, cardW, 20)) {
                    selectedMod = m;
                    if (leftClick) toggle(m);
                    return true;
                }''', '''                if (in(e.x(), e.y(), cx, cy, cardW, 20)) {
                    selectedMod = m;
                    if (leftClick) toggle(m);
                    else if (rightClick) {
                        resetModuleSettings(m);
                        save();
                        notifyMessage(m.name + " settings reset", 0xFF9DD9FF, 1800L);
                    }
                    return true;
                }''', 'module reset')

rep('String footerHelp = help + "  |  RMB setting = reset";', 'String footerHelp = help + "  |  RMB setting/module = reset";', 'footer help')

p.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.15.0+26.3' not in g:
    raise SystemExit('gradle version target not found')
gp.write_text(g.replace('mod_version=0.15.0+26.3', 'mod_version=0.16.0+26.3', 1))

lp = Path('src/main/resources/assets/eioclient/lang/en_us.json')
lang = json.loads(lp.read_text())
lang['key.eioclient.cps'] = 'CPS'
lang['key.eioclient.keystrokes'] = 'Keystrokes'
lang['key.eioclient.held_item'] = 'Held Item'
lp.write_text(json.dumps(lang, indent=2) + '\n')
