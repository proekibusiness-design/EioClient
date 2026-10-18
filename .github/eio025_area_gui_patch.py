from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()

# This transformer is intentionally fail-fast. It only applies to the verified 0.24 compatibility source.
def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

rep('public static final String VERSION = "0.24.0";', 'public static final String VERSION = "0.25.0";', 'version')
rep('public static final String BUILD_ID = "EIO-024-COMPAT1";', 'public static final String BUILD_ID = "EIO-025-AREA1";', 'build id')

# --- Area Miner persistent runtime state ---
rep('''    private static final Set<BlockPos> NUKER_SKIPPED = new HashSet<>();\n    private static boolean attackForced;''', '''    private static final Set<BlockPos> NUKER_SKIPPED = new HashSet<>();\n    private static BlockPos areaCornerA;\n    private static BlockPos areaCornerB;\n    private static BlockPos areaMineTarget;\n    private static int areaMineLayerTop = Integer.MIN_VALUE;\n    private static int areaMineLane;\n    private static boolean areaMineReverse;\n    private static int areaMineRearmTicks;\n    private static int areaMineAimTicks;\n    private static final Set<BlockPos> AREA_MINE_SKIPPED = new HashSet<>();\n    private static boolean attackForced;''', 'area state')

# --- module declaration ---
anchor = '''        mod("Chunk Miner", "Mining", "Continuously mines nearby valid blocks in your current chunk, re-arming normal mining input between targets.", -1)'''
area_mod = '''        mod("Area Miner", "Mining", "Clears a rectangular region in 5-block-deep layers using straight serpentine tunnel lanes from the selected surface downward.", -1)\n                .num("Depth", 20.0, 5.0, 128.0, 5.0, "Total depth below the selected surface. Mining progresses 5 blocks at a time.")\n                .num("Tunnel Width", 1.0, 1.0, 5.0, 1.0, "Horizontal lane width cleared before shifting to the next lane.")\n                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack between block targets.")\n                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to acquire a selected block before trying another.")\n                .bool("Face Block", true, "Turn toward each selected block before mining it.")\n                .bool("Auto Move", true, "Move through the current straight lane after nearby blocks ahead are clear.")\n                .bool("Stop On Correction", true, "Pause Area Miner after a server position correction until the compatibility pause ends.");\n\n''' + anchor
rep(anchor, area_mod, 'Area Miner module')

# --- commands to set area corners from player location ---
cmd_anchor = '''                        .then(ClientCommands.literal("waypoint")'''
area_commands = '''                        .then(ClientCommands.literal("area")\n                                .then(ClientCommands.literal("pos1").executes(c -> {\n                                    Minecraft mc = Minecraft.getInstance();\n                                    if (mc.player == null) return 0;\n                                    areaCornerA = mc.player.blockPosition();\n                                    resetAreaMinerProgress();\n                                    c.getSource().sendFeedback(Component.literal("Area Miner pos1 = " + posText(areaCornerA)));\n                                    return 1;\n                                }))\n                                .then(ClientCommands.literal("pos2").executes(c -> {\n                                    Minecraft mc = Minecraft.getInstance();\n                                    if (mc.player == null) return 0;\n                                    areaCornerB = mc.player.blockPosition();\n                                    resetAreaMinerProgress();\n                                    c.getSource().sendFeedback(Component.literal("Area Miner pos2 = " + posText(areaCornerB)));\n                                    return 1;\n                                }))\n                                .then(ClientCommands.literal("clear").executes(c -> {\n                                    areaCornerA = null; areaCornerB = null; resetAreaMinerProgress();\n                                    c.getSource().sendFeedback(Component.literal("Area Miner coordinates cleared"));\n                                    return 1;\n                                }))\n                                .then(ClientCommands.literal("status").executes(c -> {\n                                    c.getSource().sendFeedback(Component.literal(areaMinerStatus()));\n                                    return 1;\n                                })))\n''' + cmd_anchor
rep(cmd_anchor, area_commands, 'area commands')

# --- locate module in tick ---
rep('''        Mod chunkMiner = find("Chunk Miner");\n        Mod nuker = find("Nuker");''', '''        Mod areaMiner = find("Area Miner");\n        Mod chunkMiner = find("Chunk Miner");\n        Mod nuker = find("Nuker");''', 'tick module lookup')

# Disable tunnel auto-walk ownership if Area Miner owns forward movement.
rep('''        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;''', '''        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value && !areaMiner.enabled) shouldForceForward = true;''', 'tunnel forward arbitration')

