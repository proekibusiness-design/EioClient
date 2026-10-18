from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

if 'public static final String VERSION = "0.29.0";' not in s:
    if 'public static final String VERSION = "0.28.0";' not in s:
        raise SystemExit('unexpected source version')
    s = s.replace('public static final String VERSION = "0.28.0";', 'public static final String VERSION = "0.29.0";', 1)
    s = s.replace('public static final String BUILD_ID = "EIO-028-PLANE1";', 'public static final String BUILD_ID = "EIO-029-LANE1";', 1)

    old_mod = '''        mod("Area Miner", "Mining", "Clears one full horizontal plane at a time in serpentine lanes; five planes form a stage before the next 5-block stage begins.", -1)
                .point("Corner A", "Stand at the first horizontal corner and left-click this row to set it here. Right-click clears it.")
                .point("Corner B", "Stand at the opposite horizontal corner and left-click this row to set it here. Right-click clears it.")
                .num("Depth", 10.0, 1.0, 64.0, 1.0, "Total depth below the surface. Area Miner processes this in fixed 5-block stages.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next area target.")
                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to line up with a target before temporarily skipping it.")
                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one serpentine navigation cell before moving to the next cell.")
                .bool("Auto Move", true, "Move through each lane of the configured rectangle after clearing the blocks immediately ahead.")
                .bool("Sprint", false, "Sprint while Area Miner is navigating through a cleared lane.")
                .bool("Auto Jump", true, "Jump over simple one-block obstacles while Area Miner is moving.")
                .bool("Exposed Only", true, "Mine only exposed blocks; each horizontal plane is revisited until it is completely clear.")
                .bool("Face Block", true, "Turn your view toward the current straight-ahead Area Miner target.");'''
    new_mod = '''        mod("Area Miner", "Mining", "Walks deterministic serpentine lanes and continuously mines the valid lane block currently under the crosshair.", -1)
                .point("Corner A", "Stand at the first horizontal corner and left-click this row to set it here. Right-click clears it.")
                .point("Corner B", "Stand at the opposite horizontal corner and left-click this row to set it here. Right-click clears it.")
                .num("Depth", 10.0, 1.0, 64.0, 1.0, "Total depth below the surface. Area Miner processes this in fixed 5-block stages.")
                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one serpentine navigation cell before pausing instead of wandering.")
                .bool("Auto Move", true, "Hold forward while mining the current lane so the player walks into each cleared block seamlessly.")
                .bool("Sprint", false, "Sprint while Area Miner is navigating through a cleared lane.")
                .bool("Auto Jump", true, "Jump over simple one-block obstacles while Area Miner is moving.")
                .bool("Exposed Only", true, "Mine only exposed blocks on the active horizontal plane.")
                .bool("Face Block", true, "Keep the view centered on the current deterministic lane block.");'''
    if old_mod not in s:
        raise SystemExit('Area Miner module block not found')
    s = s.replace(old_mod, new_mod, 1)

    start = s.index('    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {')
    end = s.index('    private static boolean areaPlaneHasBlocks', start)
    replacement = '''    private static BlockPos currentAreaLaneCell(Mod area) {
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || areaStageIndex >= region.stageCount()) return null;
        if (areaNavIndex < 0 || areaNavIndex >= region.navigationCells()) return null;
        return region.navigationCell(areaNavIndex, region.stageLayerY(areaStageIndex, areaLayerIndex));
    }

    private static BlockPos currentAreaLookTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !(mc.hitResult instanceof BlockHitResult hit)) return null;
        BlockPos looked = hit.getBlockPos();
        if (!validAreaMineTarget(mc, area, looked)) return null;
        AreaRegion region = areaRegion(area);
        if (region == null) return null;
        int cells = region.navigationCells();
        int from = Math.max(0, Math.min(areaNavIndex, Math.max(0, cells - 1)));
        int to = Math.min(cells, from + 3);
        int y = region.stageLayerY(areaStageIndex, areaLayerIndex);
        for (int i = from; i < to; i++) {
            BlockPos lane = region.navigationCell(i, y);
            if (lane != null && lane.equals(looked)) return looked.immutable();
        }
        return null;
    }

'''
    s = s[:start] + replacement + s[end:]

    start = s.index('    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {')
    end = s.index('    private static void faceHorizontal', start)
    replacement = '''    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || areaStageIndex >= region.stageCount()) return false;

        if (areaNavIndex >= region.navigationCells()) {
            if (advanceAreaPlaneIfReady(mc, area, region)) return false;
        }
        BlockPos nav = currentAreaLaneCell(area);
        if (nav == null) return false;

        double px = mc.player.getX(), pz = mc.player.getZ();
        double goalX = nav.getX() + 0.5, goalZ = nav.getZ() + 0.5;
        double dx = goalX - px, dz = goalZ - pz;
        double distance = Math.sqrt(dx * dx + dz * dz);
        var state = mc.level.getBlockState(nav);
        boolean solidLaneBlock = !state.isAir() && state.getDestroySpeed(mc.level, nav) >= 0.0f;

        if (solidLaneBlock) {
            if (area.bool("Face Block").value) faceBlock(mc.player, nav);
            areaMoveTicks++;
            if (areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
                area.enabled = false;
                save();
                notifyMessage("AREA MINER PAUSED: LANE BLOCK NOT CLEARING", 0xFFFFB36B, 3200L);
                appendDiagnostic("AREA_MINER lane_timeout index=" + areaNavIndex + " pos=" + nav.toShortString());
                areaMoveTicks = 0;
                return false;
            }
            return area.bool("Auto Move").value && distance > 0.45;
        }

        if (distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            areaMineTarget = null;
            return false;
        }

        if (++areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
            area.enabled = false;
            save();
            notifyMessage("AREA MINER PAUSED: CANNOT REACH LANE", 0xFFFFB36B, 3200L);
            appendDiagnostic("AREA_MINER move_timeout index=" + areaNavIndex);
            areaMoveTicks = 0;
            return false;
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return area.bool("Auto Move").value && distance > 0.45;
    }

'''
    s = s[:start] + replacement + s[end:]

    mining_start = s.index('            if (areaMiner.enabled) {', s.index('boolean miningAllowed'))
    mining_end = s.index('                nukerTarget = null;', mining_start)
    mining_replacement = '''            if (areaMiner.enabled) {
                if (!areaConfigured(areaMiner)) {
                    areaMineTarget = null;
                } else {
                    if (areaMineTarget != null && mc.level.getBlockState(areaMineTarget).isAir()) {
                        areaMinedThisPass++;
                        areaMineTarget = null;
                    }
                    BlockPos looked = currentAreaLookTarget(mc, areaMiner);
                    if (looked != null) {
                        areaMineTarget = looked;
                        shouldForceAttack = true;
                        areaMineAimTicks = 0;
                        areaMineRearmTicks = 0;
                    } else {
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                    }
                }
'''
    s = s[:mining_start] + mining_replacement + s[mining_end:]

    src.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.28.0+26.3' in g:
    g = g.replace('mod_version=0.28.0+26.3', 'mod_version=0.29.0+26.3', 1)
elif 'mod_version=0.29.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)

print('Applied 0.29 deterministic crosshair Area Miner patch')
