from pathlib import Path
import re

p = Path('eio26/EioClient.java')
s = p.read_text()

def rep(old: str, new: str, label: str) -> None:
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, 1)

rep('public static final String VERSION = "0.16.0";', 'public static final String VERSION = "0.17.0";', 'version')
rep('public static final String BUILD_ID = "EIO-016-QA2";', 'public static final String BUILD_ID = "EIO-017-QA1";', 'build id')
rep('GUI=438x254', 'GUI=690x390', 'doctor gui size')

formatter = '    private static final DateTimeFormatter CLOCK_FORMATTER = DateTimeFormatter.ofPattern("HH:mm:ss", Locale.ROOT);'
mob_ids = '''    private static final String[] FOLLOW_MOB_IDS = {
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
    };'''
rep(formatter, formatter + '\n' + mob_ids, 'mob id catalog')

old_follow = '''        mod("Follow", "Movement", "Follows a selected or nearby living entity while keeping a configurable distance.", InputConstants.KEY_H)
                .num("Search Range", 24.0, 4.0, 64.0, 1.0, "Maximum distance used when finding a follow target.")
                .num("Distance", 3.0, 1.0, 12.0, 0.5, "Distance to maintain behind the follow target.")
                .bool("Players", true, "Allow following players.")
                .bool("Mobs", true, "Allow following non-player living entities.")
                .bool("Face Target", true, "Turn your view toward the follow target.")
                .bool("Sprint", true, "Sprint while closing distance to the target.");'''
new_follow = '''        mod("Follow", "Movement", "Follows the nearest allowed player or selected mob type while keeping a configurable distance.", InputConstants.KEY_H)
                .num("Search Range", 24.0, 4.0, 64.0, 1.0, "Maximum distance used when finding a follow target.")
                .num("Distance", 3.0, 1.0, 12.0, 0.5, "Distance to maintain behind the follow target.")
                .bool("Players", true, "Allow following players.")
                .bool("Mobs", true, "Master switch for following non-player living entities.")
                .bool("Face Target", true, "Turn your view toward the follow target.")
                .bool("Sprint", true, "Sprint while closing distance to the target.")
                .mobList("Mob Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Follow is allowed to target.");'''
rep(old_follow, new_follow, 'follow module')

rep('''                if (setting instanceof BoolSetting b) p.setProperty("setting." + m.name + "." + setting.name, Boolean.toString(b.value));
                else if (setting instanceof NumSetting n) p.setProperty("setting." + m.name + "." + setting.name, Double.toString(n.value));''', '''                if (setting instanceof BoolSetting b) p.setProperty("setting." + m.name + "." + setting.name, Boolean.toString(b.value));
                else if (setting instanceof NumSetting n) p.setProperty("setting." + m.name + "." + setting.name, Double.toString(n.value));
                else if (setting instanceof MobListSetting ml) p.setProperty("mobfilter." + m.name + "." + setting.name, ml.disabledCsv());''', 'snapshot mob filter')

rep('''                if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                String v = p.getProperty("setting." + m.name + "." + setting.name);
                if (v == null) continue;
                try {
                    if (setting instanceof BoolSetting b) b.value = Boolean.parseBoolean(v);
                    else if (setting instanceof NumSetting n) n.set(Double.parseDouble(v));
                } catch (Exception ignored) {}''', '''                if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                else if (setting instanceof MobListSetting ml) ml.reset();
                if (setting instanceof MobListSetting ml) {
                    ml.loadDisabledCsv(p.getProperty("mobfilter." + m.name + "." + setting.name, ""));
                    continue;
                }
                String v = p.getProperty("setting." + m.name + "." + setting.name);
                if (v == null) continue;
                try {
                    if (setting instanceof BoolSetting b) b.value = Boolean.parseBoolean(v);
                    else if (setting instanceof NumSetting n) n.set(Double.parseDouble(v));
                } catch (Exception ignored) {}''', 'load mob filter')

rep('''            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
            else if (setting instanceof NumSetting n) n.set(n.defaultValue);''', '''            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
            else if (setting instanceof MobListSetting ml) ml.reset();''', 'reset mob filter')

follow_pattern = re.compile(r'    private static boolean runFollow\(Minecraft mc, Mod follow\) \{.*?\n    \}\n\n    private static void runTestProfile', re.S)
new_run_follow = '''    private static boolean validFollowTarget(Minecraft mc, Mod follow, Entity target) {
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

    private static void runTestProfile'''
s, count = follow_pattern.subn(new_run_follow, s, count=1)
if count != 1:
    raise SystemExit('runFollow replacement failed')

old_classes = '''    private static final class NumSetting extends Setting {
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
    }'''
