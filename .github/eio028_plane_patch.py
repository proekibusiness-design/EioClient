from pathlib import Path

SRC = Path('eio26/EioClient.java')
REGION = Path('eio26/com/eio/client/AreaRegion.java')
TEST = Path('src/test/java/com/eio/client/AreaRegionTest.java')
PROPS = Path('gradle.properties')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch target not found: {label}')
    return text.replace(old, new, 1)


def replace_section(text, start, end, replacement, label):
    a = text.find(start)
    if a < 0:
        raise SystemExit(f'section start not found: {label}')
    b = text.find(end, a)
    if b < 0:
        raise SystemExit(f'section end not found: {label}')
    return text[:a] + replacement + text[b:]

s = SRC.read_text()
if 'public static final String VERSION = "0.28.0";' not in s:
    s = replace_once(s, 'public static final String VERSION = "0.27.0";', 'public static final String VERSION = "0.28.0";', 'version')
    s = replace_once(s, 'public static final String BUILD_ID = "EIO-027-STAGE1";', 'public static final String BUILD_ID = "EIO-028-PLANE1";', 'build id')

    s = replace_once(
        s,
        '    private static int areaStageIndex;\n    private static int areaMoveTicks;',
        '    private static int areaStageIndex;\n    private static int areaLayerIndex;\n    private static int areaStallPasses;\n    private static int areaMoveTicks;',
        'area layer state')

    s = replace_once(
        s,
        'mod("Area Miner", "Mining", "Clears a selected rectangle in serpentine tunnel lanes, finishing each 5-block-deep stage before descending to the next one.", -1)',
        'mod("Area Miner", "Mining", "Clears one full horizontal plane at a time in serpentine lanes; five planes form a stage before the next 5-block stage begins.", -1)',
        'area description')
    s = replace_once(
        s,
        '.bool("Exposed Only", true, "Mine only exposed blocks; each 5-block stage is revisited until it is completely clear.")',
        '.bool("Exposed Only", true, "Mine only exposed blocks; each horizontal plane is revisited until it is completely clear.")',
        'area exposed description')

    new_status = '''    private static String areaStatus(Mod area) {
        AreaRegion region = areaRegion(area);
        if (region == null) return "Area Miner: set Corner A and Corner B";
        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;
        int stage = Math.max(0, Math.min(areaStageIndex, region.stageCount() - 1));
        int layers = region.stageLayerCount(stage);
        int layer = Math.max(0, Math.min(areaLayerIndex, Math.max(0, layers - 1)));
        int planeY = region.stageLayerY(stage, layer);
        String stageText = "stage " + (stage + 1) + "/" + region.stageCount()
                + " | layer " + (layer + 1) + "/" + layers + " Y=" + planeY;
        return "Area Miner: " + region.summary() + " | " + stageText
                + (areaComplete ? " | complete" : " | lane " + (Math.min(areaNavIndex, Math.max(0, region.navigationCells() - 1)) + 1) + "/" + region.navigationCells());
    }

'''
    s = replace_section(s, '    private static String areaStatus(Mod area) {', '    private static void resetAreaRuntime() {', new_status, 'area status')

    new_reset = '''    private static void resetAreaRuntime() {
        areaMineTarget = null;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        areaNavIndex = 0;
        areaStageIndex = 0;
        areaLayerIndex = 0;
        areaStallPasses = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        areaMoveRequested = false;
        areaComplete = false;
        AREA_MINE_SKIPPED.clear();
    }

'''
    s = replace_section(s, '    private static void resetAreaRuntime() {', '    private static boolean validAreaMineTarget(', new_reset, 'area reset')

    new_valid = '''    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || !region.containsPlane(pos, areaStageIndex, areaLayerIndex)) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }

'''
    s = replace_section(s, '    private static boolean validAreaMineTarget(', '    private static BlockPos findAreaMineTarget(', new_valid, 'area validity')

    new_find = '''    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || areaStageIndex >= region.stageCount()) return null;
        int cells = region.navigationCells();
        if (cells <= 0) return null;
        int baseIndex = Math.max(0, Math.min(areaNavIndex, cells - 1));
        int targetY = region.stageLayerY(areaStageIndex, areaLayerIndex);
        BlockPos best = null;
        double bestScore = Double.MAX_VALUE;
        int lookAhead = Math.min(4, cells - baseIndex);
        int playerX = (int) Math.floor(mc.player.getX());
        int playerZ = (int) Math.floor(mc.player.getZ());
        int playerFloorY = (int) Math.floor(mc.player.getY()) - 1;
        for (int step = 0; step < lookAhead; step++) {
            BlockPos lane = region.navigationCell(baseIndex + step, targetY);
            if (lane == null) continue;
            BlockPos pos = new BlockPos(lane.getX(), targetY, lane.getZ());
            if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;
            // Do not choose the supporting block directly under the player while other lane blocks exist.
            if (pos.getX() == playerX && pos.getZ() == playerZ && pos.getY() <= playerFloorY) continue;
            double dx = pos.getX() + 0.5 - mc.player.getX();
            double dy = pos.getY() + 0.5 - mc.player.getEyeY();
            double dz = pos.getZ() + 0.5 - mc.player.getZ();
            double score = step * 1000.0 + dx * dx + dy * dy + dz * dz;
            if (score < bestScore) { bestScore = score; best = pos.immutable(); }
        }
        return best;
    }

'''
    s = replace_section(s, '    private static BlockPos findAreaMineTarget(', '    private static boolean areaStageHasBlocks(', new_find, 'area target finder')

    new_progress = '''    private static boolean areaPlaneHasBlocks(Minecraft mc, Mod area, AreaRegion region, int stage, int layer) {
        if (mc.level == null || region == null || stage < 0 || stage >= region.stageCount()) return false;
        int y = region.stageLayerY(stage, layer);
        for (int z = region.minZ; z <= region.maxZ; z++) {
            for (int x = region.minX; x <= region.maxX; x++) {
                BlockPos pos = new BlockPos(x, y, z);
                var state = mc.level.getBlockState(pos);
                if (!state.isAir() && state.getDestroySpeed(mc.level, pos) >= 0.0f) return true;
            }
        }
        return false;
    }

    private static boolean advanceAreaPlaneIfReady(Minecraft mc, Mod area, AreaRegion region) {
        if (areaNavIndex < region.navigationCells()) return false;
        if (areaMinedThisPass > 0) {
            areaNavIndex = 0;
            areaMinedThisPass = 0;
            areaStallPasses = 0;
            areaMoveTicks = 0;
            AREA_MINE_SKIPPED.clear();
            return true;
        }
        if (areaPlaneHasBlocks(mc, area, region, areaStageIndex, areaLayerIndex)) {
            if (areaStallPasses++ < 2) {
                areaNavIndex = 0;
                areaMoveTicks = 0;
                AREA_MINE_SKIPPED.clear();
                return true;
            }
            int y = region.stageLayerY(areaStageIndex, areaLayerIndex);
            area.enabled = false;
            save();
            notifyMessage("AREA MINER PAUSED: Y " + y + " HAS UNREACHABLE BLOCKS", 0xFFFFB36B, 4200L);
            appendDiagnostic("AREA_MINER stalled stage=" + (areaStageIndex + 1) + " layer=" + (areaLayerIndex + 1) + " y=" + y);
            return true;
        }

        areaLayerIndex++;
        areaNavIndex = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        areaStallPasses = 0;
        areaMineTarget = null;
        areaMineAimTicks = 0;
        areaMineRearmTicks = 1;
        AREA_MINE_SKIPPED.clear();

        if (areaLayerIndex >= region.stageLayerCount(areaStageIndex)) {
            areaStageIndex++;
            areaLayerIndex = 0;
            if (areaStageIndex >= region.stageCount()) {
                areaComplete = true;
                area.enabled = false;
                save();
                notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3200L);
                return true;
            }
            notifyMessage("AREA MINER: STARTING STAGE " + (areaStageIndex + 1) + "/" + region.stageCount()
                    + " AT Y " + region.stageLayerY(areaStageIndex, 0), 0xFF74C8F0, 2400L);
            return true;
        }

        notifyMessage("AREA MINER: NEXT PLANE Y " + region.stageLayerY(areaStageIndex, areaLayerIndex), 0xFF74C8F0, 1400L);
        return true;
    }

'''
    s = replace_section(s, '    private static boolean areaStageHasBlocks(', '    private static boolean updateAreaNavigation(', new_progress, 'area plane progression')

    s = replace_once(s, '            if (advanceAreaStageIfReady(mc, area, region)) return false;', '            if (advanceAreaPlaneIfReady(mc, area, region)) return false;', 'area advance call')
    s = replace_once(s, '            BlockPos nav = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());', '            BlockPos nav = region.navigationCell(areaNavIndex, region.stageLayerY(areaStageIndex, areaLayerIndex));', 'area nav plane')

    SRC.write_text(s)

