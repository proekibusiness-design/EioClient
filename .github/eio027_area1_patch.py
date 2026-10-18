from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

if 'BUILD_ID = "EIO-027-AREA1"' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String VERSION = "0.26.0";', 'public static final String VERSION = "0.27.0";', 'version')
    rep('public static final String BUILD_ID = "EIO-026-AREA3";', 'public static final String BUILD_ID = "EIO-027-AREA1";', 'build id')

    rep('''    private static BlockPos areaMineTarget;
    private static int areaMineRearmTicks;
    private static int areaMineAimTicks;
    private static int areaNavIndex;
    private static int areaMoveTicks;
    private static int areaMinedThisPass;
    private static boolean areaMoveRequested;
    private static boolean areaComplete;''', '''    private static final int AREA_STAGE_HEIGHT = 5;
    private static BlockPos areaMineTarget;
    private static int areaMineRearmTicks;
    private static int areaMineAimTicks;
    private static int areaAimFailures;
    private static int areaNavIndex;
    private static int areaStageIndex;
    private static int areaMoveTicks;
    private static int areaMinedThisPass;
    private static boolean areaMoveRequested;
    private static boolean areaComplete;''', 'area state')

    start = s.index('        mod("Area Miner", "Mining",')
    end = s.index('        mod("Tool Saver", "Mining",', start)
    new_module = '''        mod("Area Miner", "Mining", "Deterministic serpentine quarry: mines straight lanes from Corner A, clears the area in 5-block-deep stages, then descends to the next stage until the requested depth is complete.", -1)
                .point("Corner A", "Starting corner. Stand at the surface start of the first lane and left-click this row. Right-click clears it.")
                .point("Corner B", "Opposite horizontal corner of the area. Left-click this row while standing there. Right-click clears it.")
                .num("Depth", 10.0, 1.0, 64.0, 1.0, "Total depth to clear. Mining is completed in fixed 5-block stages from the surface downward.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next block in the same lane cell.")
                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to acquire the current deterministic target before retrying it.")
                .num("Move Timeout", 120.0, 20.0, 300.0, 5.0, "Ticks allowed to reach the next lane cell. A timeout pauses Area Miner instead of skipping ahead.")
                .bool("Auto Move", true, "Walk one serpentine cell at a time only after the current 5-block stage column is clear.")
                .bool("Sprint", false, "Sprint only while travelling along the current straight lane.")
                .bool("Auto Jump", true, "Jump over a simple one-block obstruction without changing the lane plan.")
                .bool("Exposed Only", true, "Mine exposed blocks in deterministic top-to-bottom order inside the current 5-block stage.")
                .bool("Face Block", true, "Aim at the current deterministic Area Miner block target.");
'''
    s = s[:start] + new_module + s[end:]

    # Replace the Area Miner branch in the mining loop. Never skip targets/lanes on aim failure.
    mining_anchor = s.index('        boolean miningAllowed = !correctionPause && miningToolSafe(mc);')
    start = s.index('            if (areaMiner.enabled) {', mining_anchor)
    end = s.index('            } else if (nuker.enabled) {', start)
    new_area_branch = '''            if (areaMiner.enabled) {
                if (!areaConfigured(areaMiner)) {
                    areaMineTarget = null;
                } else {
                    if (areaMineTarget != null && mc.level.getBlockState(areaMineTarget).isAir()) {
                        areaMinedThisPass++;
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                        areaAimFailures = 0;
                        areaMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                    } else if (areaMineTarget != null && !validAreaMineTarget(mc, areaMiner, areaMineTarget)) {
                        // The player may have moved just outside vanilla interaction reach. Retry the same
                        // deterministic lane/stage rather than selecting an unrelated block elsewhere.
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                        areaMineRearmTicks = 1;
                    }
                    if (areaMineRearmTicks > 0) {
                        areaMineRearmTicks--;
                    } else {
                        if (areaMineTarget == null) {
                            areaMineTarget = findAreaMineTarget(mc, areaMiner);
                            areaMineAimTicks = 0;
                        }
                        if (areaMineTarget != null) {
                            if (areaMiner.bool("Face Block").value) faceBlock(mc.player, areaMineTarget);
                            boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(areaMineTarget);
                            if (aimed) {
                                shouldForceAttack = true;
                                areaMineAimTicks = 0;
                                areaAimFailures = 0;
                            } else if (++areaMineAimTicks >= Math.max(4, (int) Math.round(areaMiner.num("Aim Timeout").value))) {
                                areaMineTarget = null;
                                areaMineAimTicks = 0;
                                areaMineRearmTicks = 2;
                                if (++areaAimFailures >= 3) {
                                    pauseAreaMiner(areaMiner, "AIM BLOCKED - CHECK LINE OF SIGHT");
                                }
                            }
                        }
                    }
                }
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
'''
    s = s[:start] + new_area_branch + s[end:]

    # Replace status/reset helpers with explicit 5-block stage reporting.
    start = s.index('    private static String areaStatus(Mod area) {')
    end = s.index('    private static boolean validAreaMineTarget', start)
    new_helpers = '''    private static String areaStatus(Mod area) {
        AreaRegion region = areaRegion(area);
        if (region == null) return "Area Miner: set Corner A and Corner B";
        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;
        int stages = region.stageCount(AREA_STAGE_HEIGHT);
        int stage = Math.min(Math.max(0, areaStageIndex), Math.max(0, stages - 1));
        String layer = stages <= 0 ? "" : " | layer " + (stage + 1) + "/" + stages
                + " Y " + region.stageTopY(stage, AREA_STAGE_HEIGHT) + ".." + region.stageBottomY(stage, AREA_STAGE_HEIGHT);
        return "Area Miner: " + region.summary() + layer
                + (areaComplete ? " | complete" : " | lane " + Math.min(region.navigationCells(), areaNavIndex + 1) + "/" + region.navigationCells());
    }

    private static void resetAreaRuntime() {
        areaMineTarget = null;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        areaAimFailures = 0;
        areaNavIndex = 0;
        areaStageIndex = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        areaMoveRequested = false;
        areaComplete = false;
        AREA_MINE_SKIPPED.clear();
    }

    private static void pauseAreaMiner(Mod area, String reason) {
        areaMineTarget = null;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        areaMoveRequested = false;
        if (forwardForced) {
            Minecraft.getInstance().options.keyUp.setDown(false);
            forwardForced = false;
        }
        if (attackForced) {
            Minecraft.getInstance().options.keyAttack.setDown(false);
            attackForced = false;
        }
        area.enabled = false;
        save();
        notifyMessage("AREA MINER PAUSED: " + reason, 0xFFFFA56B, 3500L);
        appendDiagnostic("AREA_MINER paused reason=" + reason + " stage=" + areaStageIndex + " lane=" + areaNavIndex);
    }

'''
    s = s[:start] + new_helpers + s[end:]

    # Replace target validation so Area Miner cannot jump between vertical stages.
    old_valid = '''    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || !region.contains(pos)) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }
'''
    new_valid = '''    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || !region.contains(pos)) return false;
        int stages = region.stageCount(AREA_STAGE_HEIGHT);
        if (areaStageIndex < 0 || areaStageIndex >= stages) return false;
        int stageTop = region.stageTopY(areaStageIndex, AREA_STAGE_HEIGHT);
        int stageBottom = region.stageBottomY(areaStageIndex, AREA_STAGE_HEIGHT);
        if (pos.getY() > stageTop || pos.getY() < stageBottom) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }
'''
    rep(old_valid, new_valid, 'area validation')

    # Replace Area Miner targeting/navigation. It now uses one fixed top-to-bottom target order and
    # advances only when the player actually reaches a cell; timers pause instead of skipping cells.
    start = s.index('    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {')
    end = s.index('    private static void faceHorizontal(Player player, double x, double z) {', start)
    new_navigation = '''    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize()) return null;
        int cells = region.navigationCells();
        int stages = region.stageCount(AREA_STAGE_HEIGHT);
        if (cells <= 0 || areaNavIndex < 0 || areaNavIndex >= cells || areaStageIndex < 0 || areaStageIndex >= stages) return null;

        BlockPos lane = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
        if (lane == null) return null;
        int top = region.stageTopY(areaStageIndex, AREA_STAGE_HEIGHT);
        int bottom = region.stageBottomY(areaStageIndex, AREA_STAGE_HEIGHT);

        // AREA1: deterministic top-to-bottom order inside exactly one 5-block stage and one lane cell.
        // Never choose a nearest block from another depth/lane, which prevents view oscillation.
        for (int y = top; y >= bottom; y--) {
            BlockPos pos = new BlockPos(lane.getX(), y, lane.getZ());
            if (validAreaMineTarget(mc, area, pos)) return pos.immutable();
        }
        return null;
    }

    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        if (areaMineTarget != null || areaMineRearmTicks > 0) { areaMoveTicks = 0; return false; }
        AreaRegion region = areaRegion(area);
        if (region == null) return false;
        int cells = region.navigationCells();
        int stages = region.stageCount(AREA_STAGE_HEIGHT);
        if (cells <= 0 || stages <= 0) return false;

        if (areaStageIndex >= stages) {
            areaComplete = true;
            area.enabled = false;
            save();
            notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
            appendDiagnostic("AREA_MINER complete " + region.summary());
            return false;
        }

        if (areaNavIndex >= cells) {
            areaStageIndex++;
            areaNavIndex = 0;
            areaMoveTicks = 0;
            areaMinedThisPass = 0;
            areaAimFailures = 0;
            AREA_MINE_SKIPPED.clear();
            if (areaStageIndex >= stages) {
                areaComplete = true;
                area.enabled = false;
                save();
                notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
                appendDiagnostic("AREA_MINER complete " + region.summary());
            } else {
                notifyMessage("AREA MINER: NEXT 5-BLOCK LAYER " + (areaStageIndex + 1) + "/" + stages, 0xFF75C8FF, 2400L);
                appendDiagnostic("AREA_MINER layer=" + (areaStageIndex + 1) + "/" + stages
                        + " y=" + region.stageTopY(areaStageIndex, AREA_STAGE_HEIGHT) + ".." + region.stageBottomY(areaStageIndex, AREA_STAGE_HEIGHT));
            }
            return false;
        }

        // Always mine the current cell first. If it has nothing reachable in this stage, walk to its
        // exact center. Corner A defines cell zero, so the first lane direction never depends on player yaw.
        BlockPos forwardBlock = findAreaMineTarget(mc, area);
        if (forwardBlock != null) {
            areaMineTarget = forwardBlock;
            areaMineAimTicks = 0;
            areaMoveTicks = 0;
            return false;
        }

        BlockPos nav = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
        if (nav == null) return false;
        double goalX = nav.getX() + 0.5;
        double goalZ = nav.getZ() + 0.5;
        double dx = goalX - mc.player.getX();
        double dz = goalZ - mc.player.getZ();
        double distance = Math.sqrt(dx * dx + dz * dz);

        if (distance < 0.42) {
            areaNavIndex++;
            areaMoveTicks = 0;
            areaAimFailures = 0;
            return false;
        }

        int timeout = Math.max(20, (int) Math.round(area.num("Move Timeout").value));
        if (++areaMoveTicks >= timeout) {
            pauseAreaMiner(area, "PATH BLOCKED AT LANE " + (areaNavIndex + 1));
            areaMoveTicks = 0;
            return false;
        }

        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.30;
    }

'''
    s = s[:start] + new_navigation + s[end:]

    src.write_text(s)

