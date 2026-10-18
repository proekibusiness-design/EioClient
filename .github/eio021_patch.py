from pathlib import Path
import json
import re

p = Path('eio26/EioClient.java')
s = p.read_text()


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)


def sub(pattern, repl, label, count=1):
    global s
    s2, n = re.subn(pattern, repl, s, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f'patch regex failed: {label} ({n}/{count})')
    s = s2

rep('import net.minecraft.network.chat.Component;\nimport net.minecraft.resources.Identifier;',
    'import net.minecraft.network.chat.Component;\nimport net.minecraft.resources.Identifier;\nimport net.minecraft.core.BlockPos;\nimport net.minecraft.core.Direction;',
    'mining core imports')
rep('import net.minecraft.world.phys.AABB;\nimport net.minecraft.world.phys.EntityHitResult;',
    'import net.minecraft.world.phys.AABB;\nimport net.minecraft.world.phys.BlockHitResult;\nimport net.minecraft.world.phys.EntityHitResult;',
    'block hit import')

rep('public static final String VERSION = "0.20.0";', 'public static final String VERSION = "0.21.0";', 'version')
rep('public static final String BUILD_ID = "EIO-020-QA1";', 'public static final String BUILD_ID = "EIO-021-QA1";', 'build id')
rep('    private static final Path TEST_LOG = FabricLoader.getInstance().getConfigDir().resolve("eio-test-session.log");\n', '', 'remove test log')
rep('''    private static int auraCooldown;
    private static int testAttackCooldown;
    private static int testCycleTicks;
    private static int testJumpTicks;
    private static int testPhase;''', '''    private static int auraCooldown;
    private static int triggerCooldown;
    private static Entity combatTarget;
    private static BlockPos chunkMineTarget;
    private static boolean attackForced;
    private static boolean toolSaverWarned;''', 'runtime fields')

combat_insert = '''
        mod("Target Lock", "Combat", "Tracks one allowed target and can keep your view centered on it without attacking automatically.", -1)
                .num("Range", 6.0, 2.0, 10.0, 0.25, "Maximum lock distance.")
                .num("FOV", 120.0, 20.0, 360.0, 10.0, "Target acquisition field of view.")
                .bool("Face Target", true, "Continuously face the locked target.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Target Lock may select.");
        mod("Trigger Bot", "Combat", "Attacks an allowed living entity only while your crosshair is directly over it.", -1)
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum direct-crosshair attack distance.")
                .num("Delay", 5.0, 1.0, 20.0, 1.0, "Ticks between trigger attacks.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Trigger Bot may attack.");
        mod("Combat Sprint", "Combat", "Automatically sprints while an allowed target is nearby and inside the configured view cone.", -1)
                .num("Range", 8.0, 2.0, 12.0, 0.5, "Target detection range used to activate sprinting.")
                .num("FOV", 180.0, 30.0, 360.0, 15.0, "Target detection field of view.")
                .bool("Players", true, "Allow player targets.")
                .bool("Mobs", true, "Allow non-player living targets.")
                .bool("Invisible", false, "Allow invisible targets.")
                .mobList("Target Selection", FOLLOW_MOB_IDS, "Choose exactly which mob types Combat Sprint may react to.");
'''
rep('\n        mod("Sprint", "Movement"', combat_insert + '\n        mod("Sprint", "Movement"', 'combat module insertion')

