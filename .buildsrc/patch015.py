from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

old_module = '''        mod("Chunk Info", "World", "Shows your current chunk coordinates.", -1);
        mod("World Time", "World", "Shows the current in-game world time as a 24-hour clock.", -1);
        mod("Waypoints", "World", "Shows your nearest saved waypoint and distance.", -1);'''
new_module = '''        mod("Chunk Info", "World", "Shows your current chunk coordinates.", -1);
        mod("Waypoints", "World", "Shows your nearest saved waypoint and distance.", -1);'''
if old_module not in s:
    raise SystemExit('World Time module block not found')
s = s.replace(old_module, new_module, 1)

old_hud = '''        if (find("World Time").enabled && mc.level != null) {
            long ticks = Math.floorMod(mc.level.getDayTime(), 24000L);
            long totalMinutes = (ticks * 60L / 1000L + 360L) % 1440L;
            g.text(mc.font, String.format(Locale.ROOT, "World %02d:%02d", totalMinutes / 60L, totalMinutes % 60L), 5, y, 0xFFD9E0E6, true); y += 11;
        }
'''
if old_hud not in s:
    raise SystemExit('World Time HUD block not found')
s = s.replace(old_hud, '', 1)

p.write_text(s)
print('Removed unverified World Time API from 0.14 candidate')
