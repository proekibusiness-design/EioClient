from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()

if 'BUILD_ID = "EIO-026-AREA2"' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String BUILD_ID = "EIO-026-AREA1";',
        'public static final String BUILD_ID = "EIO-026-AREA2";', 'build id')

    rep('mod("Area Miner", "Mining", "Mines a user-defined rectangular area to a chosen depth and can move through the selected coordinates.", -1)',
        'mod("Area Miner", "Mining", "Serpentine tunnel miner: clears the next lane cell straight ahead, moves into it, turns at the boundary, shifts one cell and works back across the selected zone.", -1)',
        'area description')

    rep('.num("Depth", 8.0, 1.0, 64.0, 1.0, "Number of blocks to mine downward from the higher corner Y level.")',
        '.num("Depth", 8.0, 1.0, 64.0, 1.0, "Vertical depth included in the selected zone. Area Miner only targets the current serpentine lane column instead of mining surrounding blocks.")',
        'depth description')

    rep('.bool("Auto Move", true, "Move through the configured rectangle when no mineable block is currently in normal interaction range.")',
        '.bool("Auto Move", true, "Walk the serpentine lane path after the block column directly ahead is clear.")',
        'auto move description')

    old_find = '''    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize()) return null;
        BlockPos origin = mc.player.blockPosition();
        int radius = 6;
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;
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
    new_find = '''    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize()) return null;
        int cells = region.navigationCells();
        if (cells <= 0 || areaNavIndex < 0 || areaNavIndex >= cells) return null;

        // AREA2: only clear the column for the current serpentine lane cell. This deliberately
        // avoids the old radius scan that could turn around and mine unrelated blocks behind/aside.
        BlockPos lane = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
        if (lane == null) return null;
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int y = region.topY; y >= region.bottomY; y--) {
            BlockPos pos = new BlockPos(lane.getX(), y, lane.getZ());
            if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;
            double px = pos.getX() + 0.5 - mc.player.getX();
            double py = pos.getY() + 0.5 - mc.player.getEyeY();
            double pz = pos.getZ() + 0.5 - mc.player.getZ();
            double d = px * px + py * py + pz * pz;
            if (d < bestSq) { bestSq = d; best = pos.immutable(); }
        }
        return best;
    }
'''
    rep(old_find, new_find, 'lane-only area target')

    old_nav = '''    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        if (areaMineTarget != null || areaMineRearmTicks > 0) { areaMoveTicks = 0; return false; }
        BlockPos reachable = findAreaMineTarget(mc, area);
        if (reachable != null) {
            areaMineTarget = reachable;
            areaMineAimTicks = 0;
            areaMoveTicks = 0;
            return false;
        }
        AreaRegion region = areaRegion(area);
        if (region == null) return false;

        double px = mc.player.getX(), pz = mc.player.getZ();
        boolean outside = px < region.minX + 0.15 || px > region.maxX + 0.85
                || pz < region.minZ + 0.15 || pz > region.maxZ + 0.85;
        double goalX, goalZ;
        if (outside) {
            goalX = region.clampX(px) + 0.5;
            goalZ = region.clampZ(pz) + 0.5;
        } else {
            int cells = region.navigationCells();
            if (cells <= 0) return false;
            if (areaNavIndex >= cells) {
                if (areaMinedThisPass <= 0) {
                    areaComplete = true;
                    area.enabled = false;
                    save();
                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
                    return false;
                }
                areaNavIndex = 0;
                areaMinedThisPass = 0;
                AREA_MINE_SKIPPED.clear();
            }
            BlockPos nav = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
            if (nav == null) return false;
            goalX = nav.getX() + 0.5;
            goalZ = nav.getZ() + 0.5;
        }

        double dx = goalX - px, dz = goalZ - pz;
        double distance = Math.sqrt(dx * dx + dz * dz);
        if (!outside && distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        if (++areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
            if (!outside) areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.45;
    }
'''
    new_nav = '''    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        if (areaMineTarget != null || areaMineRearmTicks > 0) { areaMoveTicks = 0; return false; }
        AreaRegion region = areaRegion(area);
        if (region == null) return false;

        double px = mc.player.getX(), pz = mc.player.getZ();
        boolean outside = px < region.minX + 0.15 || px > region.maxX + 0.85
                || pz < region.minZ + 0.15 || pz > region.maxZ + 0.85;
        double goalX, goalZ;
        if (outside) {
            // Enter at the nearest point in the configured zone before taking ownership of the lane path.
            goalX = region.clampX(px) + 0.5;
            goalZ = region.clampZ(pz) + 0.5;
        } else {
            int cells = region.navigationCells();
            if (cells <= 0) return false;
            if (areaNavIndex >= cells) {
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
            }

            BlockPos nav = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
            if (nav == null) return false;

            // Mine the current lane column before walking into it. At row boundaries navigationCell()
            // supplies the adjacent shift cell followed by the reverse lane, producing the U-turn pattern.
            BlockPos forwardBlock = findAreaMineTarget(mc, area);
            if (forwardBlock != null) {
                areaMineTarget = forwardBlock;
                areaMineAimTicks = 0;
                areaMoveTicks = 0;
                return false;
            }

            goalX = nav.getX() + 0.5;
            goalZ = nav.getZ() + 0.5;
        }

        double dx = goalX - px, dz = goalZ - pz;
        double distance = Math.sqrt(dx * dx + dz * dz);
        if (!outside && distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        if (++areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
            if (!outside) areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.45;
    }
'''
    rep(old_nav, new_nav, 'serpentine navigation')

    # Remove an accidental duplicate PointSetting reset branch and make module reset include points.
    s = s.replace('''                else if (setting instanceof MobListSetting ml) ml.reset();
            else if (setting instanceof PointSetting point) point.reset();
                else if (setting instanceof PointSetting point) point.reset();''',
                  '''                else if (setting instanceof MobListSetting ml) ml.reset();
                else if (setting instanceof PointSetting point) point.reset();''')

    rep('''            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
            else if (setting instanceof MobListSetting ml) ml.reset();
        }''',
        '''            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
            else if (setting instanceof MobListSetting ml) ml.reset();
            else if (setting instanceof PointSetting point) point.reset();
        }''',
        'module point reset')

    rep('return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | nav " + (areaNavIndex + 1) + "/" + region.navigationCells());',
        'return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | lane " + Math.min(region.navigationCells(), areaNavIndex + 1) + "/" + region.navigationCells());',
        'area status lane')

    p.write_text(s)

print('EIO 0.26 AREA2 serpentine patch applied')
