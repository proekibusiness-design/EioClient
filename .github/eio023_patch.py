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

rep('''    private static final Set<BlockPos> CHUNK_MINE_SKIPPED = new HashSet<>();
    private static boolean attackForced;''', '''    private static final Set<BlockPos> CHUNK_MINE_SKIPPED = new HashSet<>();
    private static BlockPos nukerTarget;
    private static int nukerRearmTicks;
    private static int nukerAimTicks;
    private static final Set<BlockPos> NUKER_SKIPPED = new HashSet<>();
    private static boolean attackForced;''', 'nuker runtime fields')

rep('''.num("Multiplier", 1.8, 1.0, 5.0, 0.1, "Horizontal movement multiplier. High values may be rejected or corrected by multiplayer servers.")''', '''.num("Multiplier", 1.8, 1.0, 10.0, 0.1, "Horizontal movement multiplier. Extreme values may be rejected or corrected by multiplayer servers.")''', 'speed max')

chunk_block = '''        mod("Chunk Miner", "Mining", "Continuously mines nearby valid blocks in your current chunk, re-arming normal mining input between targets.", -1)
                .num("Radius", 4.0, 2.0, 5.0, 0.5, "Local block scan radius. Server interaction range still applies.")
                .num("Vertical", 2.0, 1.0, 4.0, 1.0, "Vertical scan distance above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next block.")
                .num("Aim Timeout", 12.0, 4.0, 40.0, 1.0, "Ticks allowed to acquire the selected block under the crosshair before trying another block.")
                .bool("Exposed Only", true, "Only choose blocks with at least one air-adjacent face.")
                .bool("Avoid Below", true, "Avoid selecting blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the selected chunk-mining block.");'''
nuker_block = chunk_block + '''
        mod("Nuker", "Mining", "Aggressively clears nearby breakable blocks with continuous retargeting while still using normal mining interaction.", -1)
                .num("Radius", 5.0, 1.0, 6.0, 0.5, "Area-clear radius around you. Normal server interaction distance still applies.")
                .num("Vertical", 3.0, 1.0, 5.0, 1.0, "Vertical area cleared above and below you.")
                .num("Retarget Delay", 1.0, 1.0, 3.0, 1.0, "Ticks to release attack before starting the next Nuker target.")
                .num("Aim Timeout", 8.0, 4.0, 30.0, 1.0, "Ticks allowed to acquire a block before skipping it temporarily.")
                .bool("Exposed Only", true, "Only target blocks with at least one exposed face.")
                .bool("Avoid Below", true, "Avoid mining blocks below your feet.")
                .bool("Face Block", true, "Turn your view toward the active Nuker target.");'''
rep(chunk_block, nuker_block, 'nuker module')

rep('''            chunkMineChunkZ = Integer.MIN_VALUE;
            CHUNK_MINE_SKIPPED.clear();
            clickAccumulator = 0.0;''', '''            chunkMineChunkZ = Integer.MIN_VALUE;
            CHUNK_MINE_SKIPPED.clear();
            nukerTarget = null;
            nukerRearmTicks = 0;
            nukerAimTicks = 0;
            NUKER_SKIPPED.clear();
            clickAccumulator = 0.0;''', 'disconnect nuker cleanup')

rep('''        Mod chunkMiner = find("Chunk Miner");
        Mod bright = find("Fullbright");''', '''        Mod chunkMiner = find("Chunk Miner");
        Mod nuker = find("Nuker");
        Mod bright = find("Fullbright");''', 'nuker tick ref')

old_mining_start = '''        if (miningAllowed) {
            if (chunkMiner.enabled) {'''
