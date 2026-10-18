from pathlib import Path
import json

src = Path('eio26/EioClient.java')
s = src.read_text()

# Idempotent: CI may run again after the canonicalized source commit.
if 'public static final String VERSION = "0.24.0";' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String VERSION = "0.23.0";', 'public static final String VERSION = "0.24.0";', 'version')
    rep('public static final String BUILD_ID = "EIO-023-QA1";', 'public static final String BUILD_ID = "EIO-024-COMPAT1";', 'build id')

    rep('''    private static boolean flyPrevMayfly;
    private static boolean flyPrevFlying;
    private static boolean lowHealthAlerted;''', '''    private static boolean flyPrevMayfly;
    private static boolean flyPrevFlying;
    private static float flyPrevSpeed = 0.05f;
    private static boolean lowHealthAlerted;''', 'fly state')

    rep('''    private static boolean creativeAssistWarned;
    private static boolean creativeAssistSpeedForced;
    private static String configSource = "defaults";''', '''    private static boolean creativeAssistWarned;
    private static boolean creativeAssistSpeedForced;
    private static float creativeAssistPrevSpeed = 0.05f;
    private static String configSource = "defaults";''', 'creative speed state')

    rep('''    private static boolean runtimeSafeMode;
    private static int runtimeFaults;
    private static String lastRuntimeFault = "none";''', '''    private static boolean runtimeSafeMode;
    private static int runtimeFaults;
    private static String lastRuntimeFault = "none";
    private static final CompatibilityState COMPAT = new CompatibilityState();
    private static long suppressedOutOfRangeAttacks;''', 'compat telemetry state')

    misc_anchor = '''        mod("Session Info", "Misc", "Shows Eio and Minecraft versions on the HUD.", -1)'''
    compat_module = '''        mod("Compatibility Guard", "Misc", "Keeps automated interactions inside vanilla reach and yields briefly when the server corrects player position.", -1)
                .bool("Vanilla Ranges", true, "Require Minecraft's own entity/block interaction-range checks before automated actions.")
                .bool("Pause On Correction", true, "Temporarily yield Eio movement/combat/mining after a server position correction or teleport.")
                .num("Pause Ticks", 4.0, 1.0, 20.0, 1.0, "Ticks to yield automation after a server position correction.")
                .bool("Diagnostics", true, "Write server-position telemetry to eio-diagnostics.log.");

''' + misc_anchor
    rep(misc_anchor, compat_module, 'compatibility module')

    rep('''                                    + " | backup=" + Files.exists(CONFIG_BACKUP) + " | safeMode=" + runtimeSafeMode
                                    + " | faults=" + runtimeFaults + " | lastFault=" + lastRuntimeFault;''', '''                                    + " | backup=" + Files.exists(CONFIG_BACKUP) + " | safeMode=" + runtimeSafeMode
                                    + " | faults=" + runtimeFaults + " | lastFault=" + lastRuntimeFault
                                    + " | serverCorrections=" + COMPAT.correctionCount() + " correctionPause=" + COMPAT.pauseTicks()
                                    + " | blockedOutOfRangeAttacks=" + suppressedOutOfRangeAttacks;''', 'doctor telemetry')

    rep('''    private static void openGui() {
        if (guiOpen) return;
        Minecraft.getInstance().setScreenAndShow(new ClickGui());
    }
''', '''    private static void openGui() {
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
''', 'server correction callback')

    rep('''            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            return;''', '''            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            COMPAT.clearPause();
            return;''', 'disconnect pause clear')

    rep('''        Mod nuker = find("Nuker");
        Mod bright = find("Fullbright");

        boolean shouldForceForward = walk.enabled;
        if (follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;''', '''        Mod nuker = find("Nuker");
        Mod bright = find("Fullbright");
        Mod compatibility = find("Compatibility Guard");
        boolean correctionPause = compatibility != null && compatibility.enabled
                && compatibility.bool("Pause On Correction").value && COMPAT.paused();

        boolean shouldForceForward = !correctionPause && walk.enabled;
        if (!correctionPause && follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;''', 'correction pause start')

    rep('''        if (sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {''', '''        if (!correctionPause && sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {''', 'sprint pause')
    rep('''        if (tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {''', '''        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {''', 'tunnel sprint pause')
    rep('''        if (speed.enabled) applyMovementSpeed(mc, speed);''', '''        if (!correctionPause && speed.enabled) applyMovementSpeed(mc, speed);''', 'speed pause')
    rep('''        boolean shouldForceSneak = safe.enabled && movingForSafeWalk && mc.player.onGround();''', '''        boolean shouldForceSneak = !correctionPause && safe.enabled && movingForSafeWalk && mc.player.onGround();''', 'safewalk pause')

    rep('''        if (fly.enabled) {
            var a = mc.player.getAbilities();
            if (!flyForced) {
                flyPrevMayfly = a.mayfly;
                flyPrevFlying = a.flying;
                flyForced = true;
            }''', '''        if (!correctionPause && fly.enabled) {
            var a = mc.player.getAbilities();
            if (!flyForced) {
                flyPrevMayfly = a.mayfly;
                flyPrevFlying = a.flying;
                flyPrevSpeed = a.getFlyingSpeed();
                flyForced = true;
            }''', 'fly pause and preserve speed')

    rep('''        if (creative.enabled && !fly.enabled && creative.bool("Auto Fly").value) {
            var abilities = mc.player.getAbilities();
            if (abilities.mayfly) {
                abilities.flying = true;
                abilities.setFlyingSpeed((float) creative.num("Flight Speed").value);
                creativeAssistSpeedForced = true;''', '''        if (!correctionPause && creative.enabled && !fly.enabled && creative.bool("Auto Fly").value) {
            var abilities = mc.player.getAbilities();
            if (abilities.mayfly) {
                if (!creativeAssistSpeedForced) creativeAssistPrevSpeed = abilities.getFlyingSpeed();
                abilities.flying = true;
                abilities.setFlyingSpeed((float) creative.num("Flight Speed").value);
                creativeAssistSpeedForced = true;''', 'creative pause and preserve speed')
    rep('''                mc.player.getAbilities().setFlyingSpeed(0.05f);
                creativeAssistSpeedForced = false;''', '''                mc.player.getAbilities().setFlyingSpeed(creativeAssistPrevSpeed);
                creativeAssistSpeedForced = false;''', 'creative exact restore', 1)

    rep('''        if (targetLock.enabled) {''', '''        if (!correctionPause && targetLock.enabled) {''', 'target lock pause')
    rep('''        if (trigger.enabled) {''', '''        if (!correctionPause && trigger.enabled) {''', 'trigger pause')
    rep('''        if (combatSprint.enabled && !mc.player.horizontalCollision) {''', '''        if (!correctionPause && combatSprint.enabled && !mc.player.horizontalCollision) {''', 'combat sprint pause')
    rep('''        boolean miningAllowed = miningToolSafe(mc);''', '''        boolean miningAllowed = !correctionPause && miningToolSafe(mc);''', 'mining pause')
    rep('''        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();
        if (clicker.enabled && clickAllowed) {''', '''        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();
        if (!correctionPause && clicker.enabled && clickAllowed) {''', 'clicker pause')
    rep('''        if (aura.enabled) {''', '''        if (!correctionPause && aura.enabled) {''', 'aura pause')
    rep('''        boolean shouldForceJump = (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater());''', '''        boolean shouldForceJump = !correctionPause && ((autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater()));''', 'jump pause')
    rep('''        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);
    }''', '''        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);
        COMPAT.tick();
    }''', 'compat countdown')

    rep('''    private static boolean validChunkMineTarget(Minecraft mc, Mod chunk, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;''', '''    private static boolean validChunkMineTarget(Minecraft mc, Mod chunk, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;''', 'chunk vanilla range')
    rep('''    private static boolean validNukerTarget(Minecraft mc, Mod nuker, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;''', '''    private static boolean validNukerTarget(Minecraft mc, Mod nuker, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;''', 'nuker vanilla range')

    rep('''    private static void attack(Minecraft mc, Entity target) {
        if (mc.player == null || mc.gameMode == null || target == null || !target.isAlive()) return;
        mc.gameMode.attack(mc.player, target);''', '''    private static boolean compatibilityRangeGuardEnabled() {
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
        mc.gameMode.attack(mc.player, target);''', 'vanilla entity attack guard')

    rep('''            a.mayfly = flyPrevMayfly;
            a.flying = flyPrevFlying;
            a.setFlyingSpeed(0.05f);''', '''            a.mayfly = flyPrevMayfly;
            a.flying = flyPrevFlying;
            a.setFlyingSpeed(flyPrevSpeed);''', 'fly exact restore')

    release_anchor = '''    private static void releaseRuntimeState(Minecraft mc) {'''
    release_helper = '''    private static void releaseCorrectionSensitiveState(Minecraft mc) {
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
        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
    }

''' + release_anchor
    rep(release_anchor, release_helper, 'correction-sensitive cleanup')

    rep('''        if (creativeAssistSpeedForced && mc.player != null && !find("Fly").enabled) mc.player.getAbilities().setFlyingSpeed(0.05f);''', '''        if (creativeAssistSpeedForced && mc.player != null && !find("Fly").enabled) mc.player.getAbilities().setFlyingSpeed(creativeAssistPrevSpeed);''', 'runtime creative restore')

    rep('''            String enabledDefault = m.name.equals("Notifications") ? "true" : "false";''', '''            String enabledDefault = (m.name.equals("Notifications") || m.name.equals("Compatibility Guard")) ? "true" : "false";''', 'compat default enabled')

    src.write_text(s)

