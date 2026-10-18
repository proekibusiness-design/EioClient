from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label} patch target not found')
    s = s.replace(old, new, 1)

# This patch intentionally starts from the compatibility/functionality baseline produced by patch010.
replace_once('public static final String VERSION = "0.10.0";', 'public static final String VERSION = "0.13.0";', 'version')
# Stable translation keys from this release onward so user keybinds survive upgrades.
s = s.replace('key.eioclient.v0100.', 'key.eioclient.')

replace_once(
'''    private static Entity followTarget;''',
'''    private static Entity followTarget;
    private static boolean jumpForced;''',
'jump force state')

# Add a self-diagnostic command for fast runtime support.
replace_once(
'''                        .then(ClientCommands.literal("list").executes(c -> {
                            c.getSource().sendFeedback(Component.literal(summary())); return 1;
                        }))''',
'''                        .then(ClientCommands.literal("list").executes(c -> {
                            c.getSource().sendFeedback(Component.literal(summary())); return 1;
                        }))
                        .then(ClientCommands.literal("doctor").executes(c -> {
                            long enabled = MODS.stream().filter(m -> m.enabled).count();
                            long bound = MODS.stream().filter(m -> m.bind != null && !m.bind.isUnbound()).count();
                            String report = "Eio " + VERSION + " | modules=" + MODS.size() + " enabled=" + enabled
                                    + " bound=" + bound + " | GUI=438x254 | config=" + CONFIG.toAbsolutePath();
                            c.getSource().sendFeedback(Component.literal(report));
                            return 1;
                        }))''',
'doctor command')

# Never globally stamp the jump key false. Only release it if Eio actually forced it.
replace_once(
'''        if (mc.player == null) return;''',
'''        if (mc.player == null) {
            if (jumpForced) {
                mc.options.keyJump.setDown(false);
                jumpForced = false;
            }
            return;
        }''',
'worldless jump cleanup')

replace_once(
'''        if (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround()) mc.options.keyJump.setDown(true);
        else if (!test.enabled || testJumpTicks <= 0) mc.options.keyJump.setDown(false);

        if (follow.enabled) runFollow(mc, follow);''',
'''        // Jump forcing is resolved after Test Profile updates so ordinary Space input is not cancelled globally.

        if (follow.enabled) runFollow(mc, follow);''',
'old auto jump forcing')

replace_once(
'''        if (testJumpTicks > 0) {
            mc.options.keyJump.setDown(true);
            testJumpTicks--;
        }

        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);''',
'''        boolean shouldForceJump = (autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (test.enabled && testJumpTicks > 0);
        if (shouldForceJump) {
            mc.options.keyJump.setDown(true);
            jumpForced = true;
        } else if (jumpForced) {
            mc.options.keyJump.setDown(false);
            jumpForced = false;
        }
        if (testJumpTicks > 0) testJumpTicks--;

        if (bright.enabled) maintainFullbright(mc); else clearFullbright(mc);''',
'controlled jump forcing')

# Notifications are a requested core UX feature; default them on for configs that have never explicitly set them.
replace_once(
'''            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, "false"));''',
'''            String enabledDefault = m.name.equals("Notifications") ? "true" : "false";
            m.enabled = Boolean.parseBoolean(p.getProperty("enabled." + m.name, enabledDefault));''',
'notification default')

# Atomic config writes prevent a partially-written properties file after interruption/crash.
replace_once(
'''        try { Files.createDirectories(CONFIG.getParent()); try (OutputStream out = Files.newOutputStream(CONFIG)) { p.store(out, "Eio Client " + VERSION); } } catch (Exception ignored) {}''',
'''        try {
            Files.createDirectories(CONFIG.getParent());
            Path tmp = CONFIG.resolveSibling(CONFIG.getFileName().toString() + ".tmp");
            try (OutputStream out = Files.newOutputStream(tmp, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
                p.store(out, "Eio Client " + VERSION);
            }
            try {
                Files.move(tmp, CONFIG, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException ex) {
                Files.move(tmp, CONFIG, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (Exception ignored) {}''',
'atomic config save')

# Main-menu branding remains double-size and rainbow; ClickGUI itself stays unbranded/minimal.
old_brand = '''    private static void drawBrand(GuiGraphicsExtractor g, int width) {
        String text = "MADE BY EIO";
        int scale = 2;
        int pixelWidth = 0;
        for (int i = 0; i < text.length(); i++) pixelWidth += (text.charAt(i) == ' ' ? 2 : 4) * scale;
        ClickGui.drawBlockBrand(g, width - pixelWidth - 8, 8, scale, 0xFF8CCDF2);
    }'''