r = REGION.read_text()
if 'int stageLayerCount(int stage)' not in r:
    anchor = '''    int stageBottomY(int stage) {
        return Math.max(bottomY, stageTopY(stage) - STAGE_DEPTH + 1);
    }
'''
    insert = anchor + '''
    int stageLayerCount(int stage) {
        return stageTopY(stage) - stageBottomY(stage) + 1;
    }

    int stageLayerY(int stage, int layer) {
        int count = stageLayerCount(stage);
        int safeLayer = Math.max(0, Math.min(Math.max(0, count - 1), layer));
        return stageTopY(stage) - safeLayer;
    }
'''
    r = replace_once(r, anchor, insert, 'AreaRegion layer helpers')

    anchor2 = '''    boolean containsStage(BlockPos pos, int stage) {
        return contains(pos) && stage >= 0 && stage < stageCount()
                && pos.getY() <= stageTopY(stage) && pos.getY() >= stageBottomY(stage);
    }
'''
    insert2 = anchor2 + '''
    boolean containsPlane(BlockPos pos, int stage, int layer) {
        return containsStage(pos, stage) && pos.getY() == stageLayerY(stage, layer);
    }
'''
    r = replace_once(r, anchor2, insert2, 'AreaRegion plane containment')
    REGION.write_text(r)

