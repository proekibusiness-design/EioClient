from pathlib import Path
import re

SRC = Path('eio26/EioClient.java')
s = SRC.read_text()

if 'public static final String VERSION = "0.27.0";' in s:
    print('0.27 source already patched')
else:
    if 'public static final String VERSION = "0.26.0";' not in s:
        raise SystemExit('expected canonical 0.26 source')

    s = s.replace('public static final String VERSION = "0.26.0";', 'public static final String VERSION = "0.27.0";', 1)
    s = s.replace('public static final String BUILD_ID = "EIO-026-AREA1";', 'public static final String BUILD_ID = "EIO-027-LAYER1";', 1)

    old_state = '''    private static int areaNavIndex;\n    private static int areaMoveTicks;\n    private static int areaMinedThisPass;\n    private static boolean areaMoveRequested;'''
    new_state = '''    private static int areaLayerIndex;\n    private static int areaNavIndex;\n    private static int areaMoveTicks;\n    private static int areaMinedThisPass;\n    private static boolean areaMoveRequested;'''
    if old_state not in s: raise SystemExit('area state anchor missing')
    s = s.replace(old_state, new_state, 1)

    old_module = '''        mod("Area Miner", "Mining", "Mines a user-defined rectangular area to a chosen depth and can move through the selected coordinates.", -1)\n                .point("Corner A", "Stand at the first horizontal corner and left-click this row to set it here. Right-click clears it.")\n                .point("Corner B", "Stand at the opposite horizontal corner and left-click this row to set it here. Right-click clears it.")\n                .num("Depth", 8.0, 1.0, 64.0, 1.0, "Number of blocks to mine downward from the higher corner Y level.")\n                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next area target.")\n                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to line up with a target before temporarily skipping it.")\n                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one navigation cell before moving to the next cell.")\n                .bool("Auto Move", true, "Move through the configured rectangle when no mineable block is currently in normal interaction range.")\n                .bool("Sprint", false, "Sprint while Area Miner is navigating between cells.")\n                .bool("Auto Jump", true, "Jump over simple one-block obstacles while Area Miner is moving.")\n                .bool("Exposed Only", true, "Mine only blocks with an air-adjacent face, exposing deeper layers progressively.")\n                .bool("Face Block", true, "Turn your view toward the current Area Miner target.");'''
    new_module = '''        mod("Area Miner", "Mining", "Excavates only below the selected surface in strict 5-block slices, clearing each slice in straight serpentine lanes before descending.", -1)\n                .point("Corner A", "Stand at the first surface corner and left-click this row to set it here. Right-click clears it.")\n                .point("Corner B", "Stand at the opposite surface corner and left-click this row to set it here. Right-click clears it.")\n                .num("Depth", 20.0, 5.0, 64.0, 5.0, "Total excavation depth below the selected surface. Area Miner finishes each 5-block slice before going 5 blocks deeper.")\n                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next area target.")\n                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to line up with a target before temporarily skipping it.")\n                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one serpentine navigation cell before advancing.")\n                .bool("Auto Move", true, "Move in straight back-and-forth lanes inside the selected rectangle while clearing the current 5-block slice.")\n                .bool("Sprint", false, "Sprint while Area Miner is navigating a lane.")\n                .bool("Auto Jump", true, "Jump over simple one-block obstacles while Area Miner is moving.")\n                .bool("Exposed Only", true, "Mine exposed blocks first. Deeper blocks become eligible as the slice opens up.")\n                .bool("Face Block", true, "Turn your view toward the current Area Miner target.");'''
    if old_module not in s: raise SystemExit('Area Miner module anchor missing')
    s = s.replace(old_module, new_module, 1)

    # Clean an accidental duplicated PointSetting reset branch while touching config code.
    s = s.replace('''                else if (setting instanceof MobListSetting ml) ml.reset();\n            else if (setting instanceof PointSetting point) point.reset();\n                else if (setting instanceof PointSetting point) point.reset();''',
                  '''                else if (setting instanceof MobListSetting ml) ml.reset();\n                else if (setting instanceof PointSetting point) point.reset();''', 1)

    # Replace the entire Area Miner helper/navigation section. The new logic has a hard current-slice invariant.
    pattern = re.compile(r'    private static AreaRegion areaRegion\(Mod area\) \{.*?\n    private static void faceHorizontal\(Player player, double x, double z\) \{', re.S)
    match = pattern.search(s)
    if not match: raise SystemExit('Area Miner helper block not found')
    replacement = r'''    private static AreaRegion areaRegion(Mod area) {
        if (area == null) return null;
        PointSetting a = area.point("Corner A"), b = area.point("Corner B");
        return AreaRegion.from(a.value, b.value, (int) Math.round(area.num("Depth").value));
    }

    private static boolean areaConfigured(Mod area) {
        AreaRegion region = areaRegion(area);
        return region != null && region.supportedSize();
    }

    private static String areaStatus(Mod area) {
        AreaRegion region = areaRegion(area);
        if (region == null) return "Area Miner: set Corner A and Corner B";
        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;
        if (areaComplete) return "Area Miner: complete | " + region.summary();
        int layer = Math.max(0, Math.min(areaLayerIndex, Math.max(0, region.layerCount() - 1)));
        return "Area Miner: layer " + (layer + 1) + "/" + region.layerCount()
                + " Y " + region.layerTop(layer) + ".." + region.layerBottom(layer)
                + " | lane " + (Math.min(areaNavIndex, Math.max(0, region.navigationCells() - 1)) / Math.max(1, region.width()) + 1)
                + "/" + region.length() + " | " + region.minX + "," + region.minZ + " -> " + region.maxX + "," + region.maxZ;
    }

    private static void resetAreaRuntime() {
        areaMineTarget = null;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        areaLayerIndex = 0;
        areaNavIndex = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        areaMoveRequested = false;
        areaComplete = false;
        AREA_MINE_SKIPPED.clear();
    }

    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || areaLayerIndex < 0 || areaLayerIndex >= region.layerCount()) return false;
        // Hard safety invariant: coordinates are the SURFACE plane. The miner may only touch blocks below it,
        // and only inside the active 5-block slice. It cannot select blocks on/above the marker Y or in deeper slices.
        if (!region.containsInLayer(pos, areaLayerIndex)) return false;
        if (pos.getY() >= region.surfaceY) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }

    private static boolean areaLayerHasMineableBlocks(Minecraft mc, AreaRegion region, int layer) {
        if (mc.level == null || layer < 0 || layer >= region.layerCount()) return false;
        int top = region.layerTop(layer), bottom = region.layerBottom(layer);
        for (int z = region.minZ; z <= region.maxZ; z++) {
            for (int x = region.minX; x <= region.maxX; x++) {
                for (int y = top; y >= bottom; y--) {
                    BlockPos pos = new BlockPos(x, y, z);
                    var state = mc.level.getBlockState(pos);
                    if (!state.isAir() && state.getDestroySpeed(mc.level, pos) >= 0.0f) return true;
                }
            }
        }
        return false;
    }

    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || areaLayerIndex >= region.layerCount()) return null;
        int cells = region.navigationCells();
        if (cells <= 0) return null;
        int current = Math.max(0, Math.min(areaNavIndex, cells - 1));
        int row = current / region.width();
        int rowEnd = Math.min(cells - 1, (row + 1) * region.width() - 1);

        // Only search forward through the CURRENT serpentine lane. This prevents nearest-block/random-area behavior.
        // Every candidate is also limited to the current 5-block slice by validAreaMineTarget().
        for (int index = current; index <= rowEnd; index++) {
            BlockPos lane = region.navigationCell(index, region.layerTop(areaLayerIndex));
            if (lane == null) continue;
            for (int y = region.layerTop(areaLayerIndex); y >= region.layerBottom(areaLayerIndex); y--) {
                BlockPos pos = new BlockPos(lane.getX(), y, lane.getZ());
                if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;
                return pos.immutable();
            }
        }
        return null;
    }

    private static boolean finishOrAdvanceAreaLayer(Minecraft mc, Mod area, AreaRegion region) {
        if (areaLayerHasMineableBlocks(mc, region, areaLayerIndex)) {
            // A pass can leave temporarily unreachable/interior blocks. Retry the same slice from lane 1.
            areaNavIndex = 0;
            areaMoveTicks = 0;
            areaMinedThisPass = 0;
            AREA_MINE_SKIPPED.clear();
            return false;
        }
        areaLayerIndex++;
        areaNavIndex = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        AREA_MINE_SKIPPED.clear();
        areaMineTarget = null;
        if (areaLayerIndex >= region.layerCount()) {
            areaComplete = true;
            area.enabled = false;
            save();
            notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
            return true;
        }
        notifyMessage("AREA MINER: NEXT 5-BLOCK LAYER", 0xFF8FDCC0, 1800L);
        return false;
    }

    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || areaLayerIndex >= region.layerCount()) return false;
        if (areaMineTarget != null || areaMineRearmTicks > 0) { areaMoveTicks = 0; return false; }

        BlockPos reachable = findAreaMineTarget(mc, area);
        if (reachable != null) {
            areaMineTarget = reachable;
            areaMineAimTicks = 0;
            areaMoveTicks = 0;
            return false;
        }

        int cells = region.navigationCells();
        if (cells <= 0) return false;
        if (areaNavIndex >= cells) {
            if (finishOrAdvanceAreaLayer(mc, area, region)) return false;
            if (areaLayerIndex >= region.layerCount()) return false;
        }

        BlockPos nav = region.navigationCell(areaNavIndex, region.layerTop(areaLayerIndex));
        if (nav == null) return false;
        double goalX = nav.getX() + 0.5;
        double goalZ = nav.getZ() + 0.5;
        double dx = goalX - mc.player.getX(), dz = goalZ - mc.player.getZ();
        double distance = Math.sqrt(dx * dx + dz * dz);

        if (distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        if (++areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
            // Never leave the layer because of a navigation timeout; move to the next cell and retry leftovers later.
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.45;
    }

    private static void faceHorizontal(Player player, double x, double z) {'''
    s = s[:match.start()] + replacement + s[match.end():]

    SRC.write_text(s)

