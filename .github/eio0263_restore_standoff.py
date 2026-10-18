from pathlib import Path
import subprocess

# Restore the last stable straight-ahead Area Miner implementation from 0.26.1.
subprocess.run(["git", "fetch", "origin", "fix/0.26.1-area-mining", "--depth=1"], check=True)

def restore(path: str) -> None:
    data = subprocess.check_output(["git", "show", f"FETCH_HEAD:{path}"], text=True)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(data)

for path in [
    "eio26/EioClient.java",
    "eio26/com/eio/client/AreaRegion.java",
    "src/test/java/com/eio/client/AreaRegionTest.java",
    "gradle.properties",
]:
    restore(path)

src = Path("eio26/EioClient.java")
s = src.read_text()

s = s.replace('public static final String VERSION = "0.26.1";', 'public static final String VERSION = "0.26.3";', 1)
s = s.replace('public static final String BUILD_ID = "EIO-0261-MINEFIX1";', 'public static final String BUILD_ID = "EIO-0263-STANDOFF2";', 1)

anchor = '    private static int areaNavIndex;\n'
if anchor not in s:
    raise SystemExit("areaNavIndex anchor missing")
s = s.replace(anchor, anchor + '    private static final double AREA_FRONT_STANDOFF = 2.0;\n', 1)

old = '''        if (!outside && distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }'''
new = '''        // Keep the player roughly two blocks behind the freshly-cleared mining front.
        // Advance the serpentine target index instead of walking into every cleared cell.
        if (!outside && distance <= AREA_FRONT_STANDOFF) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }'''
if old not in s:
    raise SystemExit("old Area Miner arrival threshold missing")
s = s.replace(old, new, 1)

# Update the module description only; preserve all 0.26.1 mining behavior/settings.
s = s.replace(
    'mod("Area Miner", "Mining", "Serpentine tunnel miner: clears the next lane cell straight ahead, moves into it, turns at the boundary, shifts one cell and works back across the selected zone.", -1)',
    'mod("Area Miner", "Mining", "Serpentine tunnel miner restored from 0.26.1, keeping a two-block stand-off behind the freshly-cleared mining front.", -1)',
    1,
)

Path("eio26/EioClient.java").write_text(s)

gp = Path("gradle.properties")
g = gp.read_text().replace("mod_version=0.26.1+26.3", "mod_version=0.26.3+26.3", 1)
if "mod_version=0.26.3+26.3" not in g:
    raise SystemExit("gradle version update failed")
gp.write_text(g)

print("Restored 0.26.1 Area Miner and applied fixed 2-block stand-off")
