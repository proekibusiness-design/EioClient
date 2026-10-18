from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()

def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

rep('public static final String VERSION = "0.22.0";', 'public static final String VERSION = "0.23.0";', 'version')
rep('public static final String BUILD_ID = "EIO-022-QA1";', 'public static final String BUILD_ID = "EIO-023-QA1";', 'build id')

chunk_module = '''        mod("Chunk Miner", "Mining", "Continuously mines nearby valid blocks in your current chunk, re-arming normal mining input between targets.", -1)
                .num("Radius", 4.0, 2.0, 5.0, 0.5, "Local block scan radius. Server interaction range still applies.")
                .num("Vertical", 2.0, 1.0, 4.0, 1.0, "Vertical scan distance above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next block.")
                .num("Aim Timeout", 12.0, 4.0, 40.0, 1.0, "Ticks allowed to acquire the selected block under the crosshair before trying another block.")
                .bool("Exposed Only", true, "Only choose blocks with at least one air-adjacent face.")
                .bool("Avoid Below", true, "Avoid selecting blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the selected chunk-mining block.");'''
chunk_plus_nuker = chunk_module + '''
        mod("Nuker", "Mining", "Continuously clears nearby breakable blocks around you using normal block-breaking interaction and automatic retargeting.", -1)
                .num("Radius", 5.0, 2.0, 6.0, 0.5, "Horizontal clearing radius. Effective distance is still limited by normal server interaction range.")
                .num("Vertical", 3.0, 1.0, 6.0, 1.0, "Vertical scan distance above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next block.")
                .num("Aim Timeout", 10.0, 4.0, 40.0, 1.0, "Ticks allowed to acquire a selected block before trying another one.")
                .bool("Exposed Only", true, "Only target blocks that currently have an exposed face.")
                .bool("Avoid Below", true, "Avoid blocks below your feet so Nuker is less likely to drop you.")
                .bool("Face Block", true, "Turn your view toward the selected Nuker target.");'''
rep(chunk_module, chunk_plus_nuker, 'nuker module')

rep('''        Mod tunnelMiner = find("Tunnel Miner");
        Mod chunkMiner = find("Chunk Miner");
        Mod bright = find("Fullbright");''', '''        Mod tunnelMiner = find("Tunnel Miner");
        Mod chunkMiner = find("Chunk Miner");
        Mod nuker = find("Nuker");
        Mod bright = find("Fullbright");''', 'nuker tick ref')

old_branch = '''            if (chunkMiner.enabled) {
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
            }'''
new_branch = '''            Mod areaMiner = nuker.enabled ? nuker : (chunkMiner.enabled ? chunkMiner : null);
            boolean nukerMode = areaMiner == nuker;
            if (areaMiner != null) {
                int cx = mc.player.blockPosition().getX() >> 4;
                int cz = mc.player.blockPosition().getZ() >> 4;
                if (!nukerMode && (cx != chunkMineChunkX || cz != chunkMineChunkZ)) {
                    chunkMineChunkX = cx;
                    chunkMineChunkZ = cz;
                    chunkMineTarget = null;
                    chunkMineRearmTicks = 0;
                    chunkMineAimTicks = 0;
                    CHUNK_MINE_SKIPPED.clear();
                }
                if (nukerMode) {
                    chunkMineChunkX = Integer.MIN_VALUE;
                    chunkMineChunkZ = Integer.MIN_VALUE;
                }

                boolean currentValid = nukerMode
                        ? validNukerTarget(mc, areaMiner, chunkMineTarget)
                        : validChunkMineTarget(mc, areaMiner, chunkMineTarget);
                if (chunkMineTarget != null && mc.level.getBlockState(chunkMineTarget).isAir()) {
                    chunkMineTarget = null;
                    chunkMineAimTicks = 0;
                    CHUNK_MINE_SKIPPED.clear();
                    chunkMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                } else if (chunkMineTarget != null && !currentValid) {
                    CHUNK_MINE_SKIPPED.add(chunkMineTarget.immutable());
                    chunkMineTarget = null;
                    chunkMineAimTicks = 0;
                    chunkMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                }

                if (chunkMineRearmTicks > 0) {
                    chunkMineRearmTicks--;
                } else {
                    if (chunkMineTarget == null) {
                        chunkMineTarget = nukerMode ? findNukerTarget(mc, areaMiner) : findChunkMineTarget(mc, areaMiner);
                        chunkMineAimTicks = 0;
                        if (chunkMineTarget == null && !CHUNK_MINE_SKIPPED.isEmpty()) {
                            CHUNK_MINE_SKIPPED.clear();
                            chunkMineTarget = nukerMode ? findNukerTarget(mc, areaMiner) : findChunkMineTarget(mc, areaMiner);
                        }
                    }
                    if (chunkMineTarget != null) {
                        if (areaMiner.bool("Face Block").value) faceBlock(mc.player, chunkMineTarget);
                        boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(chunkMineTarget);
                        if (aimed) {
                            shouldForceAttack = true;
                            chunkMineAimTicks = 0;
                        } else if (++chunkMineAimTicks >= Math.max(4, (int) Math.round(areaMiner.num("Aim Timeout").value))) {
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
            }'''