# Version metadata.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.26.0+26.3' in g:
    gp.write_text(g.replace('mod_version=0.26.0+26.3', 'mod_version=0.27.0+26.3', 1))
elif 'mod_version=0.27.0+26.3' not in g:
    raise SystemExit('unexpected mod_version')

# AreaRegion: coordinates are a surface plane, excavation begins one block BELOW it.
rp = Path('eio26/com/eio/client/AreaRegion.java')
r = rp.read_text()
r = r.replace('''    final int topY;\n    final int bottomY;\n\n    private AreaRegion(int minX, int maxX, int minZ, int maxZ, int topY, int bottomY) {''', '''    final int surfaceY;\n    final int topY;\n    final int bottomY;\n\n    private AreaRegion(int minX, int maxX, int minZ, int maxZ, int surfaceY, int topY, int bottomY) {''')
r = r.replace('''        this.minZ = minZ;\n        this.maxZ = maxZ;\n        this.topY = topY;''', '''        this.minZ = minZ;\n        this.maxZ = maxZ;\n        this.surfaceY = surfaceY;\n        this.topY = topY;''')
r = r.replace('''        int safeDepth = Math.max(1, Math.min(64, depth));\n        int top = Math.max(a.getY(), b.getY());\n        return new AreaRegion(\n                Math.min(a.getX(), b.getX()), Math.max(a.getX(), b.getX()),\n                Math.min(a.getZ(), b.getZ()), Math.max(a.getZ(), b.getZ()),\n                top, top - safeDepth + 1);''', '''        int safeDepth = Math.max(5, Math.min(64, depth));\n        int surface = Math.max(a.getY(), b.getY());\n        int mineTop = surface - 1;\n        return new AreaRegion(\n                Math.min(a.getX(), b.getX()), Math.max(a.getX(), b.getX()),\n                Math.min(a.getZ(), b.getZ()), Math.max(a.getZ(), b.getZ()),\n                surface, mineTop, surface - safeDepth);''')
insert = '''\n    int layerCount() { return (depth() + 4) / 5; }\n\n    int layerTop(int layer) {\n        if (layer < 0 || layer >= layerCount()) throw new IllegalArgumentException("layer " + layer);\n        return topY - layer * 5;\n    }\n\n    int layerBottom(int layer) {\n        return Math.max(bottomY, layerTop(layer) - 4);\n    }\n\n    boolean containsInLayer(BlockPos pos, int layer) {\n        return contains(pos) && layer >= 0 && layer < layerCount()\n                && pos.getY() <= layerTop(layer) && pos.getY() >= layerBottom(layer);\n    }\n'''
needle = '    int depth() { return topY - bottomY + 1; }\n'
if insert.strip() not in r:
    if needle not in r: raise SystemExit('AreaRegion depth anchor missing')
    r = r.replace(needle, needle + insert, 1)
