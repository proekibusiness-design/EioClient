from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

def rep(old, new, label, count=1):
    global s
    if old not in s:
        if new in s:
            return
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

rep('public static final String VERSION = "0.29.0";',
    'public static final String VERSION = "0.30.0";', 'version')
rep('public static final String BUILD_ID = "EIO-029-LANE1";',
    'public static final String BUILD_ID = "EIO-030-STAGE1";', 'build id')

rep('''    private static int areaMinedThisPass;\n    private static boolean areaMoveRequested;''',
    '''    private static int areaMinedThisPass;\n    private static int areaStageSweeps;\n    private static boolean areaMoveRequested;''', 'stage sweep state')

rep('''        mod("Area Miner", "Mining", "Walks deterministic serpentine lanes and continuously mines the valid lane block currently under the crosshair.", -1)''',
    '''        mod("Area Miner", "Mining", "Clears the selected quarry in strict five-block-deep bands, finishing the whole active band before descending.", -1)''', 'area description')
rep('''                .num("Depth", 10.0, 1.0, 64.0, 1.0, "Total depth below the surface. Area Miner processes this in fixed 5-block stages.")''',
    '''                .num("Depth", 10.0, 1.0, 64.0, 1.0, "Total depth below the surface. Eio completely clears each 5-block band before entering the next one.")''', 'depth description')

rep('''        int planeY = region.stageLayerY(stage, layer);\n        String stageText = "stage " + (stage + 1) + "/" + region.stageCount()\n                + " | layer " + (layer + 1) + "/" + layers + " Y=" + planeY;''',
    '''        int planeY = region.stageLayerY(stage, layer);\n        int bandTop = region.stageTopY(stage);\n        int bandBottom = region.stageBottomY(stage);\n        String stageText = "stage " + (stage + 1) + "/" + region.stageCount()\n                + " | band Y " + bandTop + ".." + bandBottom\n                + " | plane " + (layer + 1) + "/" + layers + " Y=" + planeY;''', 'status band')

rep('''        areaMinedThisPass = 0;\n        areaMoveRequested = false;''',
    '''        areaMinedThisPass = 0;\n        areaStageSweeps = 0;\n        areaMoveRequested = false;''', 'reset stage sweeps')

rep('''        AreaRegion region = areaRegion(area);\n        if (region == null || !region.supportedSize() || !region.containsPlane(pos, areaStageIndex, areaLayerIndex)) return false;''',
    '''        AreaRegion region = areaRegion(area);\n        if (region == null || !region.supportedSize()) return false;\n        // Hard invariant: Area Miner may never target outside the current five-block band.\n        if (!region.containsStage(pos, areaStageIndex) || !region.containsPlane(pos, areaStageIndex, areaLayerIndex)) return false;''', 'hard stage target gate')

rep('''        BlockPos looked = hit.getBlockPos();\n        if (!validAreaMineTarget(mc, area, looked)) return null;\n        AreaRegion region = areaRegion(area);\n        if (region == null) return null;''',
    '''        BlockPos looked = hit.getBlockPos();\n        AreaRegion region = areaRegion(area);\n        if (region == null || areaStageIndex < 0 || areaStageIndex >= region.stageCount()) return null;\n        // Never accept a crosshair block above/below the active five-block band.\n        if (looked.getY() > region.stageTopY(areaStageIndex) || looked.getY() < region.stageBottomY(areaStageIndex)) return null;\n        if (!validAreaMineTarget(mc, area, looked)) return null;''', 'crosshair stage gate')

plane_method = '''    private static boolean areaPlaneHasBlocks(Minecraft mc, Mod area, AreaRegion region, int stage, int layer) {\n        if (mc.level == null || region == null || stage < 0 || stage >= region.stageCount()) return false;\n        int y = region.stageLayerY(stage, layer);\n        for (int z = region.minZ; z <= region.maxZ; z++) {\n            for (int x = region.minX; x <= region.maxX; x++) {\n                BlockPos pos = new BlockPos(x, y, z);\n                var state = mc.level.getBlockState(pos);\n                if (!state.isAir() && state.getDestroySpeed(mc.level, pos) >= 0.0f) return true;\n            }\n        }\n        return false;\n    }\n'''
stage_method = plane_method + '''\n    private static boolean areaStageHasBlocks(Minecraft mc, AreaRegion region, int stage) {\n        if (mc.level == null || region == null || stage < 0 || stage >= region.stageCount()) return false;\n        int top = region.stageTopY(stage);\n        int bottom = region.stageBottomY(stage);\n        for (int y = top; y >= bottom; y--) {\n            for (int z = region.minZ; z <= region.maxZ; z++) {\n                for (int x = region.minX; x <= region.maxX; x++) {\n                    BlockPos pos = new BlockPos(x, y, z);\n                    var state = mc.level.getBlockState(pos);\n                    if (!state.isAir() && state.getDestroySpeed(mc.level, pos) >= 0.0f) return true;\n                }\n            }\n        }\n        return false;\n    }\n'''
rep(plane_method, stage_method, 'whole-stage scanner')