rep(old_branch, new_branch, 'nuker mining controller')

helper_anchor = '''    private static boolean isExposedBlock(Minecraft mc, BlockPos pos) {
        for (Direction direction : Direction.values()) {
            if (mc.level.getBlockState(pos.relative(direction)).isAir()) return true;
        }
        return false;
    }

    private static BlockPos findChunkMineTarget(Minecraft mc, Mod chunk) {'''
helper_replacement = '''    private static boolean isExposedBlock(Minecraft mc, BlockPos pos) {
        for (Direction direction : Direction.values()) {
            if (mc.level.getBlockState(pos.relative(direction)).isAir()) return true;
        }
        return false;
    }

    private static boolean validNukerTarget(Minecraft mc, Mod nuker, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        BlockPos origin = mc.player.blockPosition();
        int vertical = (int) Math.round(nuker.num("Vertical").value);
        if (Math.abs(pos.getY() - origin.getY()) > vertical) return false;
        if (nuker.bool("Avoid Below").value && pos.getY() < (int) Math.floor(mc.player.getY())) return false;
        double dx = pos.getX() + 0.5 - mc.player.getX();
        double dy = pos.getY() + 0.5 - mc.player.getY();
        double dz = pos.getZ() + 0.5 - mc.player.getZ();
        double r = nuker.num("Radius").value;
        if (dx * dx + dz * dz > r * r || Math.abs(dy) > vertical + 1.0) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        if (nuker.bool("Exposed Only").value && !isExposedBlock(mc, pos)) return false;
        return true;
    }

    private static BlockPos findNukerTarget(Minecraft mc, Mod nuker) {
        if (mc.player == null || mc.level == null) return null;
        BlockPos origin = mc.player.blockPosition();
        int radius = (int) Math.ceil(nuker.num("Radius").value);
        int vertical = (int) Math.round(nuker.num("Vertical").value);
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int dy = -vertical; dy <= vertical; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (CHUNK_MINE_SKIPPED.contains(pos)) continue;
                    if (!validNukerTarget(mc, nuker, pos)) continue;
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

    private static BlockPos findChunkMineTarget(Minecraft mc, Mod chunk) {'''
rep(helper_anchor, helper_replacement, 'nuker target helpers')

rep('''            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && attackForced) {''', '''            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner") || m.name.equals("Nuker"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled
                    && !find("Nuker").enabled && attackForced) {''', 'nuker attack cleanup')
rep('''            if (m.name.equals("Chunk Miner")) {
                chunkMineTarget = null;''', '''            if (m.name.equals("Chunk Miner") || m.name.equals("Nuker")) {
                chunkMineTarget = null;''', 'nuker toggle cleanup')

rep('''                String text = "Mining " + chunkMineTarget.getX() + "," + chunkMineTarget.getY() + "," + chunkMineTarget.getZ();''', '''                String owner = find("Nuker").enabled ? "Nuker" : "Mining";
                String text = owner + " " + chunkMineTarget.getX() + "," + chunkMineTarget.getY() + "," + chunkMineTarget.getZ();''', 'mining HUD owner')

p.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.22.0+26.3' not in g:
    raise SystemExit('gradle version target missing')
gp.write_text(g.replace('mod_version=0.22.0+26.3', 'mod_version=0.23.0+26.3', 1))

langp = Path('src/main/resources/assets/eioclient/lang/en_us.json')
import json
lang = json.loads(langp.read_text())
lang['key.eioclient.nuker'] = 'Nuker'
langp.write_text(json.dumps(lang, indent=2, sort_keys=False) + '\n')