# Replace AreaRegion with start-corner-oriented serpentine math and explicit 5-block stage helpers.
region_path = Path('eio26/com/eio/client/AreaRegion.java')
region_path.write_text('''package com.eio.client;

import net.minecraft.core.BlockPos;

/** Immutable quarry bounds, Corner-A-oriented serpentine navigation and top-down stage math. */
final class AreaRegion {
    static final int MAX_SIDE = 128;

    final int minX;
    final int maxX;
    final int minZ;
    final int maxZ;
    final int topY;
    final int bottomY;
    final int startX;
    final int startZ;
    final int xStep;
    final int zStep;

    private AreaRegion(int minX, int maxX, int minZ, int maxZ, int topY, int bottomY,
                       int startX, int startZ, int xStep, int zStep) {
        this.minX = minX;
        this.maxX = maxX;
        this.minZ = minZ;
        this.maxZ = maxZ;
        this.topY = topY;
        this.bottomY = bottomY;
        this.startX = startX;
        this.startZ = startZ;
        this.xStep = xStep;
        this.zStep = zStep;
    }

    static AreaRegion from(BlockPos a, BlockPos b, int depth) {
        if (a == null || b == null) return null;
        int safeDepth = Math.max(1, Math.min(64, depth));
        int top = Math.max(a.getY(), b.getY());
        int xs = Integer.compare(b.getX(), a.getX());
        int zs = Integer.compare(b.getZ(), a.getZ());
        if (xs == 0) xs = 1;
        if (zs == 0) zs = 1;
        return new AreaRegion(
                Math.min(a.getX(), b.getX()), Math.max(a.getX(), b.getX()),
                Math.min(a.getZ(), b.getZ()), Math.max(a.getZ(), b.getZ()),
                top, top - safeDepth + 1,
                a.getX(), a.getZ(), xs, zs);
    }

    int width() { return maxX - minX + 1; }
    int length() { return maxZ - minZ + 1; }
    int depth() { return topY - bottomY + 1; }

    boolean supportedSize() {
        return width() > 0 && length() > 0 && width() <= MAX_SIDE && length() <= MAX_SIDE;
    }

    int navigationCells() {
        if (!supportedSize()) return 0;
        return width() * length();
    }

    int stageCount(int stageHeight) {
        int h = Math.max(1, stageHeight);
        return (depth() + h - 1) / h;
    }

    int stageTopY(int stage, int stageHeight) {
        int h = Math.max(1, stageHeight);
        int count = stageCount(h);
        int s = Math.max(0, Math.min(Math.max(0, count - 1), stage));
        return topY - s * h;
    }

    int stageBottomY(int stage, int stageHeight) {
        int h = Math.max(1, stageHeight);
        return Math.max(bottomY, stageTopY(stage, h) - h + 1);
    }

    boolean contains(BlockPos pos) {
        return pos != null
                && pos.getX() >= minX && pos.getX() <= maxX
                && pos.getZ() >= minZ && pos.getZ() <= maxZ
                && pos.getY() >= bottomY && pos.getY() <= topY;
    }

    int clampX(double x) { return Math.max(minX, Math.min(maxX, (int) Math.floor(x))); }
    int clampZ(double z) { return Math.max(minZ, Math.min(maxZ, (int) Math.floor(z))); }

    BlockPos navigationCell(int index, int y) {
        int cells = navigationCells();
        if (cells <= 0 || index < 0 || index >= cells) return null;
        int row = index / width();
        int column = index % width();
        int along = (row & 1) == 0 ? column : width() - 1 - column;
        int x = startX + along * xStep;
        int z = startZ + row * zStep;
        int navY = Math.max(bottomY, Math.min(topY, y));
        if (x < minX || x > maxX || z < minZ || z > maxZ) return null;
        return new BlockPos(x, navY, z);
    }

    boolean isRowEnd(int index) {
        int cells = navigationCells();
        return cells > 0 && index >= 0 && index < cells && ((index + 1) % width()) == 0;
    }

    String summary() {
        return minX + "," + minZ + " -> " + maxX + "," + maxZ
                + " | Y " + topY + ".." + bottomY + " | " + width() + "x" + length() + "x" + depth();
    }
}
''')

