from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()

def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

rep('public static final String VERSION = "0.21.0";', 'public static final String VERSION = "0.22.0";', 'version')
rep('public static final String BUILD_ID = "EIO-021-QA1";', 'public static final String BUILD_ID = "EIO-022-QA1";', 'build id')

rep('''    private static Entity combatTarget;
    private static BlockPos chunkMineTarget;
    private static boolean attackForced;
    private static boolean toolSaverWarned;''', '''    private static Entity combatTarget;
    private static BlockPos chunkMineTarget;
    private static int chunkMineRearmTicks;
    private static int chunkMineAimTicks;
    private static int chunkMineChunkX = Integer.MIN_VALUE;
    private static int chunkMineChunkZ = Integer.MIN_VALUE;
    private static final Set<BlockPos> CHUNK_MINE_SKIPPED = new HashSet<>();
    private static boolean attackForced;
    private static boolean toolSaverWarned;''', 'chunk miner runtime fields')

rep('''        mod("Speed", "Render", "Shows horizontal movement speed in blocks per second.", -1);''', '''        mod("Speed", "Movement", "Adjusts horizontal movement speed while you are moving, with an optional live HUD readout.", -1)
                .num("Multiplier", 1.8, 1.0, 5.0, 0.1, "Horizontal movement multiplier. High values may be rejected or corrected by multiplayer servers.")
                .bool("Ground Only", true, "Only apply the speed multiplier while standing on the ground.")
                .bool("Show HUD", true, "Show current horizontal blocks-per-second while Speed is enabled.");''', 'speed module')

rep('''        mod("Chunk Miner", "Mining", "Automatically selects nearby exposed breakable blocks inside your current chunk and mines them using normal input.", -1)
                .num("Radius", 4.0, 2.0, 5.0, 0.5, "Local block scan radius. Server interaction range still applies.")
                .num("Vertical", 2.0, 1.0, 4.0, 1.0, "Vertical scan distance above and below you.")
                .bool("Exposed Only", true, "Only choose blocks with at least one air-adjacent face.")
                .bool("Avoid Below", true, "Avoid selecting blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the selected chunk-mining block.");''', '''        mod("Chunk Miner", "Mining", "Continuously mines nearby valid blocks in your current chunk, re-arming normal mining input between targets.", -1)
                .num("Radius", 4.0, 2.0, 5.0, 0.5, "Local block scan radius. Server interaction range still applies.")
                .num("Vertical", 2.0, 1.0, 4.0, 1.0, "Vertical scan distance above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next block.")
                .num("Aim Timeout", 12.0, 4.0, 40.0, 1.0, "Ticks allowed to acquire the selected block under the crosshair before trying another block.")
                .bool("Exposed Only", true, "Only choose blocks with at least one air-adjacent face.")
                .bool("Avoid Below", true, "Avoid selecting blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the selected chunk-mining block.");''', 'chunk miner settings')

rep('''            combatTarget = null;
            chunkMineTarget = null;
            clickAccumulator = 0.0;''', '''            combatTarget = null;
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
            chunkMineChunkX = Integer.MIN_VALUE;
            chunkMineChunkZ = Integer.MIN_VALUE;
            CHUNK_MINE_SKIPPED.clear();
            clickAccumulator = 0.0;''', 'disconnect chunk cleanup')

rep('''        Mod autoSwim = find("Auto Swim");
        Mod respawn = find("Auto Respawn");''', '''        Mod autoSwim = find("Auto Swim");
        Mod speed = find("Speed");
        Mod respawn = find("Auto Respawn");''', 'speed tick ref')

rep('''        if (tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }
        boolean movingForSafeWalk''', '''        if (tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }
        if (speed.enabled) applyMovementSpeed(mc, speed);
        boolean movingForSafeWalk''', 'speed tick application')

old_mining = '''        boolean miningAllowed = miningToolSafe(mc);
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
new_mining = '''        boolean miningAllowed = miningToolSafe(mc);
        boolean shouldForceAttack = false;
        if (miningAllowed) {
            if (chunkMiner.enabled) {
                int cx = mc.player.blockPosition().getX() >> 4;
                int cz = mc.player.blockPosition().getZ() >> 4;
                if (cx != chunkMineChunkX || cz != chunkMineChunkZ) {
                    chunkMineChunkX = cx;
                    chunkMineChunkZ = cz;
                    chunkMineTarget = null;
                    chunkMineRearmTicks = 0;
                    chunkMineAimTicks = 0;
                    CHUNK_MINE_SKIPPED.clear();
                }

                if (chunkMineTarget != null && mc.level.getBlockState(chunkMineTarget).isAir()) {
                    chunkMineTarget = null;
                    chunkMineAimTicks = 0;
                    CHUNK_MINE_SKIPPED.clear();
                    chunkMineRearmTicks = Math.max(1, (int) Math.round(chunkMiner.num("Retarget Delay").value));
                } else if (chunkMineTarget != null && !validChunkMineTarget(mc, chunkMiner, chunkMineTarget)) {
                    CHUNK_MINE_SKIPPED.add(chunkMineTarget.immutable());
                    chunkMineTarget = null;
                    chunkMineAimTicks = 0;
                    chunkMineRearmTicks = Math.max(1, (int) Math.round(chunkMiner.num("Retarget Delay").value));
                }

                if (chunkMineRearmTicks > 0) {
                    chunkMineRearmTicks--;
                } else {
                    if (chunkMineTarget == null) {
                        chunkMineTarget = findChunkMineTarget(mc, chunkMiner);
                        chunkMineAimTicks = 0;
                        if (chunkMineTarget == null && !CHUNK_MINE_SKIPPED.isEmpty()) {
                            CHUNK_MINE_SKIPPED.clear();
                            chunkMineTarget = findChunkMineTarget(mc, chunkMiner);
                        }
                    }
                    if (chunkMineTarget != null) {
                        if (chunkMiner.bool("Face Block").value) faceBlock(mc.player, chunkMineTarget);
                        boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(chunkMineTarget);
                        if (aimed) {
                            shouldForceAttack = true;
                            chunkMineAimTicks = 0;
                        } else if (++chunkMineAimTicks >= Math.max(4, (int) Math.round(chunkMiner.num("Aim Timeout").value))) {
                            CHUNK_MINE_SKIPPED.add(chunkMineTarget.immutable());
                            chunkMineTarget = null;
                            chunkMineAimTicks = 0;
                            chunkMineRearmTicks = 1;
                        }
                    }
                }
            } else {
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;
                chunkMineChunkZ = Integer.MIN_VALUE;
                CHUNK_MINE_SKIPPED.clear();

                if (autoMine.enabled && (!autoMine.bool("Stop In GUI").value || !guiOpen)
                        && mc.hitResult instanceof BlockHitResult) shouldForceAttack = true;
                if (tunnelMiner.enabled && (!tunnelMiner.bool("Pause On Entity").value || !(mc.hitResult instanceof EntityHitResult))) {
                    shouldForceAttack = true;
                }
            }
        } else {
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
        }

        if (shouldForceAttack) {
            mc.options.keyAttack.setDown(true);
            attackForced = true;
        } else if (attackForced) {
            mc.options.keyAttack.setDown(false);
            attackForced = false;
        }
