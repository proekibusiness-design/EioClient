from pathlib import Path
import runpy
import subprocess

# Reuse the complete transformer from the parent commit, then correct the
# Java regex escape before compilation. This wrapper is temporary and is
# deleted after the 0.16 source is canonicalized.
base = subprocess.check_output(
    ['git', 'show', 'HEAD^:.github/eio016_patch.py'],
    text=True,
)
tmp = Path('/tmp/eio016_base_patch.py')
tmp.write_text(base)
runpy.run_path(str(tmp), run_name='__main__')

source = Path('eio26/EioClient.java')
s = source.read_text()
bad = 'replaceFirst("\\.properties$", "")'
good = 'replaceFirst("\\\\.properties$", "")'
if bad not in s:
    raise SystemExit('generated Java profile regex target not found')
source.write_text(s.replace(bad, good, 1))
