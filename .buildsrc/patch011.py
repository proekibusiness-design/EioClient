from pathlib import Path

p = Path('src/main/java/com/eio/client/EioClient.java')
s = p.read_text()

s = s.replace('public static final String VERSION = "0.10.0";', 'public static final String VERSION = "0.11.0";')
s = s.replace('key.eioclient.v0100.', 'key.eioclient.v0110.')

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
        @Override public void tick() { super.tick(); }

        private Mod firstInCategory(String category) {
            for (Mod m : MODS) if (m.category.equals(category)) return m;
            return null;
        }

        private int panelW() { return Math.min(480, width - 16); }
        private int panelH() { return Math.min(270, height - 16); }
        private int panelX() { return (width - panelW()) / 2; }
        private int panelY() { return (height - panelH()) / 2; }

        @Override
        public void extractRenderState(GuiGraphicsExtractor g, int mx, int my, float delta) {
            String tooltip = null;
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();

            // Lightweight glass overlay and compact body.
            g.fill(0, 0, width, height, 0x16000000);
            g.fill(x, y, x + bw, y + bh, 0xA80B1016);
            g.fill(x, y, x + bw, y + 24, 0xB9131A23);
            g.fill(x, y + 24, x + bw, y + 25, 0x884D9FCB);

            g.text(font, "Eio", x + 9, y + 8, 0xFF8CCDF2, true);
            g.text(font, VERSION, x + 31, y + 8, 0xFF657585, false);
            String hint = "RSHIFT";
            g.text(font, hint, x + bw - font.width(hint) - 9, y + 8, 0xFF667483, false);

            // Horizontal category tabs: no fat sidebar.
            int tabsX = x + 7, tabsY = y + 29;
            int tabGap = 3;
            int tabW = Math.max(48, (bw - 14 - tabGap * (CATEGORIES.length - 1)) / CATEGORIES.length);
            for (int i = 0; i < CATEGORIES.length; i++) {
                String c = CATEGORIES[i];
                int tx = tabsX + i * (tabW + tabGap);
                boolean active = c.equals(selectedCategory);
                boolean hover = in(mx, my, tx, tabsY, tabW, 17);
                g.fill(tx, tabsY, tx + tabW, tabsY + 17, active ? 0xC01B3442 : (hover ? 0x9A17212B : 0x6410151B));
                if (active) g.fill(tx, tabsY + 15, tx + tabW, tabsY + 17, 0xFF55B7E8);
                String label = shortCat(c);
                g.centeredText(font, label, tx + tabW / 2, tabsY + 5, active ? 0xFFE8F5FF : 0xFF9AA7B4);
                if (hover) tooltip = "Show " + c + " modules";
            }

            int contentY = y + 51;
            int leftX = x + 8;
            int leftW = 150;
            int rightX = leftX + leftW + 8;
            int rightW = x + bw - 8 - rightX;
            int contentBottom = y + bh - 25;

            g.fill(leftX, contentY, leftX + leftW, contentBottom, 0x7410151B);
            g.fill(rightX, contentY, rightX + rightW, contentBottom, 0x7410151B);

            // Compact module list.
            int ry = contentY + 5;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                boolean chosen = m == selectedMod;
                boolean hover = in(mx, my, leftX + 4, ry, leftW - 8, 21);
                int bg = chosen ? 0xB71B2A35 : (hover ? 0x8C17212A : 0x4012171D);
                g.fill(leftX + 4, ry, leftX + leftW - 4, ry + 21, bg);
                if (m.enabled) g.fill(leftX + 4, ry, leftX + 6, ry + 21, 0xFF55C18B);
                g.text(font, trim(m.name, 18), leftX + 10, ry + 7, chosen ? 0xFFFFFFFF : 0xFFD4DCE4, false);
                String state = m.enabled ? "ON" : "OFF";
                g.text(font, state, leftX + leftW - font.width(state) - 9, ry + 7, m.enabled ? 0xFF69D99B : 0xFF68737F, false);
                if (hover) tooltip = m.description;
                ry += 24;
            }

            if (selectedMod == null) {
                g.text(font, "Select a module", rightX + 10, contentY + 11, 0xFFDCE4EB, false);
                g.text(font, "Everything is edited here.", rightX + 10, contentY + 28, 0xFF6F7D89, false);
            } else {
                int sx = rightX + 8;
                int sw = rightW - 16;
                int sy = contentY + 7;

                g.text(font, selectedMod.name, sx, sy, 0xFFFFFFFF, true);
                sy += 13;
                g.text(font, trim(selectedMod.description, 47), sx, sy, 0xFF8E9AA6, false);
                sy += 17;

                boolean hoverToggle = in(mx, my, sx, sy, sw, 18);
                g.fill(sx, sy, sx + sw, sy + 18, selectedMod.enabled ? 0xA51E5C45 : 0x8B1A222A);
                g.text(font, selectedMod.enabled ? "Enabled" : "Disabled", sx + 7, sy + 5, selectedMod.enabled ? 0xFF7AE0A7 : 0xFFB5BEC7, false);
                String toggleHint = "CLICK";
                g.text(font, toggleHint, sx + sw - font.width(toggleHint) - 7, sy + 5, 0xFF667584, false);
                if (hoverToggle) tooltip = "Toggle " + selectedMod.name;
                sy += 22;

                boolean hoverBind = in(mx, my, sx, sy, sw, 18);
                g.fill(sx, sy, sx + sw, sy + 18, hoverBind ? 0x8619232D : 0x65151B22);
                String key = selectedMod.bind == null || selectedMod.bind.isUnbound() ? "None" : selectedMod.bind.getTranslatedKeyMessage().getString();
                g.text(font, "Keybind", sx + 7, sy + 5, 0xFFB8C3CD, false);
                g.text(font, key, sx + sw - font.width(key) - 7, sy + 5, 0xFF8CCDF2, false);
                if (hoverBind) tooltip = "Open Minecraft controls to change this keybind";
                sy += 22;

                for (Setting setting : selectedMod.settings) {
                    boolean hover = in(mx, my, sx, sy, sw, 18);
                    g.fill(sx, sy, sx + sw, sy + 18, hover ? 0x7E19222B : 0x4D12171D);
                    if (setting instanceof BoolSetting b) {
                        g.text(font, b.name, sx + 7, sy + 5, 0xFFD8E0E7, false);
                        String value = b.value ? "ON" : "OFF";
                        g.text(font, value, sx + sw - font.width(value) - 7, sy + 5, b.value ? 0xFF69D99B : 0xFFCC7575, false);
                    } else if (setting instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        g.text(font, n.name, sx + 7, sy + 4, 0xFFD8E0E7, false);
                        String value = n.display();
                        g.text(font, value, sx + sw - font.width(value) - 7, sy + 4, 0xFF9DD9FF, false);
                        g.fill(sx + 4, sy + 16, sx + sw - 4, sy + 18, 0x5535424E);
                        g.fill(sx + 4, sy + 16, sx + 4 + (int) ((sw - 8) * ratio), sy + 18, 0xFF4D9FCB);
                    }
                    if (hover) tooltip = setting.description;
                    sy += 20;
                }

                if (selectedMod.name.equals("Follow") && sy < contentBottom - 12) {
                    g.text(font, "/eio followtarget", sx, sy + 2, 0xFF657585, false);
                } else if (selectedMod.name.equals("Waypoints") && sy < contentBottom - 12) {
                    g.text(font, "/eio waypoint add <name>", sx, sy + 2, 0xFF657585, false);
                }
            }

            // Small floating hover description.
            if (tooltip != null && !tooltip.isEmpty()) {
                String t = trim(tooltip, 70);
                int tw = Math.min(bw - 18, font.width(t) + 12);
                int tx = Math.max(x + 5, Math.min(mx + 8, x + bw - tw - 5));
                int ty = Math.max(y + 27, Math.min(my + 10, y + bh - 20));
                g.fill(tx, ty, tx + tw, ty + 16, 0xE4080C11);
                g.text(font, t, tx + 6, ty + 5, 0xFFE4EBF1, false);
            }

            g.text(font, "Left click modules to toggle • click settings to edit • click Keybind to open controls",
                    x + 8, y + bh - 15, 0xFF657585, false);
            super.extractRenderState(g, mx, my, delta);
        }

        @Override
        public boolean mouseClicked(MouseButtonEvent e, boolean doubled) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            boolean leftClick = e.button() == InputConstants.MOUSE_BUTTON_LEFT;
            if (!leftClick) return super.mouseClicked(e, doubled);

            int tabsX = x + 7, tabsY = y + 29;
            int tabGap = 3;
            int tabW = Math.max(48, (bw - 14 - tabGap * (CATEGORIES.length - 1)) / CATEGORIES.length);
            for (int i = 0; i < CATEGORIES.length; i++) {
                int tx = tabsX + i * (tabW + tabGap);
                if (in(e.x(), e.y(), tx, tabsY, tabW, 17)) {
                    selectedCategory = CATEGORIES[i];
                    selectedMod = firstInCategory(selectedCategory);
                    return true;
                }
            }

            int contentY = y + 51;
            int leftX = x + 8;
            int leftW = 150;
            int rightX = leftX + leftW + 8;
            int rightW = x + bw - 8 - rightX;
            int ry = contentY + 5;

            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                if (in(e.x(), e.y(), leftX + 4, ry, leftW - 8, 21)) {
                    selectedMod = m;
                    toggle(m);
                    return true;
                }
                ry += 24;
            }

            if (selectedMod != null) {
                int sx = rightX + 8;
                int sw = rightW - 16;
                int sy = contentY + 7 + 13 + 17;

                if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                    toggle(selectedMod);
                    return true;
                }
                sy += 22;

                if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                    Minecraft mc = Minecraft.getInstance();
                    mc.setScreenAndShow(new KeyBindsScreen(this, mc.options));
                    return true;
                }
                sy += 22;

                for (Setting setting : selectedMod.settings) {
                    if (in(e.x(), e.y(), sx, sy, sw, 18)) {
                        if (setting instanceof BoolSetting b) {
                            b.value = !b.value;
                        } else if (setting instanceof NumSetting n) {
                            double ratio = (e.x() - sx) / Math.max(1.0, sw);
                            ratio = Math.max(0.0, Math.min(1.0, ratio));
                            n.set(n.min + ratio * (n.max - n.min));
                        }
                        save();
                        return true;
                    }
                    sy += 20;
                }
            }

            return super.mouseClicked(e, doubled);
        }

        static void drawBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale, int color) {
            String text = "MADE BY EIO";
            int px = x;
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                if (c == ' ') { px += 2 * scale; continue; }
                String[] p = pattern(c);
                for (int row = 0; row < p.length; row++) {
                    for (int col = 0; col < p[row].length(); col++) {
                        if (p[row].charAt(col) == '#') {
                            g.fill(px + col * scale, y + row * scale,
                                    px + (col + 1) * scale, y + (row + 1) * scale, color);
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
print('EioClient 0.11.0 compact GUI redesign applied')
