from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

if 'public static final String VERSION = "0.27.1";' not in s:
    rep('public static final String VERSION = "0.27.0";',
        'public static final String VERSION = "0.27.1";', 'version')
    rep('public static final String BUILD_ID = "EIO-027-FASTAREA1";',
        'public static final String BUILD_ID = "EIO-0271-LOS1";', 'build id')

    rep('.num("Layer Height", 5.0, 1.0, 10.0, 1.0, "Clear the area in top-down slices. Default is five blocks per layer.")',
        '.num("Layer Height", 4.0, 1.0, 10.0, 1.0, "Clear the area in top-down slices. Default is four blocks per layer.")',
        'four block layer')

    rep('''        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }

    private static double wrappedDegrees(double degrees) {''', '''        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        if (area.bool("Exposed Only").value && !isExposedBlock(mc, pos)) return false;
        return areaVisibleAimPoint(mc, pos) != null;
    }

    private static double[] areaVisibleAimPoint(Minecraft mc, BlockPos pos) {
        if (mc == null || mc.player == null || mc.level == null || pos == null) return null;
        double sx = mc.player.getX();
        double sy = mc.player.getEyeY();
        double sz = mc.player.getZ();
        double[][] candidates = {
                {pos.getX() + 0.50, pos.getY() + 0.50, pos.getZ() + 0.01, pos.getX(),     pos.getY(), pos.getZ() - 1},
                {pos.getX() + 0.50, pos.getY() + 0.50, pos.getZ() + 0.99, pos.getX(),     pos.getY(), pos.getZ() + 1},
                {pos.getX() + 0.01, pos.getY() + 0.50, pos.getZ() + 0.50, pos.getX() - 1, pos.getY(), pos.getZ()},
                {pos.getX() + 0.99, pos.getY() + 0.50, pos.getZ() + 0.50, pos.getX() + 1, pos.getY(), pos.getZ()},
                {pos.getX() + 0.50, pos.getY() + 0.01, pos.getZ() + 0.50, pos.getX(),     pos.getY() - 1, pos.getZ()},
                {pos.getX() + 0.50, pos.getY() + 0.99, pos.getZ() + 0.50, pos.getX(),     pos.getY() + 1, pos.getZ()}
        };
        double[] best = null;
        double bestScore = Double.MAX_VALUE;
        for (double[] c : candidates) {
            BlockPos outside = new BlockPos((int) c[3], (int) c[4], (int) c[5]);
            if (!mc.level.getBlockState(outside).isAir()) continue;
            if (!clearAreaRay(mc, sx, sy, sz, c[0], c[1], c[2], pos)) continue;
            double dx = c[0] - sx, dy = c[1] - sy, dz = c[2] - sz;
            double distanceSq = dx * dx + dy * dy + dz * dz;
            double horizontal = Math.sqrt(dx * dx + dz * dz);
            double yaw = Math.toDegrees(Math.atan2(dz, dx)) - 90.0;
            double pitch = -Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)));
            double yawError = Math.abs(wrappedDegrees(yaw - mc.player.getYRot()));
            double pitchError = Math.abs(pitch - mc.player.getXRot());
            double score = distanceSq + yawError * yawError * 0.02 + pitchError * pitchError * 0.012;
            if (score < bestScore) {
                bestScore = score;
                best = new double[]{c[0], c[1], c[2]};
            }
        }
        return best;
    }

    private static boolean clearAreaRay(Minecraft mc, double sx, double sy, double sz,
                                        double tx, double ty, double tz, BlockPos target) {
        double dx = tx - sx, dy = ty - sy, dz = tz - sz;
        double distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
        int steps = Math.max(2, (int) Math.ceil(distance / 0.12));
        BlockPos previous = null;
        for (int i = 1; i < steps; i++) {
            double t = i / (double) steps;
            double x = sx + dx * t, y = sy + dy * t, z = sz + dz * t;
            BlockPos sample = new BlockPos((int) Math.floor(x), (int) Math.floor(y), (int) Math.floor(z));
            if (sample.equals(target)) return true;
            if (sample.equals(previous)) continue;
            previous = sample;
            if (!mc.level.getBlockState(sample).isAir()) return false;
        }
        return true;
    }

    private static void faceAreaBlock(Minecraft mc, BlockPos pos) {
        if (mc == null || mc.player == null || pos == null) return;
        double[] aim = areaVisibleAimPoint(mc, pos);
        if (aim == null) return;
        double dx = aim[0] - mc.player.getX();
        double dz = aim[2] - mc.player.getZ();
        double dy = aim[1] - mc.player.getEyeY();
        double horizontal = Math.sqrt(dx * dx + dz * dz);
        mc.player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
        mc.player.setXRot((float) (-Math.toDegrees(Math.atan2(dy, Math.max(0.001, horizontal)))));
    }

    private static double wrappedDegrees(double degrees) {''', 'area line of sight helpers')

    rep('if (areaMiner.bool("Face Block").value) faceBlock(mc.player, areaMineTarget);',
        'if (areaMiner.bool("Face Block").value) faceAreaBlock(mc, areaMineTarget);',
        'area visible-face aiming')

src.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.27.0+26.3' in g:
    g = g.replace('mod_version=0.27.0+26.3', 'mod_version=0.27.1+26.3', 1)
elif 'mod_version=0.27.1+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)