old_stage_advance = '''        if (areaLayerIndex >= region.stageLayerCount(areaStageIndex)) {\n            areaStageIndex++;\n            areaLayerIndex = 0;\n            if (areaStageIndex >= region.stageCount()) {\n                areaComplete = true;\n                area.enabled = false;\n                save();\n                notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3200L);\n                return true;\n            }\n            notifyMessage("AREA MINER: STARTING STAGE " + (areaStageIndex + 1) + "/" + region.stageCount()\n                    + " AT Y " + region.stageLayerY(areaStageIndex, 0), 0xFF74C8F0, 2400L);\n            return true;\n        }'''
new_stage_advance = '''        if (areaLayerIndex >= region.stageLayerCount(areaStageIndex)) {\n            int completedStage = areaStageIndex;\n            // Do not descend even one block into the next band until every breakable block\n            // in this five-block band has been cleared. This is the stage barrier.\n            if (areaStageHasBlocks(mc, region, completedStage)) {\n                areaStageSweeps++;\n                if (areaStageSweeps <= 3) {\n                    areaLayerIndex = 0;\n                    areaNavIndex = 0;\n                    areaMoveTicks = 0;\n                    areaMinedThisPass = 0;\n                    areaStallPasses = 0;\n                    areaMineTarget = null;\n                    areaMineAimTicks = 0;\n                    areaMineRearmTicks = 1;\n                    AREA_MINE_SKIPPED.clear();\n                    notifyMessage("AREA MINER: FINISHING BAND Y " + region.stageTopY(completedStage)\n                            + ".." + region.stageBottomY(completedStage), 0xFF74C8F0, 1800L);\n                    return true;\n                }\n                area.enabled = false;\n                save();\n                notifyMessage("AREA MINER PAUSED: ACTIVE 5-BLOCK BAND IS NOT CLEAR", 0xFFFFB36B, 4200L);\n                appendDiagnostic("AREA_MINER stage_gate_stall stage=" + (completedStage + 1)\n                        + " band=" + region.stageTopY(completedStage) + ".." + region.stageBottomY(completedStage));\n                return true;\n            }\n\n            areaStageSweeps = 0;\n            areaStageIndex++;\n            areaLayerIndex = 0;\n            if (areaStageIndex >= region.stageCount()) {\n                areaComplete = true;\n                area.enabled = false;\n                save();\n                notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3200L);\n                return true;\n            }\n            notifyMessage("AREA MINER: BAND CLEAR - DESCENDING TO Y " + region.stageTopY(areaStageIndex)\n                    + ".." + region.stageBottomY(areaStageIndex), 0xFF74C8F0, 2400L);\n            return true;\n        }'''
rep(old_stage_advance, new_stage_advance, 'strict stage advance')

src.write_text(s)

# Version bump.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.29.0+26.3' in g:
    g = g.replace('mod_version=0.29.0+26.3', 'mod_version=0.30.0+26.3', 1)
elif 'mod_version=0.30.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)

# Regression tests for strict non-overlapping five-block stage windows.
test = Path('src/test/java/com/eio/client/AreaRegionTest.java')
t = test.read_text()
if 'stageBandsAreStrictAndNonOverlapping' not in t:
    marker = '''    @Test\n    void rejectsOversizedNavigationArea() {'''
    addition = '''    @Test\n    void stageBandsAreStrictAndNonOverlapping() {\n        AreaRegion r = AreaRegion.from(new BlockPos(0, 70, 0), new BlockPos(2, 70, 2), 12);\n        assertEquals(5, r.stageLayerCount(0));\n        assertEquals(5, r.stageLayerCount(1));\n        assertEquals(2, r.stageLayerCount(2));\n\n        for (int y = 70; y >= 59; y--) {\n            int memberships = 0;\n            for (int stage = 0; stage < r.stageCount(); stage++) {\n                if (r.containsStage(new BlockPos(1, y, 1), stage)) memberships++;\n            }\n            assertEquals(1, memberships, "Y=" + y + " must belong to exactly one stage");\n        }\n\n        assertFalse(r.containsStage(new BlockPos(1, 65, 1), 0));\n        assertTrue(r.containsStage(new BlockPos(1, 65, 1), 1));\n        assertFalse(r.containsStage(new BlockPos(1, 60, 1), 1));\n        assertTrue(r.containsStage(new BlockPos(1, 60, 1), 2));\n    }\n\n''' + marker
    if marker not in t:
        raise SystemExit('test insertion target not found')
    t = t.replace(marker, addition, 1)
    test.write_text(t)

print('0.30 strict five-block stage patch applied')
