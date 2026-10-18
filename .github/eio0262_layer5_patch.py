from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

if 'public static final String VERSION = "0.26.2";' not in s:
    rep('public static final String VERSION = "0.26.1";', 'public static final String VERSION = "0.26.2";', 'version')
    rep('public static final String BUILD_ID = "EIO-0261-MINEFIX1";', 'public static final String BUILD_ID = "EIO-0262-LAYER5";', 'build id')

    rep('''    private static int areaNavIndex;
    private static int areaMoveTicks;''', '''    private static int areaNavIndex;
    private static int areaLayerIndex;
    private static int areaMoveTicks;''', 'area layer field')

    rep('''                .num("Depth", 8.0, 1.0, 64.0, 1.0, "Vertical depth included in the selected zone. Area Miner only targets the current serpentine lane column instead of mining surrounding blocks.")''', '''                .num("Depth", 8.0, 1.0, 64.0, 1.0, "Total quarry depth. Area Miner clears the whole selected area in five-block top-down slabs before descending to the next slab.")''', 'depth help')

    rep('''        return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | lane " + Math.min(region.navigationCells(), areaNavIndex + 1) + "/" + region.navigationCells());''', '''        return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | " + region.layerSummary(areaLayerIndex)
                + " | lane " + Math.min(region.navigationCells(), areaNavIndex + 1) + "/" + region.navigationCells());''', 'area status')

    rep('''        areaNavIndex = 0;
        areaMoveTicks = 0;''', '''        areaNavIndex = 0;
        areaLayerIndex = 0;
        areaMoveTicks = 0;''', 'area reset layer')

    rep('''        if (region == null || !region.supportedSize()) return null;
        int cells = region.navigationCells();
        if (cells <= 0 || areaNavIndex < 0 || areaNavIndex >= cells) return null;

        // AREA2: only clear the column for the current serpentine lane cell. This deliberately
        // avoids the old radius scan that could turn around and mine unrelated blocks behind/aside.
        BlockPos lane = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
        if (lane == null) return null;
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int y = region.topY; y >= region.bottomY; y--) {''', '''        if (region == null || !region.supportedSize() || !region.hasLayer(areaLayerIndex)) return null;
        int cells = region.navigationCells();
        if (cells <= 0 || areaNavIndex < 0 || areaNavIndex >= cells) return null;

        // Mine only the active five-block slab. The whole horizontal serpentine pass must be
        // proven clear before Area Miner is allowed to descend to the next slab.
        BlockPos lane = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
        if (lane == null) return null;
        int layerTop = region.layerTopY(areaLayerIndex);
        int layerBottom = region.layerBottomY(areaLayerIndex);
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int y = layerTop; y >= layerBottom; y--) {''', 'layer-limited target scan')

    rep('''            if (areaNavIndex >= cells) {
                if (areaMinedThisPass <= 0) {
                    areaComplete = true;
                    area.enabled = false;
                    save();
                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
                    appendDiagnostic("AREA_MINER complete " + region.summary());
                    return false;
                }
                // One serpentine pass exposed/mined more blocks. Start the same lanes again so
                // deeper configured blocks become reachable without ever radius-mining around the player.
                areaNavIndex = 0;
                areaMinedThisPass = 0;
                AREA_MINE_SKIPPED.clear();
            }''', '''            if (areaNavIndex >= cells) {
                if (areaMinedThisPass > 0) {
                    // Something changed in this slab, so sweep this same five-block layer again.
                    // We do not descend until an entire serpentine verification pass mines zero blocks.
                    areaNavIndex = 0;
                    areaMinedThisPass = 0;
                    AREA_MINE_SKIPPED.clear();
                } else if (region.hasLayer(areaLayerIndex + 1)) {
                    areaLayerIndex++;
                    areaNavIndex = 0;
                    areaMinedThisPass = 0;
                    areaMoveTicks = 0;
                    AREA_MINE_SKIPPED.clear();
                    stopAreaDestroy(mc);
                    notifyMessage("AREA MINER: " + region.layerSummary(areaLayerIndex).toUpperCase(Locale.ROOT), 0xFF76C7FF, 2200L);
                    appendDiagnostic("AREA_MINER descend " + region.layerSummary(areaLayerIndex));
                } else {
                    areaComplete = true;
                    area.enabled = false;
                    save();
                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
                    appendDiagnostic("AREA_MINER complete " + region.summary());
                    return false;
                }
            }''', 'layer transition scheduler')

    src.write_text(s)

# Version metadata is canonicalized only after the transformed source passes CI.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.26.1+26.3' in g:
    g = g.replace('mod_version=0.26.1+26.3', 'mod_version=0.26.2+26.3', 1)
elif 'mod_version=0.26.2+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)