r = r.replace('''        return minX + "," + minZ + " -> " + maxX + "," + maxZ\n                + " | Y " + topY + ".." + bottomY + " | " + width() + "x" + length() + "x" + depth();''', '''        return minX + "," + minZ + " -> " + maxX + "," + maxZ\n                + " | surfaceY " + surfaceY + " | mineY " + topY + ".." + bottomY\n                + " | " + width() + "x" + length() + "x" + depth();''')
rp.write_text(r)

# Regression tests now lock the exact surface-below and 5-block-layer semantics.
tp = Path('src/test/java/com/eio/client/AreaRegionTest.java')
t = tp.read_text()
t = t.replace('''        assertEquals(70, r.topY);\n        assertEquals(65, r.bottomY);''', '''        assertEquals(70, r.surfaceY);\n        assertEquals(69, r.topY);\n        assertEquals(64, r.bottomY);''')
t = t.replace('''        assertTrue(r.contains(new BlockPos(1, 63, 1)));\n        assertFalse(r.contains(new BlockPos(3, 63, 1)));\n        assertFalse(r.contains(new BlockPos(1, 60, 1)));''', '''        assertTrue(r.contains(new BlockPos(1, 63, 1)));\n        assertFalse(r.contains(new BlockPos(1, 64, 1)), "surface marker Y itself must never be mined");\n        assertFalse(r.contains(new BlockPos(3, 63, 1)));\n        assertFalse(r.contains(new BlockPos(1, 60, 1)));''')
t = t.replace('''        assertEquals(new BlockPos(0, 64, 0), r.navigationCell(0, 64));\n        assertEquals(new BlockPos(1, 64, 0), r.navigationCell(1, 64));\n        assertEquals(new BlockPos(2, 64, 0), r.navigationCell(2, 64));\n        assertEquals(new BlockPos(2, 64, 1), r.navigationCell(3, 64));\n        assertEquals(new BlockPos(1, 64, 1), r.navigationCell(4, 64));\n        assertEquals(new BlockPos(0, 64, 1), r.navigationCell(5, 64));''', '''        assertEquals(new BlockPos(0, 63, 0), r.navigationCell(0, 64));\n        assertEquals(new BlockPos(1, 63, 0), r.navigationCell(1, 64));\n        assertEquals(new BlockPos(2, 63, 0), r.navigationCell(2, 64));\n        assertEquals(new BlockPos(2, 63, 1), r.navigationCell(3, 64));\n        assertEquals(new BlockPos(1, 63, 1), r.navigationCell(4, 64));\n        assertEquals(new BlockPos(0, 63, 1), r.navigationCell(5, 64));''')
extra = '''\n    @Test\n    void excavatesFiveBlocksAtATimeStrictlyBelowSurface() {\n        AreaRegion r = AreaRegion.from(new BlockPos(0, 70, 0), new BlockPos(3, 70, 3), 12);\n        assertEquals(70, r.surfaceY);\n        assertEquals(69, r.topY);\n        assertEquals(58, r.bottomY);\n        assertEquals(3, r.layerCount());\n        assertEquals(69, r.layerTop(0));\n        assertEquals(65, r.layerBottom(0));\n        assertEquals(64, r.layerTop(1));\n        assertEquals(60, r.layerBottom(1));\n        assertEquals(59, r.layerTop(2));\n        assertEquals(58, r.layerBottom(2));\n        assertTrue(r.containsInLayer(new BlockPos(1, 65, 1), 0));\n        assertFalse(r.containsInLayer(new BlockPos(1, 64, 1), 0));\n        assertFalse(r.contains(new BlockPos(1, 70, 1)));\n    }\n'''
if 'excavatesFiveBlocksAtATimeStrictlyBelowSurface' not in t:
    t = t.rsplit('}', 1)[0] + extra + '}\n'
tp.write_text(t)

print('0.27 layered Area Miner patch applied')