t = TEST.read_text()
if 'clearsPlanesTopDownInsideFiveBlockStages' not in t:
    marker = '\n    @Test\n    void rejectsOversizedNavigationArea() {'
    test_method = '''
    @Test
    void clearsPlanesTopDownInsideFiveBlockStages() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 70, 0), new BlockPos(2, 70, 2), 12);
        assertEquals(5, r.stageLayerCount(0));
        assertEquals(70, r.stageLayerY(0, 0));
        assertEquals(69, r.stageLayerY(0, 1));
        assertEquals(66, r.stageLayerY(0, 4));
        assertEquals(65, r.stageLayerY(1, 0));
        assertEquals(61, r.stageLayerY(1, 4));
        assertEquals(2, r.stageLayerCount(2));
        assertEquals(60, r.stageLayerY(2, 0));
        assertEquals(59, r.stageLayerY(2, 1));
        assertTrue(r.containsPlane(new BlockPos(1, 69, 1), 0, 1));
        assertFalse(r.containsPlane(new BlockPos(1, 68, 1), 0, 1));
    }
'''
    if marker not in t:
        raise SystemExit('test insertion marker not found')
    t = t.replace(marker, test_method + marker, 1)
    TEST.write_text(t)

p = PROPS.read_text()
if 'mod_version=0.27.0+26.3' in p:
    p = p.replace('mod_version=0.27.0+26.3', 'mod_version=0.28.0+26.3', 1)
elif 'mod_version=0.28.0+26.3' not in p:
    raise SystemExit('unexpected mod version in gradle.properties')
PROPS.write_text(p)

print('0.28 plane-first Area Miner patch applied')