old_test_module = '''        mod("Test Profile", "Testing", "Runs obvious, repeatable stress patterns for private anti-cheat evaluation and writes a local test-session log.", -1)
                .num("Level", 1.0, 1.0, 5.0, 1.0, "Stress level. Higher levels use faster fixed combat timing and larger rotation snaps.")
                .num("Cycle Seconds", 4.0, 2.0, 12.0, 1.0, "How often the test profile advances or emits a test event.")
                .bool("Auto Sweep", true, "Cycle levels 1 through 5 automatically.")
                .bool("Combat", true, "Generate fixed-rate attack attempts against a nearby valid target.")
                .bool("Movement", true, "Generate an obvious jump pulse during each test cycle.")
                .bool("Rotation", true, "Generate a fixed-angle view snap during each test cycle.");

'''
mining_modules = '''        mod("Auto Mine", "Mining", "Keeps normal mining input held while your crosshair is on a block.", -1)
                .bool("Stop In GUI", true, "Release mining input while Eio's ClickGUI is open.");
        mod("Tunnel Miner", "Mining", "Straight-line tunneling helper that can hold forward and mine continuously.", -1)
                .bool("Auto Walk", true, "Hold forward while tunneling.")
                .bool("Sprint", false, "Sprint while moving through the tunnel.")
                .bool("Pause On Entity", true, "Do not hold mining input while an entity is directly under your crosshair.");
        mod("Chunk Miner", "Mining", "Automatically selects nearby exposed breakable blocks inside your current chunk and mines them using normal input.", -1)
                .num("Radius", 4.0, 2.0, 5.0, 0.5, "Local block scan radius. Server interaction range still applies.")
                .num("Vertical", 2.0, 1.0, 4.0, 1.0, "Vertical scan distance above and below you.")
                .bool("Exposed Only", true, "Only choose blocks with at least one air-adjacent face.")
                .bool("Avoid Below", true, "Avoid selecting blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the selected chunk-mining block.");
        mod("Tool Saver", "Mining", "Stops Eio mining automation before the held damageable tool reaches the configured remaining durability.", -1)
                .num("Remaining", 12.0, 1.0, 100.0, 1.0, "Minimum durability to keep in reserve.")
                .bool("Notify", true, "Show a warning when mining pauses to protect the tool.");
        mod("Mining HUD", "Mining", "Shows the current automatic mining target and held-tool durability.", -1)
                .bool("Target", true, "Show the current Chunk Miner target coordinates.")
                .bool("Tool", true, "Show remaining durability for the selected tool.");

'''
rep(old_test_module, mining_modules, 'replace testing module with mining')

old_test_command = '''                        .then(ClientCommands.literal("test")
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
'''
rep(old_test_command, '', 'remove test commands')

rep('''        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod bright = find("Fullbright");
        Mod test = find("Test Profile");''', '''        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod targetLock = find("Target Lock");
        Mod trigger = find("Trigger Bot");
        Mod combatSprint = find("Combat Sprint");
        Mod autoMine = find("Auto Mine");
        Mod tunnelMiner = find("Tunnel Miner");
        Mod chunkMiner = find("Chunk Miner");
        Mod bright = find("Fullbright");''', 'tick module refs')

rep('''        boolean shouldForceForward = walk.enabled;
        if (follow.enabled) shouldForceForward |= runFollow(mc, follow);''', '''        boolean shouldForceForward = walk.enabled;
        if (follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;''', 'tunnel forward integration')

rep('''        if (sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            boolean hungerOk = !sprint.bool("Hunger Check").value || mc.player.getFoodData().getFoodLevel() > 6;
            if (hungerOk) mc.player.setSprinting(true);
        }''', '''        if (sprint.enabled && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            boolean hungerOk = !sprint.bool("Hunger Check").value || mc.player.getFoodData().getFoodLevel() > 6;
            if (hungerOk) mc.player.setSprinting(true);
        }
        if (tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }''', 'tunnel sprint integration')

