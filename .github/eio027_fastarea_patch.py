from pathlib import Path

src_path = Path('eio26/EioClient.java')
s = src_path.read_text()

def replace_once(old, new, label):
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'missing source anchor: {label}')
    s = s.replace(old, new, 1)

if 'VERSION = "0.26.0"' in s:
    s = s.replace('VERSION = "0.26.0"', 'VERSION = "0.27.0"', 1)
elif 'VERSION = "0.27.0"' not in s:
    raise SystemExit('unexpected Eio version')

if 'BUILD_ID = "EIO-026-AREA1"' in s:
    s = s.replace('BUILD_ID = "EIO-026-AREA1"', 'BUILD_ID = "EIO-027-FASTAREA1"', 1)
elif 'BUILD_ID = "EIO-027-FASTAREA1"' not in s:
    raise SystemExit('unexpected build id')

replace_once(
'''    private static int areaMinedThisPass;\n    private static boolean areaMoveRequested;''',
'''    private static int areaMinedThisPass;\n    private static int areaLayerIndex;\n    private static boolean areaMoveRequested;''',
'area layer state')

replace_once(
'''                .num("Depth", 8.0, 1.0, 64.0, 1.0, "Number of blocks to mine downward from the higher corner Y level.")\n                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next area target.")\n                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to line up with a target before temporarily skipping it.")\n                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one navigation cell before moving to the next cell.")''',
'''                .num("Depth", 10.0, 1.0, 64.0, 1.0, "Total depth to mine downward from the surface.")\n                .num("Layer Height", 5.0, 1.0, 10.0, 1.0, "Clear the area in top-down slices. Default is five blocks per layer.")\n                .num("Retarget Delay", 1.0, 1.0, 3.0, 1.0, "Ticks used for the required attack-key release between blocks.")\n                .num("Aim Timeout", 3.0, 2.0, 12.0, 1.0, "Fast fallback timeout when a selected block cannot actually be acquired by the crosshair.")\n                .num("Move Timeout", 70.0, 20.0, 180.0, 5.0, "Ticks allowed to reach one navigation cell before moving to the next cell.")''',
'area fast settings')

replace_once(
'''    private static String areaStatus(Mod area) {\n        AreaRegion region = areaRegion(area);\n        if (region == null) return "Area Miner: set Corner A and Corner B";\n        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;\n        return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | nav " + (areaNavIndex + 1) + "/" + region.navigationCells());\n    }\n\n    private static void resetAreaRuntime() {''',
'''    private static int areaLayerHeight(Mod area) {\n        return Math.max(1, (int) Math.round(area.num("Layer Height").value));\n    }\n\n    private static int areaLayerCount(AreaRegion region, Mod area) {\n        int height = areaLayerHeight(area);\n        return Math.max(1, (region.depth() + height - 1) / height);\n    }\n\n    private static int areaLayerTop(AreaRegion region, Mod area) {\n        return Math.max(region.bottomY, region.topY - areaLayerIndex * areaLayerHeight(area));\n    }\n\n    private static int areaLayerBottom(AreaRegion region, Mod area) {\n        return Math.max(region.bottomY, areaLayerTop(region, area) - areaLayerHeight(area) + 1);\n    }\n\n    private static boolean inActiveAreaLayer(AreaRegion region, Mod area, BlockPos pos) {\n        return pos.getY() <= areaLayerTop(region, area) && pos.getY() >= areaLayerBottom(region, area);\n    }\n\n    private static String areaStatus(Mod area) {\n        AreaRegion region = areaRegion(area);\n        if (region == null) return "Area Miner: set Corner A and Corner B";\n        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;\n        int layers = areaLayerCount(region, area);\n        String layer = " | layer " + Math.min(areaLayerIndex + 1, layers) + "/" + layers\n                + " Y " + areaLayerTop(region, area) + ".." + areaLayerBottom(region, area);\n        return "Area Miner: " + region.summary() + layer\n                + (areaComplete ? " | complete" : " | nav " + (areaNavIndex + 1) + "/" + region.navigationCells());\n    }\n\n    private static void resetAreaRuntime() {''',
'area layer helpers')

replace_once(
'''        areaMinedThisPass = 0;\n        areaMoveRequested = false;''',
'''        areaMinedThisPass = 0;\n        areaLayerIndex = 0;\n        areaMoveRequested = false;''',
'area layer reset')

replace_once(
'''        if (region == null || !region.supportedSize() || !region.contains(pos)) return false;\n        if (!withinVanillaBlockRange(mc, pos)) return false;''',
'''        if (region == null || !region.supportedSize() || !region.contains(pos)) return false;\n        if (!inActiveAreaLayer(region, area, pos)) return false;\n        if (!withinVanillaBlockRange(mc, pos)) return false;''',
'active layer target guard')