new_brand = '''    private static void drawBrand(GuiGraphicsExtractor g, int width) {
        String text = "MADE BY EIO";
        int scale = 2;
        int pixelWidth = 0;
        for (int i = 0; i < text.length(); i++) pixelWidth += (text.charAt(i) == ' ' ? 2 : 4) * scale;
        ClickGui.drawRainbowBlockBrand(g, width - pixelWidth - 8, 8, scale);
    }'''
replace_once(old_brand, new_brand, 'rainbow main menu brand')

# Full GUI replacement. It is compact enough for the user's request but tall enough to expose every current setting.
start = s.index('    public static final class ClickGui extends Screen {')
new_class = r'''    public static final class ClickGui extends Screen {
        private static final String[] CATEGORIES = {"Combat", "Movement", "Player", "Render", "World", "Testing", "Misc"};
        private String selectedCategory = "Combat";
        private Mod selectedMod;

        ClickGui() { super(Component.literal("Eio Client")); }
        @Override public boolean isPauseScreen() { return false; }
        @Override public void added() { super.added(); guiOpen = true; if (selectedMod == null) selectedMod = firstInCategory(selectedCategory); }
        @Override public void removed() { guiOpen = false; save(); super.removed(); }
        @Override public void onClose() { guiOpen = false; save(); super.onClose(); }

        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (m.category.equals(category)) return m;
            return null;
        }

        private int panelW() { return Math.min(438, width - 14); }
        private int panelH() { return Math.min(254, height - 14); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int accent = categoryColor(selectedCategory);
            String help = selectedMod == null ? "Choose a module" : selectedMod.description;

            // Very light dimming, soft shadow, then translucent glass shell.
            g.fill(0, 0, width, height, 0x0A000000);
            g.fill(x + 3, y + 4, x + bw + 3, y + bh + 4, 0x35000000);
            g.fill(x, y, x + bw, y + bh, 0xA0080D13);
            g.fill(x, y, x + bw, y + 22, 0xC0101720);
            g.fill(x, y + 21, x + bw, y + 22, 0x88475562);
            g.fill(x, y, x + 2, y + bh, accent);

            g.text(font, "Eio", x + 9, y + 7, 0xFFF3F8FB, true);
            g.text(font, VERSION, x + 31, y + 7, 0xFF64727E, false);
            String closeHint = "RSHIFT";
            g.text(font, closeHint, x + bw - font.width(closeHint) - 8, y + 7, 0xFF64727E, false);

            // Slim horizontal categories - no large sidebar.
            int tabsX = x + 7, tabsY = y + 27;
            int gap = 2;
            int tabW = (bw - 14 - gap * (CATEGORIES.length - 1)) / CATEGORIES.length;
            for (int i = 0; i < CATEGORIES.length; i++) {
                String category = CATEGORIES[i];
                int tx = tabsX + i * (tabW + gap);
                boolean active = category.equals(selectedCategory);
                boolean hover = in(mx, my, tx, tabsY, tabW, 15);
                g.fill(tx, tabsY, tx + tabW, tabsY + 15, active ? 0xB51A2731 : (hover ? 0x71151F27 : 0x3510151B));
                if (active) g.fill(tx + 4, tabsY + 13, tx + tabW - 4, tabsY + 15, accent);
                g.centeredText(font, shortCat(category), tx + tabW / 2, tabsY + 5, active ? 0xFFF0F6FA : 0xFF8D9AA5);
                if (hover) help = "Category: " + category;
            }

            int bodyY = y + 47;
            int footerY = y + bh - 22;
            int modulesX = x + 7;
            int modulesW = 232;
            int settingsX = modulesX + modulesW + 7;
            int settingsW = x + bw - 7 - settingsX;

            g.fill(modulesX, bodyY, modulesX + modulesW, footerY - 4, 0x480D1218);
            g.fill(settingsX, bodyY, settingsX + settingsW, footerY - 4, 0x480D1218);

            // Dense two-column module cards.
            int cardGap = 4;
            int cardW = (modulesW - 12 - cardGap) / 2;
            int index = 0;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                int col = index % 2;
                int row = index / 2;
                int cx = modulesX + 4 + col * (cardW + cardGap);
                int cy = bodyY + 5 + row * 24;
                boolean selected = m == selectedMod;
                boolean hover = in(mx, my, cx, cy, cardW, 20);
                g.fill(cx, cy, cx + cardW, cy + 20, selected ? 0xA01B2B35 : (hover ? 0x7217212A : 0x3511161C));
                if (m.enabled) g.fill(cx, cy, cx + 2, cy + 20, 0xFF62D39B);
                g.text(font, trim(m.name, 13), cx + 6, cy + 6, m.enabled ? 0xFFF3F7F9 : 0xFFC3CDD5, false);
                String state = m.enabled ? "ON" : "";
                if (!state.isEmpty()) g.text(font, state, cx + cardW - font.width(state) - 5, cy + 6, 0xFF72DDA5, false);
                if (hover) help = m.description;
                index++;
            }

            if (selectedMod == null) {
                g.text(font, "Choose a module", settingsX + 8, bodyY + 10, 0xFFD7E0E8, false);
            } else {
                int sx = settingsX + 6;
                int sw = settingsW - 12;
                int sy = bodyY + 6;

                // Header row doubles as the compact enable switch.
                boolean hoverToggle = in(mx, my, sx, sy, sw, 18);
                g.fill(sx, sy, sx + sw, sy + 18, selectedMod.enabled ? 0x8E1A4A39 : (hoverToggle ? 0x6219222A : 0x3B11171D));
                g.text(font, trim(selectedMod.name, 18), sx + 6, sy + 5, 0xFFF0F4F7, true);
                String state = selectedMod.enabled ? "ON" : "OFF";
                g.text(font, state, sx + sw - font.width(state) - 6, sy + 5, selectedMod.enabled ? 0xFF73DFA7 : 0xFF86929C, false);
                if (hoverToggle) help = "Toggle " + selectedMod.name;
                sy += 21;

                // Key row opens vanilla Controls, preserving Minecraft's native rebinding behavior.
                boolean hoverBind = in(mx, my, sx, sy, sw, 17);
                g.fill(sx, sy, sx + sw, sy + 17, hoverBind ? 0x661A2530 : 0x3511161C);
                String key = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "NONE" : selectedMod.bind.getTranslatedKeyMessage().getString();
                g.text(font, "Keybind", sx + 5, sy + 5, 0xFFBBC5CD, false);
                String keyTrim = trim(key, 10);
                g.text(font, keyTrim, sx + sw - font.width(keyTrim) - 5, sy + 5, 0xFF94D8F6, false);
                if (hoverBind) help = "Open Minecraft Controls to change this keybind";
                sy += 20;

                // Every current module setting fits without hidden/unclickable rows.
                for (Setting setting : selectedMod.settings) {
                    boolean hover = in(mx, my, sx, sy, sw, 18);
                    g.fill(sx, sy, sx + sw, sy + 18, hover ? 0x6119232C : 0x3011161C);
                    if (setting instanceof BoolSetting b) {
                        g.text(font, trim(b.name, 14), sx + 5, sy + 5, 0xFFD5DDE4, false);
                        String value = b.value ? "ON" : "OFF";
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 5, b.value ? 0xFF69D99B : 0xFFC87575, false);
                    } else if (setting instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        g.text(font, trim(n.name, 12), sx + 5, sy + 3, 0xFFD5DDE4, false);
                        String value = n.display();
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 3, 0xFF9DD9FF, false);
                        g.fill(sx + 4, sy + 15, sx + sw - 4, sy + 17, 0x55303C47);
                        g.fill(sx + 4, sy + 15, sx + 4 + (int) ((sw - 8) * ratio), sy + 17, accent);
                    }
                    if (hover) help = setting.description;
                    sy += 19;
                }
            }

            // Fixed help/status footer avoids popups covering controls.
            g.fill(x + 7, footerY, x + bw - 7, y + bh - 6, 0x3210151B);
            g.text(font, trim(help, 66), x + 11, footerY + 5, 0xFF82909B, false);

            super.extractRenderState(g, mx, my, delta);
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            if (e.button() != InputConstants.MOUSE_BUTTON_LEFT) return super.mouseClicked(e, doubled);

            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int tabsX = x + 7, tabsY = y + 27;
            int gap = 2;
            int tabW = (bw - 14 - gap * (CATEGORIES.length - 1)) / CATEGORIES.length;
            for (int i = 0; i < CATEGORIES.length; i++) {
                int tx = tabsX + i * (tabW + gap);
                if (in(e.x(), e.y(), tx, tabsY, tabW, 15)) {
                    selectedCategory = CATEGORIES[i];
                    selectedMod = firstInCategory(selectedCategory);
                    return true;
                }
            }

            int bodyY = y + 47;
            int modulesX = x + 7;
            int modulesW = 232;
            int settingsX = modulesX + modulesW + 7;
            int settingsW = x + bw - 7 - settingsX;
            int cardGap = 4;
            int cardW = (modulesW - 12 - cardGap) / 2;

            int index = 0;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                int col = index % 2;
                int row = index / 2;
                int cx = modulesX + 4 + col * (cardW + cardGap);
                int cy = bodyY + 5 + row * 24;
                if (in(e.x(), e.y(), cx, cy, cardW, 20)) {
                    selectedMod = m;
                    toggle(m);
                    return true;
                }
                index++;
            }

            if (selectedMod != null) {
                int sx = settingsX + 6;
                int sw = settingsW - 12;
                int sy = bodyY + 6;
                if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                    toggle(selectedMod);
                    return true;
                }
                sy += 21;
                if (in(e.x(), e.y(), sx, sy, sw, 17)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 20;
                for (Setting setting : selectedMod.settings) {
                    if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                        if (setting instanceof BoolSetting b) {
                            b.value = !b.value;
                        } else if (setting instanceof NumSetting n) {
                            double ratio = (e.x() - (sx + 4.0)) / Math.max(1.0, sw - 8.0);
                            ratio = Math.max(0.0, Math.min(1.0, ratio));
                            n.set(n.min + ratio * (n.max - n.min));
                        }
                        save();
                        return true;
                    }
                    sy += 19;
                }
            }

            return super.mouseClicked(e, doubled);
        }

        static void drawRainbowBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale) {
            String text = "MADE BY EIO";
            int px = x;
            long now = System.currentTimeMillis();
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                if (c == ' ') { px += 2 * scale; continue; }
                float hue = ((now % 7000L) / 7000f + i * 0.065f) % 1f;
                int rgb = 0xFF000000 | Color.HSBtoRGB(hue, 0.55f, 1.0f);
                String[] pixels = pattern(c);
                for (int row = 0; row < pixels.length; row++) {
                    for (int col = 0; col < pixels[row].length(); col++) {
                        if (pixels[row].charAt(col) == '#') {
                            g.fill(px + col * scale, y + row * scale,
                                    px + (col + 1) * scale, y + (row + 1) * scale, rgb);
                        }
                    }
                }
                px += 4 * scale;
            }
        }

        private static int categoryColor(String category) {
            return switch (category) {
                case "Combat" -> 0xFFE97979;
                case "Movement" -> 0xFF6AC7F0;
                case "Player" -> 0xFF79D69A;
                case "Render" -> 0xFFC497F3;
                case "World" -> 0xFFF0C778;
                case "Testing" -> 0xFFF09A68;
                default -> 0xFF83B7D4;
            };
        }

        private static String[] pattern(char c) {
            return switch (c) {
                case 'M' -> new String[]{"#.#","###","###","#.#","#.#"};
                case 'A' -> new String[]{".#.","#.#","###","#.#","#.#"};
                case 'D' -> new String[]{"##.","#.#","#.#","#.#","##."};
                case 'E' -> new String[]{"###","#..","##.","#..","###"};
                case 'B' -> new String[]{"##.","#.#","##.","#.#","##."};
                case 'Y' -> new String[]{"#.#","#.#",".#.",".#.",".#."};
                case 'I' -> new String[]{"###",".#.",".#.",".#.","###"};
                case 'O' -> new String[]{".#.","#.#","#.#","#.#",".#."};
                default -> new String[]{"...","...","...","...","..."};
            };
        }

        private static String shortCat(String c) {
            return switch (c) {
                case "Movement" -> "Move";
                case "Testing" -> "Test";
                default -> c;
            };
        }

        private static boolean in(double mx, double my, int x, int y, int w, int h) {
            return mx >= x && mx < x + w && my >= y && my < y + h;
        }

        private static String trim(String text, int max) {
            return text.length() <= max ? text : text.substring(0, Math.max(0, max - 1)) + "…";
        }
    }'''

s = s[:start] + new_class + '\n}\n'
p.write_text(s)
print('EioClient 0.13.0 quality release patch applied')