combat_tick = '''
        if (targetLock.enabled) {
            double lockRange = targetLock.num("Range").value;
            double lockFov = targetLock.num("FOV").value;
            if (!validConfiguredTarget(mc, targetLock, combatTarget, lockRange, lockFov)) {
                combatTarget = nearestTarget(mc, targetLock, lockRange, lockFov);
            }
            if (combatTarget != null && targetLock.bool("Face Target").value) faceEntity(mc.player, combatTarget);
        } else combatTarget = null;

        if (trigger.enabled) {
            if (triggerCooldown > 0) triggerCooldown--;
            if (triggerCooldown <= 0 && mc.hitResult instanceof EntityHitResult hit) {
                Entity t = hit.getEntity();
                double r = trigger.num("Range").value;
                if (validModuleTarget(trigger, t) && mc.player.distanceToSqr(t) <= r * r) {
                    attack(mc, t);
                    triggerCooldown = Math.max(1, (int) Math.round(trigger.num("Delay").value));
                }
            }
        } else triggerCooldown = 0;

        if (combatSprint.enabled && !mc.player.horizontalCollision) {
            Entity t = nearestTarget(mc, combatSprint, combatSprint.num("Range").value, combatSprint.num("FOV").value);
            if (t != null) mc.player.setSprinting(true);
        }

        boolean miningAllowed = miningToolSafe(mc);
        boolean shouldForceAttack = false;
        if (miningAllowed) {
            if (chunkMiner.enabled) {
                if (!validChunkMineTarget(mc, chunkMiner, chunkMineTarget)) {
                    chunkMineTarget = findChunkMineTarget(mc, chunkMiner);
                }
                if (chunkMineTarget != null) {
                    if (chunkMiner.bool("Face Block").value) faceBlock(mc.player, chunkMineTarget);
                    shouldForceAttack = true;
                }
            } else chunkMineTarget = null;

            if (autoMine.enabled && (!autoMine.bool("Stop In GUI").value || !guiOpen)
                    && mc.hitResult instanceof BlockHitResult) shouldForceAttack = true;
            if (tunnelMiner.enabled && (!tunnelMiner.bool("Pause On Entity").value || !(mc.hitResult instanceof EntityHitResult))) {
                shouldForceAttack = true;
            }
        } else chunkMineTarget = null;

        if (shouldForceAttack) {
            mc.options.keyAttack.setDown(true);
            attackForced = true;
        } else if (attackForced) {
            mc.options.keyAttack.setDown(false);
            attackForced = false;
        }
'''
rep('\n        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();', combat_tick + '\n        boolean clickAllowed = !clicker.bool("Require Attack").value || mc.options.keyAttack.isDown();', 'combat/mining tick insertion')

old_test_tick = '''        if (test.enabled) runTestProfile(mc, test);
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
        if (testJumpTicks > 0) testJumpTicks--;'''
new_jump = '''        boolean shouldForceJump = (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater());
        if (shouldForceJump) {
            mc.options.keyJump.setDown(true);
            jumpForced = true;
        } else if (jumpForced) {
            mc.options.keyJump.setDown(false);
            jumpForced = false;
        }'''
rep(old_test_tick, new_jump, 'remove test tick path')

