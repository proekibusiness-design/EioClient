from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

if 'public static final String VERSION = "0.28.0";' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String VERSION = "0.27.0";',
        'public static final String VERSION = "0.28.0";', 'version')
    rep('public static final String BUILD_ID = "EIO-027-AREA1";',
        'public static final String BUILD_ID = "EIO-028-GROUND1";', 'build id')

    rep('''                .point("Corner A", "Starting corner. Stand at the surface start of the first lane and left-click this row. Right-click clears it.")
                .point("Corner B", "Opposite horizontal corner of the area. Left-click this row while standing there. Right-click clears it.")''',
        '''                .point("Corner A", "Starting corner. Stand ON the surface block; Area Miner begins with the block directly under your feet. Right-click clears it.")
                .point("Corner B", "Opposite corner. Stand ON its surface block; the block directly under your feet defines that edge. Right-click clears it.")''',
        'corner help')

    old_aim = '''                            boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(areaMineTarget);
                            if (aimed) {
                                shouldForceAttack = true;
                                areaMineAimTicks = 0;
                                areaAimFailures = 0;
                            } else if (++areaMineAimTicks >= Math.max(4, (int) Math.round(areaMiner.num("Aim Timeout").value))) {'''
    new_aim = '''                            if (mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(areaMineTarget)) {
                                // Drive the same mapped game-mode destroy progression vanilla uses once the
                                // crosshair is actually on the selected block. This avoids relying on a late
                                // synthetic attack-key press to begin the first surface block.
                                if (mc.gameMode != null) mc.gameMode.continueDestroyBlock(areaMineTarget, hit.getDirection());
                                areaMineAimTicks = 0;
                                areaAimFailures = 0;
                            } else if (++areaMineAimTicks >= Math.max(4, (int) Math.round(areaMiner.num("Aim Timeout").value))) {'''
    rep(old_aim, new_aim, 'area mining progression')

    src.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.27.0+26.3' in g:
    g = g.replace('mod_version=0.27.0+26.3', 'mod_version=0.28.0+26.3', 1)
elif 'mod_version=0.28.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)
