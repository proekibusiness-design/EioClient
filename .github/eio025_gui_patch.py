from pathlib import Path

src = Path('eio26/EioClient.java')
s = src.read_text()

if 'public static final String VERSION = "0.25.0";' not in s:
    def rep(old, new, label, count=1):
        global s
        if old not in s:
            raise SystemExit('patch target not found: ' + label)
        s = s.replace(old, new, count)

    rep('public static final String VERSION = "0.24.0";', 'public static final String VERSION = "0.25.0";', 'version')
    rep('public static final String BUILD_ID = "EIO-024-COMPAT1";', 'public static final String BUILD_ID = "EIO-025-GUI1";', 'build id')
    rep('GUI=690x390 scrollable-glass', 'GUI=720x410 modern-scroll-glass', 'doctor gui id')

    rep('''        private int settingsScroll;
        private int modulesScroll;
        private static final int MOB_SELECTOR_HEIGHT = 130;''', '''        private int settingsScroll;
        private int modulesScroll;
        private int categoriesScroll;
        private static final int MOB_SELECTOR_HEIGHT = 130;''', 'category scroll state')

    rep('''            settingsScroll = 0;
            modulesScroll = 0;
        }''', '''            settingsScroll = 0;
            modulesScroll = 0;
            categoriesScroll = 0;
        }''', 'initial scroll reset')

    rep('''        private int panelW() { return Math.max(430, Math.min(690, width - 18)); }
        private int panelH() { return Math.max(270, Math.min(390, height - 18)); }''', '''        private int panelW() { return Math.max(430, Math.min(720, width - 18)); }
        private int panelH() { return Math.max(270, Math.min(410, height - 18)); }''', 'modern dimensions')

    # Modern translucent shell and slightly wider navigation rail in render/click/scroll layouts.
    s = s.replace('int railX = x + 10, railW = 98;', 'int railX = x + 10, railW = 108;')
    s = s.replace('g.fill(0, 0, width, height, 0x06000000);', 'g.fill(0, 0, width, height, 0x04000000);')
    s = s.replace('g.fill(x + 5, y + 7, x + bw + 5, y + bh + 7, 0x18000000);', 'g.fill(x + 5, y + 7, x + bw + 5, y + bh + 7, 0x12000000);')
    s = s.replace('g.fill(x, y, x + bw, y + bh, 0x72090E14);', 'g.fill(x, y, x + bw, y + bh, 0x56090E14);')
    s = s.replace('g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x24131A22);', 'g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x18131A22);')
    s = s.replace('g.fill(x, y, x + bw, y + 31, 0x920C131B);', 'g.fill(x, y, x + bw, y + 31, 0x700C131B);')
    s = s.replace('g.fill(railX, bodyY, railX + railW, footerY - 6, 0x2E10171F);', 'g.fill(railX, bodyY, railX + railW, footerY - 6, 0x2410171F);')
    s = s.replace('g.fill(modsX, bodyY, modsX + modsW, footerY - 6, 0x2410171F);', 'g.fill(modsX, bodyY, modsX + modsW, footerY - 6, 0x1C10171F);')
    s = s.replace('g.fill(detailX, bodyY, detailX + detailW, footerY - 6, 0x2A10171F);', 'g.fill(detailX, bodyY, detailX + detailW, footerY - 6, 0x2210171F);')

    rep('''            g.fill(x, y + 30, x + bw, y + 31, 0x50405260);
            g.fill(x, y, x + 3, y + bh, accent);''', '''            g.fill(x, y + 30, x + bw, y + 31, 0x3A405260);
            g.fill(x + 3, y + 30, x + Math.min(110, Math.max(60, bw / 5)), y + 32, accent);
            g.fill(x, y, x + 3, y + bh, accent);''', 'modern header accent')

    old_render = '''            g.text(font, "CATEGORIES", railX + 8, bodyY + 8, 0xFF61717E, false);
            int cy = bodyY + 23;
            for (String category : CATEGORIES) {
                boolean active = category.equals(selectedCategory);
                boolean hover = in(mx, my, railX + 5, cy, railW - 10, 25);
                if (hover || active) g.fill(railX + 5, cy, railX + railW - 5, cy + 25, active ? 0x8A1B2731 : 0x4518232C);
                if (active) g.fill(railX + 5, cy + 5, railX + 8, cy + 20, accent);
                g.text(font, shortCat(category), railX + 14, cy + 8, active ? 0xFFF3F7FA : 0xFFAAB5BD, active);
                String count = Integer.toString(categoryCount(category));
                g.text(font, count, railX + railW - font.width(count) - 12, cy + 8, active ? accent : 0xFF596873, false);
                if (hover) help = "Open " + category + " modules";
                cy += 28;
            }
'''
    new_render = '''            g.text(font, "CATEGORIES", railX + 8, bodyY + 8, 0xFF738592, false);
            int categoryTop = bodyY + 23;
            int categoryBottom = footerY - 9;
            int categoryViewport = Math.max(1, categoryBottom - categoryTop);
            int categoryMax = Math.max(0, CATEGORIES.length * 28 - categoryViewport);
            categoriesScroll = clampScroll(categoriesScroll, categoryMax);
            int cy = categoryTop - categoriesScroll;
            for (String category : CATEGORIES) {
                boolean active = category.equals(selectedCategory);
                boolean visible = cy + 25 > categoryTop && cy < categoryBottom;
                boolean fullyVisible = cy >= categoryTop && cy + 25 <= categoryBottom;
                boolean hover = fullyVisible && in(mx, my, railX + 5, cy, railW - 10, 25);
                if (visible) {
                    int drawTop = Math.max(cy, categoryTop);
                    int drawBottom = Math.min(cy + 25, categoryBottom);
                    if (hover || active) g.fill(railX + 5, drawTop, railX + railW - 5, drawBottom,
                            active ? 0x761B2731 : 0x3818232C);
                    if (active) g.fill(railX + 5, Math.max(drawTop, cy + 5), railX + 8, Math.min(drawBottom, cy + 20), accent);
                    if (fullyVisible) {
                        g.text(font, shortCat(category), railX + 14, cy + 8, active ? 0xFFF4F8FA : 0xFFABB7BF, active);
                        String count = Integer.toString(categoryCount(category));
                        int badgeX = railX + railW - font.width(count) - 15;
                        g.fill(badgeX - 4, cy + 5, railX + railW - 7, cy + 20, active ? 0x402B3A44 : 0x261A232A);
                        g.text(font, count, badgeX, cy + 8, active ? accent : 0xFF667681, false);
                        if (hover) help = "Open " + category + " modules";
                    }
                }
                cy += 28;
            }
            drawScrollBar(g, railX + railW - 3, categoryTop, categoryViewport, categoriesScroll, categoryMax, accent);
'''
    rep(old_render, new_render, 'category rail render')

    old_click = '''            int cy = bodyY + 23;
            for (String category : CATEGORIES) {
                if (leftClick && in(e.x(), e.y(), railX + 5, cy, railW - 10, 25)) {
                    selectedCategory = category;
                    selectedMod = firstInCategory(category);
                    mobPage = 0;
                    settingsScroll = 0;
                    modulesScroll = 0;
                    return true;
                }
                cy += 28;
            }
'''
    new_click = '''            int categoryTop = bodyY + 23;
            int categoryBottom = footerY - 9;
            int categoryViewport = Math.max(1, categoryBottom - categoryTop);
            int categoryMax = Math.max(0, CATEGORIES.length * 28 - categoryViewport);
            categoriesScroll = clampScroll(categoriesScroll, categoryMax);
            int cy = categoryTop - categoriesScroll;
            for (String category : CATEGORIES) {
                if (leftClick && cy >= categoryTop && cy + 25 <= categoryBottom
                        && in(e.x(), e.y(), railX + 5, cy, railW - 10, 25)) {
                    selectedCategory = category;
                    selectedMod = firstInCategory(category);
                    mobPage = 0;
                    settingsScroll = 0;
                    modulesScroll = 0;
                    return true;
                }
                cy += 28;
            }
'''
    rep(old_click, new_click, 'category rail click')

    scroll_anchor = '''            int moduleTop = bodyY + 23, moduleBottom = footerY - 9;
            if (in(mouseX, mouseY, modsX, bodyY, modsW, Math.max(1, footerY - 6 - bodyY))) {'''
    scroll_new = '''            int categoryTop = bodyY + 23, categoryBottom = footerY - 9;
            if (in(mouseX, mouseY, railX, bodyY, railW, Math.max(1, footerY - 6 - bodyY))) {
                int max = Math.max(0, CATEGORIES.length * 28 - Math.max(1, categoryBottom - categoryTop));
                categoriesScroll = clampScroll(categoriesScroll + (scrollY < 0.0 ? step : -step), max);
                return true;
            }

            int moduleTop = bodyY + 23, moduleBottom = footerY - 9;
            if (in(mouseX, mouseY, modsX, bodyY, modsW, Math.max(1, footerY - 6 - bodyY))) {'''
    rep(scroll_anchor, scroll_new, 'category wheel handler')

    rep('''            String hint = "ACTIVE = enabled modules  •  LMB select/toggle  •  RMB reset";''', '''            String hint = "WHEEL scrolls each panel  •  LMB open/toggle  •  RMB reset";''', 'modern footer hint')

    src.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.24.0+26.3' in g:
    g = g.replace('mod_version=0.24.0+26.3', 'mod_version=0.25.0+26.3', 1)
elif 'mod_version=0.25.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)

print('0.25 GUI patch applied')
