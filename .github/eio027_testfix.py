from pathlib import Path

p = Path('src/test/java/com/eio/client/AreaRegionTest.java')
s = p.read_text()
old = '''        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 2), 3);\n        assertTrue(r.contains(new BlockPos(1, 63, 1)));\n        assertFalse(r.contains(new BlockPos(1, 64, 1)), "surface marker Y itself must never be mined");\n        assertFalse(r.contains(new BlockPos(3, 63, 1)));\n        assertFalse(r.contains(new BlockPos(1, 60, 1)));'''
new = '''        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 2), 5);\n        assertTrue(r.contains(new BlockPos(1, 63, 1)));\n        assertTrue(r.contains(new BlockPos(1, 59, 1)));\n        assertFalse(r.contains(new BlockPos(1, 64, 1)), "surface marker Y itself must never be mined");\n        assertFalse(r.contains(new BlockPos(3, 63, 1)));\n        assertFalse(r.contains(new BlockPos(1, 58, 1)));'''
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('containsOnlyConfiguredVolume test anchor not found')
p.write_text(s)
print('0.27 test contract aligned to 5-block minimum')