# Replace mining priority block by giving Area Miner first ownership.
old_mining = '''        boolean miningAllowed = !correctionPause && miningToolSafe(mc);\n        if (nuker.enabled) {'''
new_mining = '''        boolean miningAllowed = !correctionPause && miningToolSafe(mc);\n        if (areaMiner.enabled) {\n            miningAllowed = miningAllowed && areaMinerReady();\n            boolean wantsAttack = runAreaMiner(mc, areaMiner, miningAllowed);\n            setAttackOwned(mc, wantsAttack);\n            if (areaMiner.bool("Auto Move").value && miningAllowed && areaMineTarget == null && areaMinerHasCurrentLane(mc, areaMiner)) {\n                shouldForceForward = true;\n                setForwardOwned(mc, true);\n            }\n        } else if (nuker.enabled) {'''
rep(old_mining, new_mining, 'mining priority')

# Avoid later release of attack in the no-miner branch by making Area Miner part of the condition.
rep('''        } else if (chunkMiner.enabled) {''', '''        } else if (chunkMiner.enabled) {''', 'chunk branch marker')

# --- reset/cleanup state ---
rep('''        nukerTarget = null;\n        nukerRearmTicks = 0;\n        nukerAimTicks = 0;\n        NUKER_SKIPPED.clear();''', '''        nukerTarget = null;\n        nukerRearmTicks = 0;\n        nukerAimTicks = 0;\n        NUKER_SKIPPED.clear();\n        areaMineTarget = null;\n        areaMineLayerTop = Integer.MIN_VALUE;\n        areaMineLane = 0;\n        areaMineReverse = false;\n        areaMineRearmTicks = 0;\n        areaMineAimTicks = 0;\n        AREA_MINE_SKIPPED.clear();''', 'correction cleanup', 1)

# second occurrence in runtime cleanup
rep('''        nukerTarget = null;\n        nukerRearmTicks = 0;\n        nukerAimTicks = 0;\n        NUKER_SKIPPED.clear();''', '''        nukerTarget = null;\n        nukerRearmTicks = 0;\n        nukerAimTicks = 0;\n        NUKER_SKIPPED.clear();\n        areaMineTarget = null;\n        areaMineLayerTop = Integer.MIN_VALUE;\n        areaMineLane = 0;\n        areaMineReverse = false;\n        areaMineRearmTicks = 0;\n        areaMineAimTicks = 0;\n        AREA_MINE_SKIPPED.clear();''', 'runtime cleanup', 1)