old_find = '''    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {\n        if (mc.player == null || mc.level == null) return null;\n        AreaRegion region = areaRegion(area);\n        if (region == null || !region.supportedSize()) return null;\n        BlockPos origin = mc.player.blockPosition();\n        int radius = 6;\n        BlockPos best = null;\n        double bestSq = Double.MAX_VALUE;\n        for (int dy = -radius; dy <= radius; dy++) {\n            for (int dx = -radius; dx <= radius; dx++) {\n                for (int dz = -radius; dz <= radius; dz++) {\n                    BlockPos pos = origin.offset(dx, dy, dz);\n                    if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;\n                    double px = pos.getX() + 0.5 - mc.player.getX();\n                    double py = pos.getY() + 0.5 - mc.player.getY();\n                    double pz = pos.getZ() + 0.5 - mc.player.getZ();\n                    double d = px * px + py * py + pz * pz;\n                    if (d < bestSq) { bestSq = d; best = pos.immutable(); }\n                }\n            }\n        }\n        return best;\n    }'''
new_find = '''    private static double wrappedDegrees(double degrees) {\n        double wrapped = degrees % 360.0;\n        if (wrapped > 180.0) wrapped -= 360.0;\n        if (wrapped < -180.0) wrapped += 360.0;\n        return wrapped;\n    }\n\n    private static double blockAimError(Player player, BlockPos pos) {\n        double dx = pos.getX() + 0.5 - player.getX();\n        double dz = pos.getZ() + 0.5 - player.getZ();\n        double dy = pos.getY() + 0.5 - player.getEyeY();\n        double horizontal = Math.sqrt(dx * dx + dz * dz);\n        double targetYaw = Math.toDegrees(Math.atan2(dz, dx)) - 90.0;\n        double targetPitch = -Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)));\n        double yawError = Math.abs(wrappedDegrees(targetYaw - player.getYRot()));\n        double pitchError = Math.abs(targetPitch - player.getXRot());\n        return yawError + pitchError * 0.65;\n    }\n\n    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {\n        if (mc.player == null || mc.level == null) return null;\n        AreaRegion region = areaRegion(area);\n        if (region == null || !region.supportedSize()) return null;\n\n        // Never rotate away from a block we can already mine under the crosshair.\n        if (mc.hitResult instanceof BlockHitResult hit) {\n            BlockPos looked = hit.getBlockPos();\n            if (!AREA_MINE_SKIPPED.contains(looked) && validAreaMineTarget(mc, area, looked)) {\n                return looked.immutable();\n            }\n        }\n\n        BlockPos origin = mc.player.blockPosition();\n        int radius = 6;\n        BlockPos best = null;\n        double bestScore = Double.MAX_VALUE;\n        for (int dy = -radius; dy <= radius; dy++) {\n            for (int dx = -radius; dx <= radius; dx++) {\n                for (int dz = -radius; dz <= radius; dz++) {\n                    BlockPos pos = origin.offset(dx, dy, dz);\n                    if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;\n                    double px = pos.getX() + 0.5 - mc.player.getX();\n                    double py = pos.getY() + 0.5 - mc.player.getY();\n                    double pz = pos.getZ() + 0.5 - mc.player.getZ();\n                    double distanceSq = px * px + py * py + pz * pz;\n                    double aim = blockAimError(mc.player, pos);\n                    // Strongly prefer small camera movements, then choose the nearer block.\n                    double score = distanceSq + aim * aim * 0.035;\n                    if (score < bestScore) { bestScore = score; best = pos.immutable(); }\n                }\n            }\n        }\n        return best;\n    }'''
replace_once(old_find, new_find, 'fast area target selection')

replace_once(
'''            if (areaNavIndex >= cells) {\n                if (areaMinedThisPass <= 0) {\n                    areaComplete = true;\n                    area.enabled = false;\n                    save();\n                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);\n                    return false;\n                }\n                areaNavIndex = 0;\n                areaMinedThisPass = 0;\n                AREA_MINE_SKIPPED.clear();\n            }''',
'''            if (areaNavIndex >= cells) {\n                if (areaMinedThisPass <= 0) {\n                    int layers = areaLayerCount(region, area);\n                    if (areaLayerIndex + 1 < layers) {\n                        areaLayerIndex++;\n                        areaNavIndex = 0;\n                        areaMoveTicks = 0;\n                        areaMinedThisPass = 0;\n                        AREA_MINE_SKIPPED.clear();\n                        notifyMessage("AREA MINER: LAYER " + (areaLayerIndex + 1) + "/" + layers, 0xFF73C8FF, 1800L);\n                        return false;\n                    }\n                    areaComplete = true;\n                    area.enabled = false;\n                    save();\n                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);\n                    return false;\n                }\n                areaNavIndex = 0;\n                areaMinedThisPass = 0;\n                AREA_MINE_SKIPPED.clear();\n            }''',
'area layer progression')

replace_once(
'''                            } else if (++areaMineAimTicks >= Math.max(4, (int) Math.round(areaMiner.num("Aim Timeout").value))) {''',
'''                            } else if (++areaMineAimTicks >= Math.max(2, (int) Math.round(areaMiner.num("Aim Timeout").value))) {''',
'fast aim timeout')

src_path.write_text(s)

gp_path = Path('gradle.properties')
gp = gp_path.read_text()
if 'mod_version=0.26.0+26.3' in gp:
    gp = gp.replace('mod_version=0.26.0+26.3', 'mod_version=0.27.0+26.3', 1)
elif 'mod_version=0.27.0+26.3' not in gp:
    raise SystemExit('unexpected gradle mod version')
gp_path.write_text(gp)

print('Eio 0.27 fast/smooth Area Miner transform ready')