'''
rep(old_mining, new_mining, 'queued chunk miner tick')

rep('''    private static boolean validConfiguredTarget(Minecraft mc, Mod selector, Entity target, double range, double fov) {''', '''    private static void applyMovementSpeed(Minecraft mc, Mod speed) {
        if (mc.player == null || mc.player.getAbilities().flying) return;
        if (speed.bool("Ground Only").value && !mc.player.onGround()) return;

        double forward = 0.0;
        double strafe = 0.0;
        if (mc.options.keyUp.isDown()) forward += 1.0;
        if (mc.options.keyDown.isDown()) forward -= 1.0;
        if (mc.options.keyRight.isDown()) strafe += 1.0;
        if (mc.options.keyLeft.isDown()) strafe -= 1.0;
        double length = Math.sqrt(forward * forward + strafe * strafe);
        if (length < 0.001) return;
        forward /= length;
        strafe /= length;

        double yaw = Math.toRadians(mc.player.getYRot());
        double sin = Math.sin(yaw);
        double cos = Math.cos(yaw);
        double worldX = -forward * sin + strafe * cos;
        double worldZ = forward * cos + strafe * sin;
        double basePerTick = mc.player.isSprinting() ? 0.2805 : 0.21585;
        double horizontal = basePerTick * speed.num("Multiplier").value;
        var velocity = mc.player.getDeltaMovement();
        mc.player.setDeltaMovement(worldX * horizontal, velocity.y, worldZ * horizontal);
    }

    private static boolean validConfiguredTarget(Minecraft mc, Mod selector, Entity target, double range, double fov) {''', 'speed helper')

rep('''                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (!validChunkMineTarget(mc, chunk, pos)) continue;''', '''                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (CHUNK_MINE_SKIPPED.contains(pos)) continue;
                    if (!validChunkMineTarget(mc, chunk, pos)) continue;''', 'chunk skipped targets')

rep('''            if (m.name.equals("Target Lock")) combatTarget = null;''', '''            if (m.name.equals("Chunk Miner")) {
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;
                chunkMineChunkZ = Integer.MIN_VALUE;
                CHUNK_MINE_SKIPPED.clear();
            }
            if (m.name.equals("Target Lock")) combatTarget = null;''', 'chunk toggle cleanup')

rep('''        combatTarget = null;
        chunkMineTarget = null;
        clickAccumulator = 0.0;''', '''        combatTarget = null;
        chunkMineTarget = null;
        chunkMineRearmTicks = 0;
        chunkMineAimTicks = 0;
        chunkMineChunkX = Integer.MIN_VALUE;
        chunkMineChunkZ = Integer.MIN_VALUE;
        CHUNK_MINE_SKIPPED.clear();
        clickAccumulator = 0.0;''', 'runtime release chunk cleanup')

rep('''        if (find("Speed").enabled) {
            var velocity = mc.player.getDeltaMovement();
            double bps = Math.sqrt(velocity.x * velocity.x + velocity.z * velocity.z) * 20.0;
            g.text(mc.font, String.format(Locale.ROOT, "Speed %.2f b/s", bps), 5, y, 0xFFD9E0E6, true); y += 11;
        }''', '''        if (find("Speed").enabled && find("Speed").bool("Show HUD").value) {
            var velocity = mc.player.getDeltaMovement();
            double bps = Math.sqrt(velocity.x * velocity.x + velocity.z * velocity.z) * 20.0;
            g.text(mc.font, String.format(Locale.ROOT, "Speed %.2f b/s  x%.1f", bps, find("Speed").num("Multiplier").value), 5, y, 0xFFD9E0E6, true); y += 11;
        }''', 'speed HUD')

p.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.21.0+26.3' not in g:
    raise SystemExit('gradle version target missing')
gp.write_text(g.replace('mod_version=0.21.0+26.3', 'mod_version=0.22.0+26.3', 1))