new_classes = '''    private static final class NumSetting extends Setting {
        final double defaultValue;
        double value, min, max, step;
        NumSetting(String name, double value, double min, double max, double step, String description) { super(name, description); this.defaultValue = value; this.min = min; this.max = max; this.step = step; set(value); }
        void set(double v) { v = Math.max(min, Math.min(max, v)); value = Math.round(v / step) * step; value = Math.max(min, Math.min(max, value)); }
        String display() { return step < 0.1 ? String.format(Locale.ROOT, "%.2f", value) : String.format(Locale.ROOT, "%.1f", value); }
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
        BoolSetting bool(String name) { for (Setting s : settings) if (s instanceof BoolSetting b && b.name.equals(name)) return b; throw new IllegalArgumentException(name); }
        NumSetting num(String name) { for (Setting s : settings) if (s instanceof NumSetting n && n.name.equals(name)) return n; throw new IllegalArgumentException(name); }
        MobListSetting mobList(String name) { for (Setting s : settings) if (s instanceof MobListSetting ml && ml.name.equals(name)) return ml; throw new IllegalArgumentException(name); }
    }'''
rep(old_classes, new_classes, 'setting classes')

marker = '    public static final class ClickGui extends Screen {'
pos = s.find(marker)
if pos < 0:
    raise SystemExit('ClickGui marker not found')

