from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

if 'public static final String VERSION = "0.10.0";' not in s:
    raise SystemExit('Expected 0.10 source before 0.12 GUI patch')
s = s.replace('public static final String VERSION = "0.10.0";', 'public static final String VERSION = "0.12.0";', 1)
s = s.replace('key.eioclient.v0100.', 'key.eioclient.v0120.')

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
if old_brand not in s:
    raise SystemExit('Main menu brand patch target not found')
s = s.replace(old_brand, new_brand, 1)

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

        private int panelW() { return Math.min(420, width - 14); }
        private int panelH() { return Math.min(240, height - 14); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            String tooltip = null;
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();

            // Thin glass shell: intentionally much smaller and more transparent than earlier builds.
            g.fill(0, 0, width, height, 0x0E000000);
            g.fill(x, y, x + bw, y + bh, 0x97080D13);
            g.fill(x, y, x + bw, y + 20, 0xB0101720);
            g.fill(x, y + 20, x + bw, y + 21, 0x994DA8D2);

            g.text(font, "Eio", x + 8, y + 6, 0xFF9BD8F5, true);
            g.text(font, VERSION, x + 30, y + 6, 0xFF5E6C79, false);
            String closeHint = "RSHIFT";
            g.text(font, closeHint, x + bw - font.width(closeHint) - 8, y + 6, 0xFF596875, false);

            // Slim category pills across the top.
            int tabsX = x + 6, tabsY = y + 25;
            int gap = 2;
            int tabW = (bw - 12 - gap * (CATEGORIES.length - 1)) / CATEGORIES.length;
            for (int i = 0; i < CATEGORIES.length; i++) {
                String category = CATEGORIES[i];
                int tx = tabsX + i * (tabW + gap);
                boolean active = category.equals(selectedCategory);
                boolean hover = in(mx, my, tx, tabsY, tabW, 14);
                g.fill(tx, tabsY, tx + tabW, tabsY + 14, active ? 0xB5264A5C : (hover ? 0x7518232D : 0x3C11171D));
                if (active) g.fill(tx + 4, tabsY + 12, tx + tabW - 4, tabsY + 14, 0xFF5BC3EE);
                g.centeredText(font, shortCat(category), tx + tabW / 2, tabsY + 4, active ? 0xFFEAF8FF : 0xFF91A0AD);
                if (hover) tooltip = category;
            }

            int bodyY = y + 44;
            int footerY = y + bh - 15;
            int modulesX = x + 7;
            int modulesW = 228;
            int settingsX = modulesX + modulesW + 7;
            int settingsW = x + bw - 7 - settingsX;

            g.fill(modulesX, bodyY, modulesX + modulesW, footerY - 3, 0x4F0D1218);
            g.fill(settingsX, bodyY, settingsX + settingsW, footerY - 3, 0x4F0D1218);

            // Two-column module grid: dramatically denser than old vertical list.
            int cardGap = 4;
            int cardW = (modulesW - 12 - cardGap) / 2;
            int index = 0;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                int col = index % 2;
                int row = index / 2;
                int cx = modulesX + 4 + col * (cardW + cardGap);
                int cy = bodyY + 5 + row * 23;
                boolean selected = m == selectedMod;
                boolean hover = in(mx, my, cx, cy, cardW, 19);
                g.fill(cx, cy, cx + cardW, cy + 19, selected ? 0xA01A303D : (hover ? 0x7217212A : 0x3511161C));
                if (m.enabled) g.fill(cx, cy, cx + 2, cy + 19, 0xFF61D49A);
                g.text(font, trim(m.name, 13), cx + 6, cy + 6, m.enabled ? 0xFFF2F7FA : 0xFFC4CDD5, false);
                if (hover) tooltip = m.description;
                index++;
            }

            // Narrow settings inspector.
            if (selectedMod == null) {
                g.text(font, "Choose a module", settingsX + 8, bodyY + 10, 0xFFD7E0E8, false);
            } else {
                int sx = settingsX + 6;
                int sw = settingsW - 12;
                int sy = bodyY + 6;
                g.text(font, trim(selectedMod.name, 19), sx, sy, 0xFFFFFFFF, true);
                sy += 13;
                g.text(font, trim(selectedMod.description, 29), sx, sy, 0xFF7E8D99, false);
                sy += 16;

                boolean hoverToggle = in(mx, my, sx, sy, sw, 16);
                g.fill(sx, sy, sx + sw, sy + 16, selectedMod.enabled ? 0xA51D6047 : 0x6D192128);
                g.text(font, selectedMod.enabled ? "ENABLED" : "DISABLED", sx + 6, sy + 4,
                        selectedMod.enabled ? 0xFF78E1AA : 0xFFADB8C1, false);
                if (hoverToggle) tooltip = "Toggle " + selectedMod.name;
                sy += 19;

                boolean hoverBind = in(mx, my, sx, sy, sw, 16);
                g.fill(sx, sy, sx + sw, sy + 16, hoverBind ? 0x6F1A2630 : 0x3E12181E);
                String key = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "NONE" : selectedMod.bind.getTranslatedKeyMessage().getString();
                g.text(font, "Key", sx + 6, sy + 4, 0xFFB9C3CC, false);
                g.text(font, trim(key, 10), sx + sw - font.width(trim(key, 10)) - 6, sy + 4, 0xFF91D7F6, false);
                if (hoverBind) tooltip = "Click to open Minecraft keybind settings";
                sy += 19;

                for (Setting setting : selectedMod.settings) {
                    if (sy + 17 > footerY - 5) break;
                    boolean hover = in(mx, my, sx, sy, sw, 17);
                    g.fill(sx, sy, sx + sw, sy + 17, hover ? 0x6519232C : 0x3211161C);
                    if (setting instanceof BoolSetting b) {
                        g.text(font, trim(b.name, 15), sx + 5, sy + 5, 0xFFD5DDE4, false);
                        String value = b.value ? "ON" : "OFF";
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 5,
                                b.value ? 0xFF69D99B : 0xFFCC7777, false);
                    } else if (setting instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        g.text(font, trim(n.name, 13), sx + 5, sy + 3, 0xFFD5DDE4, false);
                        String value = n.display();
                        g.text(font, value, sx + sw - font.width(value) - 5, sy + 3, 0xFF9DD9FF, false);
                        g.fill(sx + 4, sy + 14, sx + sw - 4, sy + 16, 0x55303C47);
                        g.fill(sx + 4, sy + 14, sx + 4 + (int) ((sw - 8) * ratio), sy + 16, 0xFF55AFE0);
                    }
                    if (hover) tooltip = setting.description;
                    sy += 19;
                }
            }

            // Tiny footer only; no oversized GUI branding.
            g.text(font, "LMB toggle • hover help", x + 7, footerY, 0xFF53616E, false);

            if (tooltip != null && !tooltip.isEmpty()) {
                String t = trim(tooltip, 62);
                int tw = Math.min(bw - 14, font.width(t) + 10);
                int tx = Math.max(x + 5, Math.min(mx + 7, x + bw - tw - 5));
                int ty = Math.max(y + 22, Math.min(my + 9, y + bh - 19));
                g.fill(tx, ty, tx + tw, ty + 15, 0xE5070B0F);
                g.text(font, t, tx + 5, ty + 4, 0xFFE5EDF3, false);
            }

            super.extractRenderState(g, mx, my, delta);
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            if (e.button() != InputConstants.MOUSE_BUTTON_LEFT) return super.mouseClicked(e, doubled);

            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int tabsX = x + 6, tabsY = y + 25;
            int gap = 2;
            int tabW = (bw - 12 - gap * (CATEGORIES.length - 1)) / CATEGORIES.length;
            for (int i = 0; i < CATEGORIES.length; i++) {
                int tx = tabsX + i * (tabW + gap);
                if (in(e.x(), e.y(), tx, tabsY, tabW, 14)) {
                    selectedCategory = CATEGORIES[i];
                    selectedMod = firstInCategory(selectedCategory);
                    return true;
                }
            }

            int bodyY = y + 44;
            int footerY = y + bh - 15;
            int modulesX = x + 7;
            int modulesW = 228;
            int settingsX = modulesX + modulesW + 7;
            int settingsW = x + bw - 7 - settingsX;
            int cardGap = 4;
            int cardW = (modulesW - 12 - cardGap) / 2;

            int index = 0;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                int col = index % 2;
                int row = index / 2;
                int cx = modulesX + 4 + col * (cardW + cardGap);
                int cy = bodyY + 5 + row * 23;
                if (in(e.x(), e.y(), cx, cy, cardW, 19)) {
                    selectedMod = m;
                    toggle(m);
                    return true;
                }
                index++;
            }

            if (selectedMod != null) {
                int sx = settingsX + 6;
                int sw = settingsW - 12;
                int sy = bodyY + 6 + 13 + 16;
                if (in(e.x(), e.y(), sx, sy, sw, 16)) {
                    toggle(selectedMod);
                    return true;
                }
                sy += 19;
                if (in(e.x(), e.y(), sx, sy, sw, 16)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 19;
                for (Setting setting : selectedMod.settings) {
                    if (sy + 17 > footerY - 5) break;
                    if (in(e.x(), e.y(), sx, sy, sw, 17)) {
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
                String[] p = pattern(c);
                for (int row = 0; row < p.length; row++) {
                    for (int col = 0; col < p[row].length(); col++) {
                        if (p[row].charAt(col) == '#') {
                            g.fill(px + col * scale, y + row * scale,
                                    px + (col + 1) * scale, y + (row + 1) * scale, rgb);
                        }
                    }
                }
                px += 4 * scale;
            }
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

        private static String trim(String s, int max) {
            return s.length() <= max ? s : s.substring(0, Math.max(0, max - 1)) + "…";
        }
    }'''

s = s[:start] + new_class + '\n}\n'
p.write_text(s)
print('EioClient 0.12.0 ultra-compact GUI redesign applied')