helpers = '''
    private static boolean validConfiguredTarget(Minecraft mc, Mod selector, Entity target, double range, double fov) {
        if (mc.player == null || target == null || !validModuleTarget(selector, target)) return false;
        if (mc.player.distanceToSqr(target) > range * range) return false;
        return fov >= 359.9 || angleFromView(mc.player, target) <= fov / 2.0;
    }

    private static void faceEntity(Player player, Entity target) {
        double dx = target.getX() - player.getX();
        double dz = target.getZ() - player.getZ();
        double dy = target.getY() + target.getBbHeight() * 0.5 - player.getEyeY();
        double horizontal = Math.sqrt(dx * dx + dz * dz);
        player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        player.setXRot((float) (-Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)))));
    }

    private static boolean miningToolSafe(Minecraft mc) {
        Mod saver = find("Tool Saver");
        if (saver == null || !saver.enabled || mc.player == null) {
            toolSaverWarned = false;
            return true;
        }
        ItemStack held = mc.player.getInventory().getSelectedItem();
        if (held.isEmpty() || !held.isDamageableItem()) {
            toolSaverWarned = false;
            return true;
        }
        int remaining = held.getMaxDamage() - held.getDamageValue();
        int reserve = (int) Math.round(saver.num("Remaining").value);
        if (remaining <= reserve) {
            if (!toolSaverWarned && saver.bool("Notify").value) {
                notifyMessage("TOOL SAVER: MINING PAUSED (" + remaining + " LEFT)", 0xFFFFC875, 2600L);
            }
            toolSaverWarned = true;
            return false;
        }
        toolSaverWarned = false;
        return true;
    }

    private static boolean validChunkMineTarget(Minecraft mc, Mod chunk, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        BlockPos origin = mc.player.blockPosition();
        if ((pos.getX() >> 4) != (origin.getX() >> 4) || (pos.getZ() >> 4) != (origin.getZ() >> 4)) return false;
        int vertical = (int) Math.round(chunk.num("Vertical").value);
        if (Math.abs(pos.getY() - origin.getY()) > vertical) return false;
        if (chunk.bool("Avoid Below").value && pos.getY() < (int) Math.floor(mc.player.getY())) return false;
        double dx = pos.getX() + 0.5 - mc.player.getX();
        double dy = pos.getY() + 0.5 - mc.player.getY();
        double dz = pos.getZ() + 0.5 - mc.player.getZ();
        double r = chunk.num("Radius").value;
        if (dx * dx + dy * dy + dz * dz > r * r) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        if (chunk.bool("Exposed Only").value && !isExposedBlock(mc, pos)) return false;
        return true;
    }

    private static boolean isExposedBlock(Minecraft mc, BlockPos pos) {
        for (Direction direction : Direction.values()) {
            if (mc.level.getBlockState(pos.relative(direction)).isAir()) return true;
        }
        return false;
    }

    private static BlockPos findChunkMineTarget(Minecraft mc, Mod chunk) {
        if (mc.player == null || mc.level == null) return null;
        BlockPos origin = mc.player.blockPosition();
        int radius = (int) Math.ceil(chunk.num("Radius").value);
        int vertical = (int) Math.round(chunk.num("Vertical").value);
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int dy = -vertical; dy <= vertical; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (!validChunkMineTarget(mc, chunk, pos)) continue;
                    double px = pos.getX() + 0.5 - mc.player.getX();
                    double py = pos.getY() + 0.5 - mc.player.getY();
                    double pz = pos.getZ() + 0.5 - mc.player.getZ();
                    double d = px * px + py * py + pz * pz;
                    if (d < bestSq) { bestSq = d; best = pos.immutable(); }
                }
            }
        }
        return best;
    }

    private static void faceBlock(Player player, BlockPos pos) {
        double dx = pos.getX() + 0.5 - player.getX();
        double dz = pos.getZ() + 0.5 - player.getZ();
        double dy = pos.getY() + 0.5 - player.getEyeY();
        double horizontal = Math.sqrt(dx * dx + dz * dz);
        player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        player.setXRot((float) (-Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)))));
    }
'''
rep('\n    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {', helpers + '\n    private static boolean validClickTarget(Minecraft mc, Mod clicker, Entity target) {', 'helper insertion')

sub(r'\n    private static void runTestProfile\(Minecraft mc, Mod test\) \{.*?\n    \}\n\n    private static void appendTestLog\(String line\) \{.*?\n    \}\n', '\n', 'remove testing methods')

rep('''            if ((m.name.equals("AutoWalk") || m.name.equals("Follow"))
                    && !find("AutoWalk").enabled && !find("Follow").enabled && forwardForced) {''', '''            if ((m.name.equals("AutoWalk") || m.name.equals("Follow") || m.name.equals("Tunnel Miner"))
                    && !find("AutoWalk").enabled && !find("Follow").enabled
                    && !find("Tunnel Miner").enabled && forwardForced) {''', 'toggle forward ownership')
rep('''            if (m.name.equals("Fullbright")) clearFullbright(mc);
            if (m.name.equals("Test Profile")) appendTestLog("SESSION STOP");
        }
        if (m.enabled && m.name.equals("Test Profile")) appendTestLog("SESSION START Eio=" + VERSION);''', '''            if (m.name.equals("Fullbright")) clearFullbright(mc);
            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && attackForced) {
                mc.options.keyAttack.setDown(false);
                attackForced = false;
                chunkMineTarget = null;
            }
            if (m.name.equals("Target Lock")) combatTarget = null;
        }''', 'toggle cleanup')

rep('''        if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
        if (flyForced) restoreFly(mc);''', '''        if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
        if (attackForced) { mc.options.keyAttack.setDown(false); attackForced = false; }
        if (flyForced) restoreFly(mc);''', 'release attack input')
