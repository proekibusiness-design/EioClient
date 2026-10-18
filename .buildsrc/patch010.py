from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label} patch target not found')
    s = s.replace(old, new, 1)

replace_once('public static final String VERSION = "0.9.0";', 'public static final String VERSION = "0.10.0";', 'version')
s = s.replace('key.eioclient.v090.', 'key.eioclient.v0100.')

replace_once(
'''        mod("Auto Clicker", "Combat", "Automatically attacks the entity under your crosshair at a fixed configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Fixed clicks per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance to the crosshair target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.");''',
'''        mod("Auto Clicker", "Combat", "Automatically attacks a valid target near your crosshair at the configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Attack attempts per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance used when selecting a click target.")
                .num("FOV", 18.0, 5.0, 90.0, 1.0, "Maximum angle from your crosshair used when selecting a target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.");''',
'auto clicker settings')

replace_once(
'''        if (clicker.enabled) {
            if (clickCooldown-- <= 0) {
                int cps = Math.max(1, (int) Math.round(clicker.num("CPS").value));
                clickCooldown = Math.max(1, 20 / cps);
                if (mc.hitResult instanceof EntityHitResult hit && validClickTarget(mc, clicker, hit.getEntity())) attack(mc, hit.getEntity());
            }
        } else clickCooldown = 0;''',
'''        if (clicker.enabled) {
            if (clickCooldown-- <= 0) {
                int cps = Math.max(1, (int) Math.round(clicker.num("CPS").value));
                clickCooldown = Math.max(1, (int) Math.round(20.0 / cps));
                Entity clickTarget = null;
                if (mc.hitResult instanceof EntityHitResult hit && validClickTarget(mc, clicker, hit.getEntity())) {
                    clickTarget = hit.getEntity();
                }
                if (clickTarget == null) {
                    clickTarget = nearestTarget(mc, clicker.num("Range").value, clicker.num("FOV").value,
                            clicker.bool("Players").value, clicker.bool("Mobs").value, clicker.bool("Invisible").value);
                }
                if (clickTarget != null) attack(mc, clickTarget);
            }
        } else clickCooldown = 0;''',
'auto clicker tick')

replace_once(
'''        if (!(target instanceof Player) && !clicker.bool("Mobs").value) return false;
        double r = clicker.num("Range").value;''',
'''        if (!(target instanceof Player) && !clicker.bool("Mobs").value) return false;
        if (target.isInvisible() && !clicker.bool("Invisible").value) return false;
        if (angleFromView(mc.player, target) > clicker.num("FOV").value / 2.0) return false;
        double r = clicker.num("Range").value;''',
'auto clicker validation')

s = s.replace('int bw = Math.min(700, width - 24), bh = Math.min(390, height - 24);',
              'int bw = Math.min(560, width - 24), bh = Math.min(320, height - 24);')
s = s.replace('int side = 112, cy = y + 45;', 'int side = 90, cy = y + 45;')
s = s.replace('int lx = x + side + 11, ly = y + 42, lw = 205, ry = ly + 7;',
              'int lx = x + side + 9, ly = y + 42, lw = 160, ry = ly + 7;')
s = s.replace('int lx = x + 123, ly = y + 42, ry = ly + 7, lw = 205;',
              'int lx = x + 99, ly = y + 42, ry = ly + 7, lw = 160;')
s = s.replace('if (in(e.x(), e.y(), x + 6, cy - 5, 100, 20))',
              'if (in(e.x(), e.y(), x + 6, cy - 5, 78, 20))')
s = s.replace('drawBlockBrand(g, x + 11, y + bh - 22, 2, 0xFF7CAFD0);',
              'drawBlockBrand(g, x + 11, y + bh - 14, 1, 0xFF7CAFD0);')
s = s.replace('g.fill(0, 0, width, height, 0x35070A0E);', 'g.fill(0, 0, width, height, 0x24070A0E);')
s = s.replace('g.fill(x, y, x + bw, y + bh, 0xD9121720);', 'g.fill(x, y, x + bw, y + bh, 0xC9121720);')

replace_once(
'''    private static void drawBrand(GuiGraphicsExtractor g, int width) {
        Minecraft mc = Minecraft.getInstance();
        String text = "Made by Eio";
        int x = width - mc.font.width(text) - 7, y = 7;
        long now = System.currentTimeMillis();
        for (int i = 0; i < text.length(); i++) {
            String ch = text.substring(i, i + 1);
            float hue = ((now % 8000L) / 8000f + i * .035f) % 1f;
            int rgb = Color.HSBtoRGB(hue, .32f, 1f);
            g.text(mc.font, ch, x, y, 0xFF000000 | rgb, false);
            x += mc.font.width(ch);
        }
    }''',
'''    private static void drawBrand(GuiGraphicsExtractor g, int width) {
        String text = "MADE BY EIO";
        int scale = 2;
        int pixelWidth = 0;
        for (int i = 0; i < text.length(); i++) pixelWidth += (text.charAt(i) == ' ' ? 2 : 4) * scale;
        ClickGui.drawBlockBrand(g, width - pixelWidth - 8, 8, scale, 0xFF8CCDF2);
    }''',
'main menu brand')

s = s.replace('private static void drawBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale, int color)',
              'static void drawBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale, int color)')

p.write_text(s)
print('EioClient 0.10.0 source patch applied successfully')
