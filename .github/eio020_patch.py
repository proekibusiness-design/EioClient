from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, 1)

rep('public static final String VERSION = "0.19.0";', 'public static final String VERSION = "0.20.0";', 'version')
rep('public static final String BUILD_ID = "EIO-019-QA1";', 'public static final String BUILD_ID = "EIO-020-QA1";', 'build id')

rep('''                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible living targets.");''', '''                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible living targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Kill Aura may target.");''', 'kill aura target selector')

rep('''                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.");''', '''                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Auto Clicker may target.");''', 'auto clicker target selector')

rep('''                .bool("Players", true, "Include players in Reach display targeting.")
                .bool("Mobs", true, "Include non-player living entities in Reach display targeting.")
                .bool("Invisible", false, "Include invisible living entities in Reach display targeting.");''', '''                .bool("Players", true, "Include players in Reach display targeting.")
                .bool("Mobs", true, "Include non-player living entities in Reach display targeting.")
                .bool("Invisible", false, "Include invisible living entities in Reach display targeting.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Reach may display as targets.");''', 'reach target selector')

rep('''                    clickTarget = nearestTarget(mc, clicker.num("Range").value, clicker.num("FOV").value,
                            clicker.bool("Players").value, clicker.bool("Mobs").value, clicker.bool("Invisible").value);''', '''                    clickTarget = nearestTarget(mc, clicker, clicker.num("Range").value, clicker.num("FOV").value);''', 'clicker shared selector')

rep('''                Entity target = nearestTarget(mc, aura.num("Range").value, aura.num("FOV").value,
                        aura.bool("Players").value, aura.bool("Mobs").value, aura.bool("Invisible").value);''', '''                Entity target = nearestTarget(mc, aura, aura.num("Range").value, aura.num("FOV").value);''', 'aura shared selector')

old_valid = '''    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {
        if (!(target instanceof LivingEntity) || !target.isAlive() || mc.player == null) return false;
        if (target instanceof Player && !clicker.bool("Players").value) return false;
        if (!(target instanceof Player) && !clicker.bool("Mobs").value) return false;
        if (target.isInvisible() && !clicker.bool("Invisible").value) return false;
        if (angleFromView(mc.player, target) > clicker.num("FOV").value / 2.0) return false;
        double r = clicker.num("Range").value;
        return mc.player.distanceToSqr(target) <= r * r;
    }

    private static void attack'''
new_valid = '''    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {
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

    private static void attack'''
rep(old_valid, new_valid, 'shared combat filter helpers')

rep('''            Entity rt = nearestTarget(mc, reach.num("Range").value, 360.0,
                    reach.bool("Players").value, reach.bool("Mobs").value, reach.bool("Invisible").value);''', '''            Entity rt = nearestTarget(mc, reach, reach.num("Range").value, 360.0);''', 'reach shared selector')

rep('''        private static final String[] CATEGORIES = {"Combat", "Movement", "Player", "Render", "World", "Testing", "Misc"};''', '''        private static final String[] CATEGORIES = {"Active", "Combat", "Movement", "Player", "Render", "World", "Testing", "Misc"};''', 'active category')

rep('''        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (m.category.equals(category)) return m;
            return null;
        }

        private int panelW() { return Math.max(430, Math.min(690, width - 18)); }
        private int panelH() { return Math.max(270, Math.min(390, height - 18)); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }
        private int categoryCount(String category) { int count = 0; for (Mod m : MODS) if (m.category.equals(category)) count++; return count; }''', '''        private boolean categoryMatches(Mod m, String category) {
            return "Active".equals(category) ? m.enabled : m.category.equals(category);
        }

        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (categoryMatches(m, category)) return m;
            return null;
        }

        private int panelW() { return Math.max(430, Math.min(690, width - 18)); }
        private int panelH() { return Math.max(270, Math.min(390, height - 18)); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }
        private int categoryCount(String category) { int count = 0; for (Mod m : MODS) if (categoryMatches(m, category)) count++; return count; }''', 'active category matching')

s = s.replace('for (Mod m : MODS) if (m.category.equals(selectedCategory)) {', 'for (Mod m : MODS) if (categoryMatches(m, selectedCategory)) {')

rep('''                    if (leftClick) {
                        if (selectedMod == m) toggle(m);
                        else { selectedMod = m; mobPage = 0; settingsScroll = 0; }
                    } else {''', '''                    if (leftClick) {
                        if (selectedMod == m) {
                            toggle(m);
                            if ("Active".equals(selectedCategory) && !m.enabled) {
                                selectedMod = firstInCategory("Active");
                                mobPage = 0;
                                settingsScroll = 0;
                            }
                        } else { selectedMod = m; mobPage = 0; settingsScroll = 0; }
                    } else {''', 'active quick disable module list')

rep('''                if (leftClick && in(e.x(), e.y(), toggleX, sy, 42, 19)) { toggle(selectedMod); return true; }''', '''                if (leftClick && in(e.x(), e.y(), toggleX, sy, 42, 19)) {
                    Mod toggled = selectedMod;
                    toggle(toggled);
                    if ("Active".equals(selectedCategory) && !toggled.enabled) {
                        selectedMod = firstInCategory("Active");
                        mobPage = 0;
                        settingsScroll = 0;
                    }
                    return true;
                }''', 'active quick disable detail toggle')

rep('''                case "Combat" -> 0xFFE87979;''', '''                case "Active" -> 0xFF72D7A0;
                case "Combat" -> 0xFFE87979;''', 'active category color')

# Make footer help explain the new section.
rep('''            String hint = "LMB select/toggle  •  RMB reset";''', '''            String hint = "ACTIVE = enabled modules  •  LMB select/toggle  •  RMB reset";''', 'active footer hint')

p.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.19.0+26.3' not in g:
    raise SystemExit('gradle version target missing')
gp.write_text(g.replace('mod_version=0.19.0+26.3', 'mod_version=0.20.0+26.3', 1))