new_gui = r'''    public static final class ClickGui extends Screen {
        private static final String[] CATEGORIES = {"Combat", "Movement", "Player", "Render", "World", "Testing", "Misc"};
        private static final int MOB_PAGE_SIZE = 8;
        private String selectedCategory = "Combat";
        private Mod selectedMod;
        private int mobPage;

        ClickGui() { super(Component.literal("Eio Client")); }
        @Override public boolean isPauseScreen() { return false; }
        @Override public void added() { super.added(); guiOpen = true; if (selectedMod == null) selectedMod = firstInCategory(selectedCategory); }
        @Override public void removed() { guiOpen = false; save(); super.removed(); }
        @Override public void onClose() { guiOpen = false; save(); super.onClose(); }

        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (m.category.equals(category)) return m;
            return null;
        }

        private int panelW() { return Math.max(430, Math.min(690, width - 18)); }
        private int panelH() { return Math.max(270, Math.min(390, height - 18)); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }
        private int categoryCount(String category) { int count = 0; for (Mod m : MODS) if (m.category.equals(category)) count++; return count; }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int accent = categoryColor(selectedCategory);
            String help = selectedMod == null ? "Choose a module" : selectedMod.description;

            g.fill(0, 0, width, height, 0x18000000);
            g.fill(x + 5, y + 7, x + bw + 5, y + bh + 7, 0x30000000);
            g.fill(x, y, x + bw, y + bh, 0xE0090E14);
            g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x80131A22);
            g.fill(x, y, x + bw, y + 31, 0xEE0C131B);
            g.fill(x, y + 30, x + bw, y + 31, 0x66405260);
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
            int railX = x + 10, railW = 98;
            int modsX = railX + railW + 8, modsW = Math.min(198, Math.max(154, bw / 3 - 22));
            int detailX = modsX + modsW + 8;
            int detailW = x + bw - 10 - detailX;

            g.fill(railX, bodyY, railX + railW, footerY - 6, 0x5610171F);
            g.fill(modsX, bodyY, modsX + modsW, footerY - 6, 0x4210171F);
            g.fill(detailX, bodyY, detailX + detailW, footerY - 6, 0x5210171F);

            g.text(font, "CATEGORIES", railX + 8, bodyY + 8, 0xFF61717E, false);
            int cy = bodyY + 23;
            for (String category : CATEGORIES) {
                boolean active = category.equals(selectedCategory);
                boolean hover = in(mx, my, railX + 5, cy, railW - 10, 25);
                if (hover || active) g.fill(railX + 5, cy, railX + railW - 5, cy + 25, active ? 0x8A1B2731 : 0x4518232C);
                if (active) g.fill(railX + 5, cy + 5, railX + 8, cy + 20, accent);
                g.text(font, shortCat(category), railX + 14, cy + 8, active ? 0xFFF3F7FA : 0xFFAAB5BD, active);
                String count = Integer.toString(categoryCount(category));
                g.text(font, count, railX + railW - font.width(count) - 12, cy + 8, active ? accent : 0xFF596873, false);
                if (hover) help = "Open " + category + " modules";
                cy += 28;
            }

            g.text(font, selectedCategory.toUpperCase(Locale.ROOT), modsX + 8, bodyY + 8, accent, true);
            int myCard = bodyY + 23;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                boolean selected = m == selectedMod;
                boolean hover = in(mx, my, modsX + 5, myCard, modsW - 10, 20);
                g.fill(modsX + 5, myCard, modsX + modsW - 5, myCard + 20,
                        selected ? 0x8D1D2A34 : (hover ? 0x5618232C : 0x2411161C));
                if (selected) g.fill(modsX + 5, myCard, modsX + 7, myCard + 20, accent);
                g.fill(modsX + 12, myCard + 8, modsX + 16, myCard + 12, m.enabled ? 0xFF6FE0A5 : 0xFF55636D);
                g.text(font, trim(m.name, Math.max(10, (modsW - 49) / 6)), modsX + 22, myCard + 6,
                        selected ? 0xFFF2F6F8 : 0xFFC2CCD3, false);
                String state = m.enabled ? "ON" : "";
                if (!state.isEmpty()) g.text(font, state, modsX + modsW - font.width(state) - 11, myCard + 6, 0xFF77DDA9, false);
                if (hover) help = m.description;
                myCard += 22;
            }

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
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        help = renderMobSelector(g, mx, my, sx, sy, sw, Math.max(64, footerY - 9 - sy), ml, help, accent);
                        break;
                    }
                    boolean hover = in(mx, my, sx, sy, sw, 22);
                    g.fill(sx, sy, sx + sw, sy + 22, hover ? 0x571A252E : 0x2911161C);
                    if (setting instanceof BoolSetting b) {
                        g.text(font, trim(b.name, 18), sx + 7, sy + 7, 0xFFD4DCE2, false);
                        int tx = sx + sw - 34;
                        g.fill(tx, sy + 5, tx + 28, sy + 17, b.value ? 0xA9347459 : 0x60424A51);
                        int kx = b.value ? tx + 17 : tx + 3;
                        g.fill(kx, sy + 7, kx + 8, sy + 15, b.value ? 0xFFF1FFF7 : 0xFFB9C1C7);
                    } else if (setting instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        g.text(font, trim(n.name, 15), sx + 7, sy + 5, 0xFFD4DCE2, false);
                        String value = n.display() + (Math.abs(n.value - n.defaultValue) > 1.0E-9 ? "*" : "");
                        g.text(font, value, sx + sw - font.width(value) - 7, sy + 5, 0xFF9DDCFA, false);
                        g.fill(sx + 7, sy + 17, sx + sw - 7, sy + 19, 0x55505E68);
                        g.fill(sx + 7, sy + 17, sx + 7 + (int) ((sw - 14) * ratio), sy + 19, accent);
                    }
                    if (hover) help = setting.description;
                    sy += 24;
                }
            }

            g.fill(x + 10, footerY, x + bw - 10, y + bh - 7, 0x4210171F);
            String footer = trim(help, Math.max(40, (bw - 40) / 6));
            g.text(font, footer, x + 15, footerY + 6, 0xFF7D8B96, false);
            String hint = "LMB select/toggle  •  RMB reset";
            g.text(font, hint, x + bw - font.width(hint) - 15, footerY + 6, 0xFF566671, false);

            super.extractRenderState(g, mx, my, delta);
        }

        private String renderMobSelector(GuiGraphicsExtractor g, int mx, int my, int sx, int sy, int sw, int sh,
                                         MobListSetting ml, String help, int accent) {
            List<String> ids = ml.ids();
            int pages = Math.max(1, (ids.size() + MOB_PAGE_SIZE - 1) / MOB_PAGE_SIZE);
            mobPage = Math.max(0, Math.min(mobPage, pages - 1));
            g.fill(sx, sy, sx + sw, sy + sh, 0x3A111820);
            g.fill(sx, sy, sx + sw, sy + 1, accent);
            g.text(font, "MOB FILTER", sx + 7, sy + 7, 0xFFE4EAF0, true);
            String count = ml.enabledCount() + "/" + ids.size();
            g.text(font, count, sx + sw - font.width(count) - 7, sy + 7, 0xFF82DDB0, false);

            int actionY = sy + 19;
            int allX = sx + 7, noneX = allX + 39;
            boolean allHover = in(mx, my, allX, actionY, 34, 15);
            boolean noneHover = in(mx, my, noneX, actionY, 42, 15);
            g.fill(allX, actionY, allX + 34, actionY + 15, allHover ? 0x72508365 : 0x49304E3E);
            g.fill(noneX, actionY, noneX + 42, actionY + 15, noneHover ? 0x72744949 : 0x494B3232);
            g.centeredText(font, "ALL", allX + 17, actionY + 5, 0xFFBFEBD4);
            g.centeredText(font, "NONE", noneX + 21, actionY + 5, 0xFFF0B8B8);
            if (allHover) help = "Allow every listed mob type";
            if (noneHover) help = "Block every listed mob type";

            String page = (mobPage + 1) + "/" + pages;
            int pageX = sx + sw - 71;
            g.fill(pageX, actionY, pageX + 18, actionY + 15, 0x49303B44);
            g.fill(pageX + 53, actionY, pageX + 71, actionY + 15, 0x49303B44);
            g.centeredText(font, "<", pageX + 9, actionY + 5, 0xFFB8C7D1);
            g.centeredText(font, ">", pageX + 62, actionY + 5, 0xFFB8C7D1);
            g.centeredText(font, page, pageX + 35, actionY + 5, 0xFF71818D);

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
                boolean hover = in(mx, my, cx, cy, cellW, 18);
                g.fill(cx, cy, cx + cellW, cy + 18, on ? (hover ? 0x87507C64 : 0x5E315A47) : (hover ? 0x71603D3D : 0x47332228));
                g.fill(cx + 5, cy + 7, cx + 9, cy + 11, on ? 0xFF75DDA8 : 0xFF80595D);
                String label = MobListSetting.label(id);
                g.text(font, trim(label, Math.max(8, (cellW - 20) / 6)), cx + 14, cy + 5, on ? 0xFFE2ECE6 : 0xFFB6A5A8, false);
                if (hover) help = (on ? "Following allowed: " : "Following blocked: ") + label;
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
            int railX = x + 10, railW = 98;
            int modsX = railX + railW + 8, modsW = Math.min(198, Math.max(154, bw / 3 - 22));
            int detailX = modsX + modsW + 8;
            int detailW = x + bw - 10 - detailX;

            int cy = bodyY + 23;
            for (String category : CATEGORIES) {
                if (leftClick && in(e.x(), e.y(), railX + 5, cy, railW - 10, 25)) {
                    selectedCategory = category;
                    selectedMod = firstInCategory(category);
                    mobPage = 0;
                    return true;
                }
                cy += 28;
            }

            int myCard = bodyY + 23;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                if (in(e.x(), e.y(), modsX + 5, myCard, modsW - 10, 20)) {
                    if (leftClick) {
                        if (selectedMod == m) toggle(m);
                        else { selectedMod = m; mobPage = 0; }
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
                if (leftClick && in(e.x(), e.y(), toggleX, sy, 42, 19)) { toggle(selectedMod); return true; }
                sy += 31;
                if (leftClick && in(e.x(), e.y(), sx, sy, sw, 22)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 42;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        if (handleMobSelectorClick(e, leftClick, rightClick, sx, sy, sw, ml)) return true;
                        break;
                    }
                    if (in(e.x(), e.y(), sx, sy, sw, 22)) {
                        if (rightClick) {
                            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                        } else if (leftClick) {
                            if (setting instanceof BoolSetting b) b.value = !b.value;
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
                                               int sx, int sy, int sw, MobListSetting ml) {
            List<String> ids = ml.ids();
            int pages = Math.max(1, (ids.size() + MOB_PAGE_SIZE - 1) / MOB_PAGE_SIZE);
            mobPage = Math.max(0, Math.min(mobPage, pages - 1));
            int actionY = sy + 19;
            int allX = sx + 7, noneX = allX + 39;
            if (leftClick && in(e.x(), e.y(), allX, actionY, 34, 15)) { ml.setAll(true); followTarget = null; save(); return true; }
            if (leftClick && in(e.x(), e.y(), noneX, actionY, 42, 15)) { ml.setAll(false); followTarget = null; save(); return true; }
            int pageX = sx + sw - 71;
            if (leftClick && in(e.x(), e.y(), pageX, actionY, 18, 15)) { mobPage = (mobPage - 1 + pages) % pages; return true; }
            if (leftClick && in(e.x(), e.y(), pageX + 53, actionY, 18, 15)) { mobPage = (mobPage + 1) % pages; return true; }
            if (rightClick && in(e.x(), e.y(), sx, sy, sw, 18)) { ml.reset(); mobPage = 0; followTarget = null; save(); return true; }

            int gap = 5, cellW = (sw - 14 - gap) / 2, listY = sy + 39;
            int start = mobPage * MOB_PAGE_SIZE;
            for (int i = 0; i < MOB_PAGE_SIZE; i++) {
                int idx = start + i;
                if (idx >= ids.size()) break;
                int col = i % 2, row = i / 2;
                int cx = sx + 7 + col * (cellW + gap), cy = listY + row * 22;
                if (leftClick && in(e.x(), e.y(), cx, cy, cellW, 18)) {
                    String id = ids.get(idx);
                    ml.set(id, !ml.allows(id));
                    followTarget = null;
                    save();
                    return true;
                }
            }
            return false;
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
                case "Combat" -> 0xFFE87979;
                case "Movement" -> 0xFF67C8F2;
                case "Player" -> 0xFF72D7A0;
                case "Render" -> 0xFFC195F1;
                case "World" -> 0xFFEEC36F;
                case "Testing" -> 0xFFF09A68;
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
'''

s = s[:pos] + new_gui + '}\n'
p.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.16.0+26.3' not in g:
    raise SystemExit('gradle version target not found')
gp.write_text(g.replace('mod_version=0.16.0+26.3', 'mod_version=0.17.0+26.3', 1))