# Version and test dependencies.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.23.0+26.3' in g:
    g = g.replace('mod_version=0.23.0+26.3', 'mod_version=0.24.0+26.3', 1)
elif 'mod_version=0.24.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)

bp = Path('build.gradle')
b = bp.read_text()
if 'mavenCentral()' not in b:
    b = b.replace('dependencies {', 'repositories {\n    mavenCentral()\n}\n\ndependencies {', 1)
if "org.junit:junit-bom" not in b:
    b = b.replace('    implementation "net.fabricmc.fabric-api:fabric-api:${project.fabric_api_version}"\n',
                  '    implementation "net.fabricmc.fabric-api:fabric-api:${project.fabric_api_version}"\n    testImplementation platform("org.junit:junit-bom:5.11.4")\n    testImplementation "org.junit.jupiter:junit-jupiter"\n', 1)
if 'useJUnitPlatform()' not in b:
    b += '\n\ntasks.withType(Test).configureEach {\n    useJUnitPlatform()\n}\n'
bp.write_text(b)

modp = Path('src/main/resources/fabric.mod.json')
mod = json.loads(modp.read_text())
mod['description'] = 'Eio Client 26.3 compatibility engineering release with server-authority telemetry, vanilla interaction guards and regression tests'
mod['mixins'] = ['eioclient.mixins.json']
modp.write_text(json.dumps(mod, indent=2) + '\n')

langp = Path('src/main/resources/assets/eioclient/lang/en_us.json')
lang = json.loads(langp.read_text())
lang['key.eioclient.compatibility_guard'] = 'Compatibility Guard'
langp.write_text(json.dumps(lang, indent=2) + '\n')
