from pathlib import Path
p = Path('eio26/EioClient.java')
s = p.read_text()
old = 'g.text(mc.font, trim(areaStatus(find("Area Miner")), 70), 5, y, 0xFF8FDCC0, true);'
new = 'g.text(mc.font, areaStatus(find("Area Miner")), 5, y, 0xFF8FDCC0, true);'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('Area Miner HUD fix target not found')
p.write_text(s)
