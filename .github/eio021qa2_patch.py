from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()
old = '''        if (mc.player == null) {
            if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
            if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
            if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
            followTarget = null;
            flyForced = false;
            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            return;
        }'''
new = '''        if (mc.player == null) {
            if (jumpForced) { mc.options.keyJump.setDown(false); jumpForced = false; }
            if (sneakForced) { mc.options.keyShift.setDown(false); sneakForced = false; }
            if (forwardForced) { mc.options.keyUp.setDown(false); forwardForced = false; }
            if (attackForced) { mc.options.keyAttack.setDown(false); attackForced = false; }
            followTarget = null;
            combatTarget = null;
            chunkMineTarget = null;
            clickAccumulator = 0.0;
            auraCooldown = 0;
            triggerCooldown = 0;
            toolSaverWarned = false;
            flyForced = false;
            lowHealthAlerted = false;
            lowHealthCooldown = 0;
            return;
        }'''
if old not in s:
    raise SystemExit('disconnect cleanup target missing')
s = s.replace(old, new, 1)
p.write_text(s)