# Add regression coverage for reverse Corner A orientation and five-block layer boundaries.
test_path = Path('src/test/java/com/eio/client/AreaRegionTest.java')
t = test_path.read_text()
if 'startsSerpentineAtCornerAInEitherDirection' not in t:
    insert = '''
    @Test
    void startsSerpentineAtCornerAInEitherDirection() {
        AreaRegion r = AreaRegion.from(new BlockPos(2, 64, 1), new BlockPos(0, 64, 0), 6);
        assertEquals(new BlockPos(2, 64, 1), r.navigationCell(0, 64));
        assertEquals(new BlockPos(1, 64, 1), r.navigationCell(1, 64));
        assertEquals(new BlockPos(0, 64, 1), r.navigationCell(2, 64));
        assertEquals(new BlockPos(0, 64, 0), r.navigationCell(3, 64));
        assertEquals(new BlockPos(1, 64, 0), r.navigationCell(4, 64));
        assertEquals(new BlockPos(2, 64, 0), r.navigationCell(5, 64));
    }

    @Test
    void splitsDepthIntoFiveBlockStagesFromSurface() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 70, 0), new BlockPos(1, 70, 1), 12);
        assertEquals(3, r.stageCount(5));
        assertEquals(70, r.stageTopY(0, 5));
        assertEquals(66, r.stageBottomY(0, 5));
        assertEquals(65, r.stageTopY(1, 5));
        assertEquals(61, r.stageBottomY(1, 5));
        assertEquals(60, r.stageTopY(2, 5));
        assertEquals(59, r.stageBottomY(2, 5));
    }
'''
    t = t.rsplit('\n}', 1)[0] + insert + '\n}\n'
    test_path.write_text(t)

# Bump Gradle artifact version.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.26.0+26.3' in g:
    g = g.replace('mod_version=0.26.0+26.3', 'mod_version=0.27.0+26.3', 1)
elif 'mod_version=0.27.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)