# --- helper insertion before existing chunk miner helper ---
helper_anchor = '''    private static boolean validChunkMineTarget(Minecraft mc, Mod chunk, BlockPos pos) {'''
helpers = r'''    private static String posText(BlockPos p) {
        return p == null ? "unset" : p.getX() + "," + p.getY() + "," + p.getZ();
    }

    private static String areaMinerStatus() {
        if (areaCornerA == null || areaCornerB == null) return "Area Miner: set /eio area pos1 and /eio area pos2";
        Mod area = find("Area Miner");
        int depth = area == null ? 0 : Math.max(5, (int) Math.round(area.num("Depth").value));
        return "Area Miner: pos1=" + posText(areaCornerA) + " pos2=" + posText(areaCornerB)
                + " surfaceY=" + areaSurfaceY() + " depth=" + depth + " layerTop="
                + (areaMineLayerTop == Integer.MIN_VALUE ? "not-started" : areaMineLayerTop)
                + " lane=" + areaMineLane + " target=" + posText(areaMineTarget);
    }

    private static void resetAreaMinerProgress() {
        areaMineTarget = null;
        areaMineLayerTop = Integer.MIN_VALUE;
        areaMineLane = 0;
        areaMineReverse = false;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        AREA_MINE_SKIPPED.clear();
    }

    private static boolean areaMinerReady() {
        return areaCornerA != null && areaCornerB != null;
    }

    private static int areaMinX() { return Math.min(areaCornerA.getX(), areaCornerB.getX()); }
    private static int areaMaxX() { return Math.max(areaCornerA.getX(), areaCornerB.getX()); }
    private static int areaMinZ() { return Math.min(areaCornerA.getZ(), areaCornerB.getZ()); }
    private static int areaMaxZ() { return Math.max(areaCornerA.getZ(), areaCornerB.getZ()); }
    private static int areaSurfaceY() { return Math.max(areaCornerA.getY(), areaCornerB.getY()); }

    private static boolean insideAreaXZ(BlockPos pos) {
        return areaMinerReady() && pos.getX() >= areaMinX() && pos.getX() <= areaMaxX()
                && pos.getZ() >= areaMinZ() && pos.getZ() <= areaMaxZ();
    }

    private static int currentAreaLayerBottom(Mod area) {
        int totalDepth = Math.max(5, (int) Math.round(area.num("Depth").value));
        int absoluteBottom = areaSurfaceY() - totalDepth + 1;
        return Math.max(absoluteBottom, areaMineLayerTop - 4);
    }

    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null || !areaMinerReady()) return false;
        if (!insideAreaXZ(pos)) return false;
        if (areaMineLayerTop == Integer.MIN_VALUE) return false;
        int bottom = currentAreaLayerBottom(area);
        if (pos.getY() > areaMineLayerTop || pos.getY() < bottom) return false;
        // Never mine above the configured surface. This is the critical boundary guarantee.
        if (pos.getY() > areaSurfaceY()) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        return !state.isAir() && state.getDestroySpeed(mc.level, pos) >= 0.0f;
    }

    private static int areaLaneCount(Mod area) {
        int width = Math.max(1, (int) Math.round(area.num("Tunnel Width").value));
        int zSize = areaMaxZ() - areaMinZ() + 1;
        return Math.max(1, (zSize + width - 1) / width);
    }

    private static boolean areaMinerHasCurrentLane(Minecraft mc, Mod area) {
        return areaMinerReady() && areaMineLayerTop != Integer.MIN_VALUE && areaMineLane < areaLaneCount(area);
    }

    private static boolean currentAreaLayerHasBlocks(Minecraft mc, Mod area) {
        int bottom = currentAreaLayerBottom(area);
        for (int x = areaMinX(); x <= areaMaxX(); x++) {
            for (int z = areaMinZ(); z <= areaMaxZ(); z++) {
                for (int y = areaMineLayerTop; y >= bottom; y--) {
                    BlockPos p = new BlockPos(x, y, z);
                    if (validAreaMineTarget(mc, area, p)) return true;
                }
            }
        }
        return false;
    }

    private static void advanceAreaLayerOrLane(Minecraft mc, Mod area) {
        if (currentAreaLayerHasBlocks(mc, area)) return;
        int laneCount = areaLaneCount(area);
        if (areaMineLane + 1 < laneCount) {
            areaMineLane++;
            areaMineReverse = !areaMineReverse;
            AREA_MINE_SKIPPED.clear();
            return;
        }
        int totalDepth = Math.max(5, (int) Math.round(area.num("Depth").value));
        int absoluteBottom = areaSurfaceY() - totalDepth + 1;
        int nextTop = areaMineLayerTop - 5;
        if (nextTop < absoluteBottom) {
            areaMineTarget = null;
            areaMineLayerTop = absoluteBottom - 1; // completion sentinel below requested region
            return;
        }
        areaMineLayerTop = nextTop;
        areaMineLane = 0;
        areaMineReverse = false;
        AREA_MINE_SKIPPED.clear();
    }

    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (!areaMinerReady() || mc.player == null || mc.level == null) return null;
        if (areaMineLayerTop == Integer.MIN_VALUE) {
            // First action is exactly the top 5-block slice beneath the selected surface.
            areaMineLayerTop = areaSurfaceY();
            areaMineLane = 0;
            areaMineReverse = false;
        }
        int totalDepth = Math.max(5, (int) Math.round(area.num("Depth").value));
        int absoluteBottom = areaSurfaceY() - totalDepth + 1;
        if (areaMineLayerTop < absoluteBottom) return null;

        int width = Math.max(1, (int) Math.round(area.num("Tunnel Width").value));
        int laneZ0 = areaMinZ() + areaMineLane * width;
        int laneZ1 = Math.min(areaMaxZ(), laneZ0 + width - 1);
        int bottom = currentAreaLayerBottom(area);

        BlockPos best = null;
        double bestScore = Double.MAX_VALUE;
        int xStart = areaMineReverse ? areaMaxX() : areaMinX();
        int xEnd = areaMineReverse ? areaMinX() : areaMaxX();
        int xStep = areaMineReverse ? -1 : 1;
        for (int x = xStart; areaMineReverse ? x >= xEnd : x <= xEnd; x += xStep) {
            for (int z = laneZ0; z <= laneZ1; z++) {
                for (int y = areaMineLayerTop; y >= bottom; y--) {
                    BlockPos p = new BlockPos(x, y, z);
                    if (AREA_MINE_SKIPPED.contains(p) || !validAreaMineTarget(mc, area, p)) continue;
                    double d = mc.player.distanceToSqr(p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5);
                    // Strongly favor the next forward X position in the current serpentine lane, then nearest reachable block.
                    double order = areaMineReverse ? (areaMaxX() - x) : (x - areaMinX());
                    double score = order * 1000.0 + d;
                    if (score < bestScore) { bestScore = score; best = p; }
                }
            }
        }
        return best;
    }

    private static boolean runAreaMiner(Minecraft mc, Mod area, boolean miningAllowed) {
        if (!miningAllowed || !areaMinerReady() || mc.player == null || mc.level == null) {
            areaMineTarget = null;
            areaMineAimTicks = 0;
            return false;
        }
        if (areaMineRearmTicks > 0) { areaMineRearmTicks--; return false; }

        if (areaMineTarget != null && (!validAreaMineTarget(mc, area, areaMineTarget) || mc.level.getBlockState(areaMineTarget).isAir())) {
            areaMineTarget = null;
            areaMineAimTicks = 0;
            areaMineRearmTicks = Math.max(1, (int) Math.round(area.num("Retarget Delay").value));
            advanceAreaLayerOrLane(mc, area);
            return false;
        }

        if (areaMineTarget == null) {
            advanceAreaLayerOrLane(mc, area);
            areaMineTarget = findAreaMineTarget(mc, area);
            areaMineAimTicks = 0;
            if (areaMineTarget == null) return false;
        }

        if (area.bool("Face Block").value) faceBlock(mc, areaMineTarget);
        areaMineAimTicks++;
        if (mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(areaMineTarget)) return true;
        if (areaMineAimTicks >= Math.max(4, (int) Math.round(area.num("Aim Timeout").value))) {
            AREA_MINE_SKIPPED.add(areaMineTarget);
            areaMineTarget = null;
            areaMineAimTicks = 0;
            areaMineRearmTicks = 1;
        }
        return false;
    }

''' + helper_anchor
rep(helper_anchor, helpers, 'area helper insertion')

