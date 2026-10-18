from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

if 'public static final String VERSION = "0.24.1";' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String VERSION = "0.24.0";', 'public static final String VERSION = "0.24.1";', 'version')
    rep('public static final String BUILD_ID = "EIO-024-COMPAT1";', 'public static final String BUILD_ID = "EIO-0241-PROTOCOL1";', 'build id')

    rep('''    private static final CompatibilityState COMPAT = new CompatibilityState();
    private static long suppressedOutOfRangeAttacks;
    private static final long sessionStartedNanos''', '''    private static final CompatibilityState COMPAT = new CompatibilityState();
    private static final SingleIntentQueue<Entity> ATTACK_QUEUE = new SingleIntentQueue<>();
    private static long suppressedOutOfRangeAttacks;
    private static long queuedAttacks;
    private static long coalescedAttacks;
    private static final long sessionStartedNanos''', 'attack queue fields')

    rep('''        mod("Compatibility Guard", "Misc", "Keeps automated interactions inside vanilla reach and yields briefly when the server corrects player position.", -1)
                .bool("Vanilla Ranges", true, "Require Minecraft's own entity/block interaction-range checks before automated actions.")
                .bool("Pause On Correction", true, "Temporarily yield Eio movement/combat/mining after a server position correction or teleport.")''', '''        mod("Compatibility Guard", "Misc", "Keeps automated interactions inside vanilla semantics and yields briefly when the server corrects player position.", -1)
                .bool("Vanilla Ranges", true, "Require Minecraft's own entity/block interaction-range checks before automated actions.")
                .bool("Line Of Sight", true, "Require direct vanilla line of sight before Eio queues an automated entity attack.")
                .bool("Pause On Correction", true, "Temporarily yield Eio movement/combat/mining after a server position correction or teleport.")''', 'line of sight setting')

    rep('''        ClientTickEvents.END_CLIENT_TICK.register(EioClient::guardedTick);''', '''        ClientTickEvents.START_CLIENT_TICK.register(EioClient::guardedStartTick);
        ClientTickEvents.END_CLIENT_TICK.register(EioClient::guardedTick);''', 'start tick registration')

    rep('''                                    + " | serverCorrections=" + COMPAT.correctionCount() + " correctionPause=" + COMPAT.pauseTicks()
                                    + " | blockedOutOfRangeAttacks=" + suppressedOutOfRangeAttacks;''', '''                                    + " | serverCorrections=" + COMPAT.correctionCount() + " correctionPause=" + COMPAT.pauseTicks()
                                    + " | blockedOutOfRangeAttacks=" + suppressedOutOfRangeAttacks
                                    + " | queuedAttacks=" + queuedAttacks + " coalescedAttacks=" + coalescedAttacks;''', 'doctor attack scheduling telemetry')

    rep('''    private static void guardedTick(Minecraft mc) {
        try {''', '''    private static void guardedStartTick(Minecraft mc) {
        try {
            if (runtimeSafeMode) {
                ATTACK_QUEUE.clear();
                return;
            }
            flushPendingAttack(mc);
        } catch (Throwable t) {
            enterSafeMode("startTick", t, mc);
        }
    }

    private static void guardedTick(Minecraft mc) {
        try {''', 'start tick flush handler')

    rep('''            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            COMPAT.clearPause();
            return;''', '''            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            ATTACK_QUEUE.clear();
            COMPAT.clearPause();
            return;''', 'disconnect queue clear')

    old_attack = '''    private static void attack(Minecraft mc, Entity target) {
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
'''
    new_attack = '''    private static boolean hasRequiredAttackLineOfSight(Minecraft mc, Entity target) {
        Mod guard = find("Compatibility Guard");
        return guard == null || !guard.enabled || !guard.bool("Line Of Sight").value
                || (mc.player != null && mc.player.hasLineOfSight(target));
    }

    private static void attack(Minecraft mc, Entity target) {
        if (mc.player == null || mc.gameMode == null || target == null || !target.isAlive()) return;
        if (!withinVanillaEntityRange(mc, target)) {
            suppressedOutOfRangeAttacks++;
            return;
        }
        if (!hasRequiredAttackLineOfSight(mc, target)) return;
        if (ATTACK_QUEUE.offer(target)) queuedAttacks++;
        else coalescedAttacks++;
    }

    private static void flushPendingAttack(Minecraft mc) {
        Entity target = ATTACK_QUEUE.poll();
        if (target == null || mc.player == null || mc.gameMode == null || mc.level == null || !target.isAlive()) return;
        if (!withinVanillaEntityRange(mc, target)) {
            suppressedOutOfRangeAttacks++;
            return;
        }
        if (!hasRequiredAttackLineOfSight(mc, target)) return;
        mc.gameMode.attack(mc.player, target);
        mc.player.swing(InteractionHand.MAIN_HAND, mc.player.getMainHandItem().getAttackAnimation(), true);
        long now = System.currentTimeMillis();
        ATTACK_TIMES.addLast(now);
        while (!ATTACK_TIMES.isEmpty() && ATTACK_TIMES.peekFirst() < now - 1000L) ATTACK_TIMES.removeFirst();
    }
'''
    rep(old_attack, new_attack, 'defer direct attacks to next start tick')

    rep('''        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
    }

    private static void releaseRuntimeState''', '''        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
        ATTACK_QUEUE.clear();
    }

    private static void releaseRuntimeState''', 'correction queue clear')

    rep('''        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
        toolSaverWarned = false;''', '''        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
        ATTACK_QUEUE.clear();
        toolSaverWarned = false;''', 'runtime queue clear')

    src.write_text(s)

# Bump artifact version.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.24.0+26.3' in g:
    g = g.replace('mod_version=0.24.0+26.3', 'mod_version=0.24.1+26.3', 1)
elif 'mod_version=0.24.1+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)

# Keep the real-client smoke test pinned to this exact candidate.
gt = Path('src/gametest/java/com/eio/client/gametest/EioClientGameTest.java')
t = gt.read_text()
t = t.replace('"0.24.0".equals(EioClient.VERSION)', '"0.24.1".equals(EioClient.VERSION)')
gt.write_text(t)

print('0.24.1 packet phase patch applied')