rep('''        followTarget = null;
        clickAccumulator = 0.0;
        auraCooldown = 0;
        testAttackCooldown = 0;
        testCycleTicks = 0;
        testJumpTicks = 0;''', '''        followTarget = null;
        combatTarget = null;
        chunkMineTarget = null;
        clickAccumulator = 0.0;
        auraCooldown = 0;
        triggerCooldown = 0;
        toolSaverWarned = false;''', 'release new runtime state')

rep('Set<String> categories = Set.of("Combat", "Movement", "Player", "Render", "World", "Testing", "Misc");',
    'Set<String> categories = Set.of("Combat", "Movement", "Player", "Render", "World", "Mining", "Misc");',
    'model categories')

hud_insert = '''
        if (find("Mining HUD").enabled) {
            Mod miningHud = find("Mining HUD");
            if (miningHud.bool("Target").value) {
                BlockPos miningPos = chunkMineTarget;
                if (miningPos == null && mc.hitResult instanceof BlockHitResult hit) miningPos = hit.getBlockPos();
                if (miningPos != null) {
                    g.text(mc.font, "Mining " + miningPos.getX() + " " + miningPos.getY() + " " + miningPos.getZ(), 5, y, 0xFFE9C67B, true);
                    y += 11;
                }
            }
            if (miningHud.bool("Tool").value) {
                ItemStack held = mc.player.getInventory().getSelectedItem();
                if (!held.isEmpty() && held.isDamageableItem()) {
                    int remaining = held.getMaxDamage() - held.getDamageValue();
                    g.text(mc.font, "Tool " + remaining + "/" + held.getMaxDamage(), 5, y, 0xFFE9C67B, true);
                    y += 11;
                }
            }
        }
'''
rep('\n        if (find("Reach").enabled) {', hud_insert + '\n        if (find("Reach").enabled) {', 'mining HUD insertion')
rep('''        if (find("Target HUD").enabled) {
            Entity t = followTarget;
            if (t == null && mc.hitResult instanceof EntityHitResult hit) t = hit.getEntity();''', '''        if (find("Target HUD").enabled) {
            Entity t = combatTarget != null ? combatTarget : followTarget;
            if (t == null && mc.hitResult instanceof EntityHitResult hit) t = hit.getEntity();''', 'target HUD combat lock')

rep('private static final String[] CATEGORIES = {"Active", "Combat", "Movement", "Player", "Render", "World", "Testing", "Misc"};',
    'private static final String[] CATEGORIES = {"Active", "Combat", "Movement", "Player", "Render", "World", "Mining", "Misc"};',
    'GUI categories')
rep('''                case "World" -> 0xFFEEC36F;
                case "Testing" -> 0xFFF09A68;
                default -> 0xFF82B8D6;''', '''                case "World" -> 0xFFEEC36F;
                case "Mining" -> 0xFFE0B767;
                default -> 0xFF82B8D6;''', 'mining category color')

# Update Gradle version.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.20.0+26.3' not in g:
    raise SystemExit('gradle version target missing')
gp.write_text(g.replace('mod_version=0.20.0+26.3', 'mod_version=0.21.0+26.3', 1))

# Keep keybind language entries canonical and remove the retired Test Profile key.
lang_path = Path('src/main/resources/assets/eioclient/lang/en_us.json')
lang = json.loads(lang_path.read_text())
lang.pop('key.eioclient.test_profile', None)
for slug, label in {
    'target_lock': 'Target Lock',
    'trigger_bot': 'Trigger Bot',
    'combat_sprint': 'Combat Sprint',
    'auto_mine': 'Auto Mine',
    'tunnel_miner': 'Tunnel Miner',
    'chunk_miner': 'Chunk Miner',
    'tool_saver': 'Tool Saver',
    'mining_hud': 'Mining HUD',
}.items():
    lang['key.eioclient.' + slug] = label
lang_path.write_text(json.dumps(lang, indent=2) + '\n')

p.write_text(s)
