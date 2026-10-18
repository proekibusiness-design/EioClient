from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

if 'BUILD_ID = "EIO-026-AREA3"' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String BUILD_ID = "EIO-026-AREA2";',
        'public static final String BUILD_ID = "EIO-026-AREA3";', 'build id')

    rep('''                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one navigation cell before moving to the next cell.")
                .bool("Auto Move", true, "Walk the serpentine lane path after the block column directly ahead is clear.")''',
        '''                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach a normal navigation cell before skipping it if movement is blocked.")
                .num("Turn Lead", 0.95, 0.65, 1.25, 0.05, "At lane ends, begin the U-turn this many blocks before the exact end-cell center once its block column is clear.")
                .num("Turn Timeout", 8.0, 2.0, 20.0, 1.0, "Maximum ticks to wait at a lane end before handing off to the next serpentine lane.")
                .bool("Auto Move", true, "Walk the serpentine lane path after the block column directly ahead is clear.")''',
        'fast-turn settings')

    old_tail = '''        double dx = goalX - px, dz = goalZ - pz;
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
    new_tail = '''        double dx = goalX - px, dz = goalZ - pz;
        double distance = Math.sqrt(dx * dx + dz * dz);
        if (!outside) {
            boolean rowEnd = region.isRowEnd(areaNavIndex);
            double arrival = rowEnd ? area.num("Turn Lead").value : 0.78;
            int timeout = rowEnd
                    ? Math.max(2, (int) Math.round(area.num("Turn Timeout").value))
                    : Math.max(20, (int) Math.round(area.num("Move Timeout").value));
            areaMoveTicks++;
            if (distance < arrival || areaMoveTicks >= timeout) {
                areaNavIndex++;
                areaMoveTicks = 0;
                if (areaNavIndex >= region.navigationCells()) return false;

                // Fast handoff: immediately inspect and face the next serpentine cell instead of
                // returning to an idle tick or waiting for the general movement timeout.
                BlockPos next = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
                if (next == null) return false;
                BlockPos nextBlock = findAreaMineTarget(mc, area);
                if (nextBlock != null) {
                    areaMineTarget = nextBlock;
                    areaMineAimTicks = 0;
                    return false;
                }
                goalX = next.getX() + 0.5;
                goalZ = next.getZ() + 0.5;
                faceHorizontal(mc.player, goalX, goalZ);
                return true;
            }
        } else {
            areaMoveTicks++;
            if (areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
                areaMoveTicks = 0;
                return false;
            }
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.35;
    }
'''
    rep(old_tail, new_tail, 'fast-turn navigation')
    src.write_text(s)

region_path = Path('eio26/com/eio/client/AreaRegion.java')
r = region_path.read_text()
if 'boolean isRowEnd(int index)' not in r:
    old = '''    String summary() {
'''
    new = '''    boolean isRowEnd(int index) {
        int cells = navigationCells();
        return cells > 0 && index >= 0 && index < cells && ((index + 1) % width()) == 0;
    }

    String summary() {
'''
    if old not in r:
        raise SystemExit('patch target not found: AreaRegion row end helper')
    r = r.replace(old, new, 1)
    region_path.write_text(r)

test_path = Path('src/test/java/com/eio/client/AreaRegionTest.java')
t = test_path.read_text()
if 'identifiesSerpentineRowEndsForFastTurns' not in t:
    old = '''    @Test
    void rejectsOversizedNavigationArea() {
'''
    new = '''    @Test
    void identifiesSerpentineRowEndsForFastTurns() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 1), 2);
        assertFalse(r.isRowEnd(-1));
        assertFalse(r.isRowEnd(0));
        assertFalse(r.isRowEnd(1));
        assertTrue(r.isRowEnd(2));
        assertFalse(r.isRowEnd(3));
        assertFalse(r.isRowEnd(4));
        assertTrue(r.isRowEnd(5));
        assertFalse(r.isRowEnd(6));
    }

    @Test
    void rejectsOversizedNavigationArea() {
'''
    if old not in t:
        raise SystemExit('patch target not found: AreaRegion test insertion')
    t = t.replace(old, new, 1)
    test_path.write_text(t)

print('EIO 0.26 AREA3 fast-turn patch applied')
