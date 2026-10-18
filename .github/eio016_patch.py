from pathlib import Path
import runpy
import subprocess

# Load the exact full transformer from the known-good 0.16 transformer commit,
# independent of the current branch ancestry. This file is temporary and will
# be deleted after the upgraded source is canonicalized.
TRANSFORM_COMMIT = '5036e4721603b15f7e3c56ba21fc2edf1326eb30'
subprocess.run(['git', 'fetch', '--no-tags', '--depth=1', 'origin', TRANSFORM_COMMIT], check=True)
base = subprocess.check_output(
    ['git', 'show', 'FETCH_HEAD:.github/eio016_patch.py'],
    text=True,
)
tmp = Path('/tmp/eio016_base_patch.py')
tmp.write_text(base)
runpy.run_path(str(tmp), run_name='__main__')

# Correct the single Java-regex escape issue found by the Java 25 compile gate.
source = Path('eio26/EioClient.java')
s = source.read_text()
bad = 'replaceFirst("\\.properties$", "")'
good = 'replaceFirst("\\\\.properties$", "")'
if bad not in s:
    raise SystemExit('generated Java profile regex target not found')
source.write_text(s.replace(bad, good, 1))
