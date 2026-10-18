from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()
old = '            if (mc.gameMode.continueDestroyBlock(areaDestroyTarget, face)) mc.player.swing(InteractionHand.MAIN_HAND);'
new = '            mc.gameMode.continueDestroyBlock(areaDestroyTarget, face);'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('Area Miner continueDestroyBlock call not found')
p.write_text(s)