# --- HUD mining target should include Area Miner ---
rep('''            BlockPos target = nukerTarget != null ? nukerTarget : chunkMineTarget;''', '''            BlockPos target = areaMineTarget != null ? areaMineTarget : (nukerTarget != null ? nukerTarget : chunkMineTarget);''', 'mining HUD target')

# --- category scrolling / modern rail ---
# Add category scroll state in ClickGui.
rep('''        private double moduleScroll;\n        private double settingsScroll;''', '''        private double categoryScroll;\n        private double moduleScroll;\n        private double settingsScroll;''', 'category scroll field')

# Replace category list geometry in render with clipped, scrolled rail. These anchors are stable in 0.24.
rep('''            int cy = y + 58;\n            for (String cat : categories()) {''', '''            int catTop = y + 58;\n            int catBottom = y + h - 34;\n            int cy = catTop - (int) Math.round(categoryScroll);\n            int categoryContent = categories().size() * 28;\n            int categoryViewport = Math.max(1, catBottom - catTop);\n            double categoryMax = Math.max(0, categoryContent - categoryViewport);\n            categoryScroll = Math.max(0, Math.min(categoryMax, categoryScroll));\n            g.enableScissor(x + 8, catTop, x + 126, catBottom);\n            for (String cat : categories()) {''', 'category render scroll start')
rep('''                cy += 28;\n            }\n\n            int modulesX = x + 138;''', '''                cy += 28;\n            }\n            g.disableScissor();\n            if (categoryMax > 0) drawScrollBar(g, x + 122, catTop, catBottom - catTop, categoryScroll, categoryMax, categoryViewport, categoryContent);\n\n            int modulesX = x + 138;''', 'category render scroll end')

# Category click hit testing must account for scroll and viewport.
rep('''            int cy = y + 58;\n            for (String cat : categories()) {\n                if (inside(mouseX, mouseY, x + 10, cy, 116, 22)) {''', '''            int catTop = y + 58;\n            int catBottom = y + h - 34;\n            int cy = catTop - (int) Math.round(categoryScroll);\n            for (String cat : categories()) {\n                if (mouseY >= catTop && mouseY < catBottom && inside(mouseX, mouseY, x + 10, cy, 112, 22)) {''', 'category click scrolling')

# Reset category scroll when GUI opens only via init if present; otherwise preserve.
# Extend mouse wheel routing to left category rail.
rep('''            if (mouseX >= modulesX && mouseX < settingsX) {''', '''            if (mouseX >= x + 8 && mouseX < x + 128) {\n                int viewport = Math.max(1, h - 92);\n                int content = categories().size() * 28;\n                double max = Math.max(0, content - viewport);\n                categoryScroll = clampScroll(categoryScroll - verticalAmount * 22.0, max);\n                return true;\n            }\n            if (mouseX >= modulesX && mouseX < settingsX) {''', 'mouse wheel categories')

# Modernize rail and panels with slightly more transparent glass / accent header while retaining readability.
rep('''            g.fill(x, y, x + w, y + h, 0xB910141C);''', '''            g.fill(x, y, x + w, y + h, 0x9B0B1018);\n            g.fill(x + 1, y + 1, x + w - 1, y + 38, 0xB5182230);''', 'modern glass shell')

p.write_text(s)

# Version bump.
gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.24.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g.replace('mod_version=0.24.0+26.3', 'mod_version=0.25.0+26.3', 1))

print('0.25 Area Miner + category-scroll patch applied')