new_mining_start = '''        if (miningAllowed) {
            if (nuker.enabled) {
                if (nukerTarget != null && mc.level.getBlockState(nukerTarget).isAir()) {
                    nukerTarget = null;
                    nukerAimTicks = 0;
                    nukerRearmTicks = Math.max(1, (int) Math.round(nuker.num("Retarget Delay").value));
                } else if (nukerTarget != null && !validNukerTarget(mc, nuker, nukerTarget)) {
                    NUKER_SKIPPED.add(nukerTarget.immutable());
                    nukerTarget = null;
                    nukerAimTicks = 0;
                    nukerRearmTicks = Math.max(1, (int) Math.round(nuker.num("Retarget Delay").value));
                }

                if (nukerRearmTicks > 0) {
                    nukerRearmTicks--;
                } else {
                    if (nukerTarget == null) {
                        nukerTarget = findNukerTarget(mc, nuker);
                        nukerAimTicks = 0;
                        if (nukerTarget == null && !NUKER_SKIPPED.isEmpty()) {
                            NUKER_SKIPPED.clear();
                            nukerTarget = findNukerTarget(mc, nuker);
                        }
                    }
                    if (nukerTarget != null) {
                        if (nuker.bool("Face Block").value) faceBlock(mc.player, nukerTarget);
                        boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(nukerTarget);
                        if (aimed) {
                            shouldForceAttack = true;
                            nukerAimTicks = 0;
                        } else if (++nukerAimTicks >= Math.max(4, (int) Math.round(nuker.num("Aim Timeout").value))) {
                            NUKER_SKIPPED.add(nukerTarget.immutable());
                            nukerTarget = null;
                            nukerAimTicks = 0;
                            nukerRearmTicks = 1;
                        }
                    }
                }

                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
            } else if (chunkMiner.enabled) {'''
rep(old_mining_start, new_mining_start, 'nuker mining priority')

rep('''            } else {
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;''', '''            } else {
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                NUKER_SKIPPED.clear();
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;''', 'inactive nuker cleanup')

rep('''        } else {
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
        }

        if (shouldForceAttack) {''', '''        } else {
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
            nukerTarget = null;
            nukerRearmTicks = 0;
            nukerAimTicks = 0;
        }

        if (shouldForceAttack) {''', 'tool saver nuker cleanup')

helper_anchor = '''    private static void faceBlock(Player player, BlockPos pos) {
        double dx = pos.getX() + 0.5 - player.getX();'''
helpers = '''    private static boolean validNukerTarget(Minecraft mc, Mod nuker, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        BlockPos origin = mc.player.blockPosition();
        int vertical = (int) Math.round(nuker.num("Vertical").value);
        if (Math.abs(pos.getY() - origin.getY()) > vertical) return false;
        if (nuker.bool("Avoid Below").value && pos.getY() < (int) Math.floor(mc.player.getY())) return false;
        double dx = pos.getX() + 0.5 - mc.player.getX();
        double dy = pos.getY() + 0.5 - mc.player.getY();
        double dz = pos.getZ() + 0.5 - mc.player.getZ();
        double r = nuker.num("Radius").value;
        if (dx * dx + dy * dy + dz * dz > r * r) return false;
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
                    if (NUKER_SKIPPED.contains(pos)) continue;
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

'''
rep(helper_anchor, helpers + helper_anchor, 'nuker helpers')

rep('''            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && attackForced) {''', '''            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner") || m.name.equals("Nuker"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && !find("Nuker").enabled && attackForced) {''', 'mining disable ownership')

rep('''            if (m.name.equals("Chunk Miner")) {
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;
                chunkMineChunkZ = Integer.MIN_VALUE;
                CHUNK_MINE_SKIPPED.clear();
            }
            if (m.name.equals("Target Lock")) combatTarget = null;''', '''            if (m.name.equals("Chunk Miner")) {
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
                chunkMineChunkX = Integer.MIN_VALUE;
                chunkMineChunkZ = Integer.MIN_VALUE;
                CHUNK_MINE_SKIPPED.clear();
            }
            if (m.name.equals("Nuker")) {
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                NUKER_SKIPPED.clear();
            }
            if (m.name.equals("Target Lock")) combatTarget = null;''', 'nuker toggle cleanup')

rep('''        chunkMineChunkZ = Integer.MIN_VALUE;
        CHUNK_MINE_SKIPPED.clear();
        clickAccumulator = 0.0;''', '''        chunkMineChunkZ = Integer.MIN_VALUE;
        CHUNK_MINE_SKIPPED.clear();
        nukerTarget = null;
        nukerRearmTicks = 0;
        nukerAimTicks = 0;
        NUKER_SKIPPED.clear();
        clickAccumulator = 0.0;''', 'runtime nuker cleanup')

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
langp.write_text(json.dumps(lang, indent=2) + '\n')
