from pathlib import Path

p = Path('eio26/EioClient.java')
s = p.read_text()

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, 1)

rep('public static final String VERSION = "0.18.0";', 'public static final String VERSION = "0.19.0";', 'version')
rep('public static final String BUILD_ID = "EIO-018-QA1";', 'public static final String BUILD_ID = "EIO-019-QA1";', 'build id')
rep('GUI=690x390', 'GUI=690x390 scrollable-glass', 'doctor gui label')

rep('''        private Mod selectedMod;
        private int mobPage;''', '''        private Mod selectedMod;
        private int mobPage;
        private int settingsScroll;
        private int modulesScroll;
        private static final int MOB_SELECTOR_HEIGHT = 130;''', 'scroll state')

rep('''        @Override public void added() { super.added(); guiOpen = true; if (selectedMod == null) selectedMod = firstInCategory(selectedCategory); }''', '''        @Override public void added() {
            super.added();
            guiOpen = true;
            if (selectedMod == null) selectedMod = firstInCategory(selectedCategory);
            settingsScroll = 0;
            modulesScroll = 0;
        }''', 'added reset')

# Make the shell genuinely translucent instead of nearly opaque.
rep('''            g.fill(0, 0, width, height, 0x18000000);
            g.fill(x + 5, y + 7, x + bw + 5, y + bh + 7, 0x30000000);
            g.fill(x, y, x + bw, y + bh, 0xE0090E14);
            g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x80131A22);
            g.fill(x, y, x + bw, y + 31, 0xEE0C131B);
            g.fill(x, y + 30, x + bw, y + 31, 0x66405260);''', '''            g.fill(0, 0, width, height, 0x06000000);
            g.fill(x + 5, y + 7, x + bw + 5, y + bh + 7, 0x18000000);
            g.fill(x, y, x + bw, y + bh, 0x72090E14);
            g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x24131A22);
            g.fill(x, y, x + bw, y + 31, 0x920C131B);
            g.fill(x, y + 30, x + bw, y + 31, 0x50405260);''', 'glass alpha')
rep('''            g.fill(railX, bodyY, railX + railW, footerY - 6, 0x5610171F);
            g.fill(modsX, bodyY, modsX + modsW, footerY - 6, 0x4210171F);
            g.fill(detailX, bodyY, detailX + detailW, footerY - 6, 0x5210171F);''', '''            g.fill(railX, bodyY, railX + railW, footerY - 6, 0x2E10171F);
            g.fill(modsX, bodyY, modsX + modsW, footerY - 6, 0x2410171F);
            g.fill(detailX, bodyY, detailX + detailW, footerY - 6, 0x2A10171F);''', 'panel alpha')
rep('''            g.fill(x + 10, footerY, x + bw - 10, y + bh - 7, 0x4210171F);''', '''            g.fill(x + 10, footerY, x + bw - 10, y + bh - 7, 0x2810171F);''', 'footer alpha')

# Replace module card rendering with a scrollable, clipped list.
old = '''            g.text(font, selectedCategory.toUpperCase(Locale.ROOT), modsX + 8, bodyY + 8, accent, true);
            int myCard = bodyY + 23;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                boolean selected = m == selectedMod;
                boolean hover = in(mx, my, modsX + 5, myCard, modsW - 10, 20);
                g.fill(modsX + 5, myCard, modsX + modsW - 5, myCard + 20,
                        selected ? 0x8D1D2A34 : (hover ? 0x5618232C : 0x2411161C));
                if (selected) g.fill(modsX + 5, myCard, modsX + 7, myCard + 20, accent);
                g.fill(modsX + 12, myCard + 8, modsX + 16, myCard + 12, m.enabled ? 0xFF6FE0A5 : 0xFF55636D);
                g.text(font, trim(m.name, Math.max(10, (modsW - 49) / 6)), modsX + 22, myCard + 6,
                        selected ? 0xFFF2F6F8 : 0xFFC2CCD3, false);
                String state = m.enabled ? "ON" : "";
                if (!state.isEmpty()) g.text(font, state, modsX + modsW - font.width(state) - 11, myCard + 6, 0xFF77DDA9, false);
                if (hover) help = m.description;
                myCard += 22;
            }'''
new = '''            g.text(font, selectedCategory.toUpperCase(Locale.ROOT), modsX + 8, bodyY + 8, accent, true);
            int moduleTop = bodyY + 23;
            int moduleBottom = footerY - 9;
            int moduleMax = Math.max(0, categoryCount(selectedCategory) * 22 - Math.max(1, moduleBottom - moduleTop));
            modulesScroll = clampScroll(modulesScroll, moduleMax);
            int myCard = moduleTop - modulesScroll;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                boolean visible = myCard + 20 > moduleTop && myCard < moduleBottom;
                if (visible) {
                    boolean selected = m == selectedMod;
                    boolean hover = in(mx, my, modsX + 5, Math.max(myCard, moduleTop), modsW - 10,
                            Math.max(0, Math.min(myCard + 20, moduleBottom) - Math.max(myCard, moduleTop)));
                    int drawTop = Math.max(myCard, moduleTop);
                    int drawBottom = Math.min(myCard + 20, moduleBottom);
                    if (drawBottom > drawTop) {
                        g.fill(modsX + 5, drawTop, modsX + modsW - 5, drawBottom,
                                selected ? 0x741D2A34 : (hover ? 0x4518232C : 0x1C11161C));
                        if (selected) g.fill(modsX + 5, drawTop, modsX + 7, drawBottom, accent);
                    }
                    if (myCard >= moduleTop && myCard + 20 <= moduleBottom) {
                        g.fill(modsX + 12, myCard + 8, modsX + 16, myCard + 12, m.enabled ? 0xFF6FE0A5 : 0xFF55636D);
                        g.text(font, trim(m.name, Math.max(10, (modsW - 49) / 6)), modsX + 22, myCard + 6,
                                selected ? 0xFFF2F6F8 : 0xFFC2CCD3, false);
                        String state = m.enabled ? "ON" : "";
                        if (!state.isEmpty()) g.text(font, state, modsX + modsW - font.width(state) - 11, myCard + 6, 0xFF77DDA9, false);
                        if (hover) help = m.description;
                    }
                }
                myCard += 22;
            }
            drawScrollBar(g, modsX + modsW - 3, moduleTop, Math.max(1, moduleBottom - moduleTop), modulesScroll, moduleMax, accent);'''
rep(old, new, 'module scrolling render')

# Replace settings loop with a scrollable viewport.
old = '''                g.text(font, "SETTINGS", sx, sy, 0xFF647581, false);
                sy += 12;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        help = renderMobSelector(g, mx, my, sx, sy, sw, Math.max(64, footerY - 9 - sy), ml, help, accent);
                        break;
                    }
                    boolean hover = in(mx, my, sx, sy, sw, 22);
                    g.fill(sx, sy, sx + sw, sy + 22, hover ? 0x571A252E : 0x2911161C);
                    if (setting instanceof BoolSetting b) {
                        g.text(font, trim(b.name, 18), sx + 7, sy + 7, 0xFFD4DCE2, false);
                        int tx = sx + sw - 34;
                        g.fill(tx, sy + 5, tx + 28, sy + 17, b.value ? 0xA9347459 : 0x60424A51);
                        int kx = b.value ? tx + 17 : tx + 3;
                        g.fill(kx, sy + 7, kx + 8, sy + 15, b.value ? 0xFFF1FFF7 : 0xFFB9C1C7);
                    } else if (setting instanceof NumSetting n) {
                        double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                        g.text(font, trim(n.name, 15), sx + 7, sy + 5, 0xFFD4DCE2, false);
                        String value = n.display() + (Math.abs(n.value - n.defaultValue) > 1.0E-9 ? "*" : "");
                        g.text(font, value, sx + sw - font.width(value) - 7, sy + 5, 0xFF9DDCFA, false);
                        g.fill(sx + 7, sy + 17, sx + sw - 7, sy + 19, 0x55505E68);
                        g.fill(sx + 7, sy + 17, sx + 7 + (int) ((sw - 14) * ratio), sy + 19, accent);
                    }
                    if (hover) help = setting.description;
                    sy += 24;
                }'''
new = '''                g.text(font, "SETTINGS", sx, sy, 0xFF647581, false);
                sy += 12;
                int settingsTop = sy;
                int settingsBottom = footerY - 9;
                int settingsViewport = Math.max(1, settingsBottom - settingsTop);
                int settingsMax = Math.max(0, settingsContentHeight(selectedMod) - settingsViewport);
                settingsScroll = clampScroll(settingsScroll, settingsMax);
                sy -= settingsScroll;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        help = renderMobSelector(g, mx, my, sx, sy, sw - 5, ml, help, accent, settingsTop, settingsBottom);
                        sy += MOB_SELECTOR_HEIGHT;
                        continue;
                    }
                    boolean visible = sy + 22 > settingsTop && sy < settingsBottom;
                    if (visible) {
                        int drawTop = Math.max(sy, settingsTop);
                        int drawBottom = Math.min(sy + 22, settingsBottom);
                        boolean fullyVisible = sy >= settingsTop && sy + 22 <= settingsBottom;
                        boolean hover = fullyVisible && in(mx, my, sx, sy, sw - 5, 22);
                        if (drawBottom > drawTop) g.fill(sx, drawTop, sx + sw - 5, drawBottom, hover ? 0x471A252E : 0x1E11161C);
                        if (fullyVisible && setting instanceof BoolSetting b) {
                            g.text(font, trim(b.name, 18), sx + 7, sy + 7, 0xFFD4DCE2, false);
                            int tx = sx + sw - 39;
                            g.fill(tx, sy + 5, tx + 28, sy + 17, b.value ? 0x93347459 : 0x50424A51);
                            int kx = b.value ? tx + 17 : tx + 3;
                            g.fill(kx, sy + 7, kx + 8, sy + 15, b.value ? 0xFFF1FFF7 : 0xFFB9C1C7);
                        } else if (fullyVisible && setting instanceof NumSetting n) {
                            double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);
                            g.text(font, trim(n.name, 15), sx + 7, sy + 5, 0xFFD4DCE2, false);
                            String value = n.display() + (Math.abs(n.value - n.defaultValue) > 1.0E-9 ? "*" : "");
                            g.text(font, value, sx + sw - font.width(value) - 12, sy + 5, 0xFF9DDCFA, false);
                            g.fill(sx + 7, sy + 17, sx + sw - 12, sy + 19, 0x45505E68);
                            g.fill(sx + 7, sy + 17, sx + 7 + (int) ((sw - 19) * ratio), sy + 19, accent);
                        }
                        if (hover) help = setting.description;
                    }
                    sy += 24;
                }
                drawScrollBar(g, sx + sw - 3, settingsTop, settingsViewport, settingsScroll, settingsMax, accent);'''
rep(old, new, 'settings scrolling render')

# Update mob selector renderer to clip to settings viewport.
rep('''        private String renderMobSelector(GuiGraphicsExtractor g, int mx, int my, int sx, int sy, int sw, int sh,
                                         MobListSetting ml, String help, int accent) {''', '''        private String renderMobSelector(GuiGraphicsExtractor g, int mx, int my, int sx, int sy, int sw,
                                         MobListSetting ml, String help, int accent, int clipTop, int clipBottom) {''', 'mob render signature')
rep('''            g.fill(sx, sy, sx + sw, sy + sh, 0x3A111820);
            g.fill(sx, sy, sx + sw, sy + 1, accent);
            g.text(font, "MOB FILTER", sx + 7, sy + 7, 0xFFE4EAF0, true);
            String count = ml.enabledCount() + "/" + ids.size();
            g.text(font, count, sx + sw - font.width(count) - 7, sy + 7, 0xFF82DDB0, false);''', '''            int boxTop = Math.max(sy, clipTop), boxBottom = Math.min(sy + MOB_SELECTOR_HEIGHT, clipBottom);
            if (boxBottom > boxTop) g.fill(sx, boxTop, sx + sw, boxBottom, 0x24111820);
            if (sy >= clipTop && sy + 18 <= clipBottom) {
                g.fill(sx, sy, sx + sw, sy + 1, accent);
                g.text(font, "MOB FILTER", sx + 7, sy + 7, 0xFFE4EAF0, true);
                String count = ml.enabledCount() + "/" + ids.size();
                g.text(font, count, sx + sw - font.width(count) - 7, sy + 7, 0xFF82DDB0, false);
            }''', 'mob header clip')
# Guard action controls.
rep('''            boolean allHover = in(mx, my, allX, actionY, 34, 15);
            boolean noneHover = in(mx, my, noneX, actionY, 42, 15);
            g.fill(allX, actionY, allX + 34, actionY + 15, allHover ? 0x72508365 : 0x49304E3E);
            g.fill(noneX, actionY, noneX + 42, actionY + 15, noneHover ? 0x72744949 : 0x494B3232);
            g.centeredText(font, "ALL", allX + 17, actionY + 5, 0xFFBFEBD4);
            g.centeredText(font, "NONE", noneX + 21, actionY + 5, 0xFFF0B8B8);
            if (allHover) help = "Allow every listed mob type";
            if (noneHover) help = "Block every listed mob type";''', '''            boolean actionsVisible = actionY >= clipTop && actionY + 15 <= clipBottom;
            boolean allHover = actionsVisible && in(mx, my, allX, actionY, 34, 15);
            boolean noneHover = actionsVisible && in(mx, my, noneX, actionY, 42, 15);
            if (actionsVisible) {
                g.fill(allX, actionY, allX + 34, actionY + 15, allHover ? 0x62508365 : 0x39304E3E);
                g.fill(noneX, actionY, noneX + 42, actionY + 15, noneHover ? 0x62744949 : 0x394B3232);
                g.centeredText(font, "ALL", allX + 17, actionY + 5, 0xFFBFEBD4);
                g.centeredText(font, "NONE", noneX + 21, actionY + 5, 0xFFF0B8B8);
                if (allHover) help = "Allow every listed mob type";
                if (noneHover) help = "Block every listed mob type";
            }''', 'mob actions clip')
rep('''            g.fill(pageX, actionY, pageX + 18, actionY + 15, 0x49303B44);
            g.fill(pageX + 53, actionY, pageX + 71, actionY + 15, 0x49303B44);
            g.centeredText(font, "<", pageX + 9, actionY + 5, 0xFFB8C7D1);
            g.centeredText(font, ">", pageX + 62, actionY + 5, 0xFFB8C7D1);
            g.centeredText(font, page, pageX + 35, actionY + 5, 0xFF71818D);''', '''            if (actionsVisible) {
                g.fill(pageX, actionY, pageX + 18, actionY + 15, 0x39303B44);
                g.fill(pageX + 53, actionY, pageX + 71, actionY + 15, 0x39303B44);
                g.centeredText(font, "<", pageX + 9, actionY + 5, 0xFFB8C7D1);
                g.centeredText(font, ">", pageX + 62, actionY + 5, 0xFFB8C7D1);
                g.centeredText(font, page, pageX + 35, actionY + 5, 0xFF71818D);
            }''', 'mob page clip')
rep('''                boolean on = ml.allows(id);
                boolean hover = in(mx, my, cx, cy, cellW, 18);
                g.fill(cx, cy, cx + cellW, cy + 18, on ? (hover ? 0x87507C64 : 0x5E315A47) : (hover ? 0x71603D3D : 0x47332228));
                g.fill(cx + 5, cy + 7, cx + 9, cy + 11, on ? 0xFF75DDA8 : 0xFF80595D);
                String label = MobListSetting.label(id);
                g.text(font, trim(label, Math.max(8, (cellW - 20) / 6)), cx + 14, cy + 5, on ? 0xFFE2ECE6 : 0xFFB6A5A8, false);
                if (hover) help = (on ? "Following allowed: " : "Following blocked: ") + label;''', '''                boolean on = ml.allows(id);
                boolean visible = cy >= clipTop && cy + 18 <= clipBottom;
                boolean hover = visible && in(mx, my, cx, cy, cellW, 18);
                if (visible) {
                    g.fill(cx, cy, cx + cellW, cy + 18, on ? (hover ? 0x77507C64 : 0x4E315A47) : (hover ? 0x61603D3D : 0x37332228));
                    g.fill(cx + 5, cy + 7, cx + 9, cy + 11, on ? 0xFF75DDA8 : 0xFF80595D);
                    String label = MobListSetting.label(id);
                    g.text(font, trim(label, Math.max(8, (cellW - 20) / 6)), cx + 14, cy + 5, on ? 0xFFE2ECE6 : 0xFFB6A5A8, false);
                    if (hover) help = (on ? "Following allowed: " : "Following blocked: ") + label;
                }''', 'mob cells clip')

# Reset both scroll positions when navigation changes.
rep('''                    selectedCategory = category;
                    selectedMod = firstInCategory(category);
                    mobPage = 0;''', '''                    selectedCategory = category;
                    selectedMod = firstInCategory(category);
                    mobPage = 0;
                    settingsScroll = 0;
                    modulesScroll = 0;''', 'category scroll reset')
rep('''                        if (selectedMod == m) toggle(m);
                        else { selectedMod = m; mobPage = 0; }''', '''                        if (selectedMod == m) toggle(m);
                        else { selectedMod = m; mobPage = 0; settingsScroll = 0; }''', 'module scroll reset')

# Scroll-aware module click coordinates.
rep('''            int myCard = bodyY + 23;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                if (in(e.x(), e.y(), modsX + 5, myCard, modsW - 10, 20)) {''', '''            int moduleTop = bodyY + 23;
            int moduleBottom = footerY - 9;
            int moduleMax = Math.max(0, categoryCount(selectedCategory) * 22 - Math.max(1, moduleBottom - moduleTop));
            modulesScroll = clampScroll(modulesScroll, moduleMax);
            int myCard = moduleTop - modulesScroll;
            for (Mod m : MODS) if (m.category.equals(selectedCategory)) {
                if (myCard >= moduleTop && myCard + 20 <= moduleBottom && in(e.x(), e.y(), modsX + 5, myCard, modsW - 10, 20)) {''', 'module click scroll')

# Scroll-aware settings click positions and clipping.
old = '''                sy += 42;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        if (handleMobSelectorClick(e, leftClick, rightClick, sx, sy, sw, ml)) return true;
                        break;
                    }
                    if (in(e.x(), e.y(), sx, sy, sw, 22)) {'''
new = '''                sy += 42;
                int settingsTop = sy;
                int settingsBottom = footerY - 9;
                int settingsMax = Math.max(0, settingsContentHeight(selectedMod) - Math.max(1, settingsBottom - settingsTop));
                settingsScroll = clampScroll(settingsScroll, settingsMax);
                sy -= settingsScroll;
                for (Setting setting : selectedMod.settings) {
                    if (setting instanceof MobListSetting ml) {
                        if (handleMobSelectorClick(e, leftClick, rightClick, sx, sy, sw - 5, ml, settingsTop, settingsBottom)) return true;
                        sy += MOB_SELECTOR_HEIGHT;
                        continue;
                    }
                    if (sy >= settingsTop && sy + 22 <= settingsBottom && in(e.x(), e.y(), sx, sy, sw - 5, 22)) {'''
rep(old, new, 'settings click scroll')

rep('''        private boolean handleMobSelectorClick(MouseButtonEvent e, boolean leftClick, boolean rightClick,
                                               int sx, int sy, int sw, MobListSetting ml) {''', '''        private boolean handleMobSelectorClick(MouseButtonEvent e, boolean leftClick, boolean rightClick,
                                               int sx, int sy, int sw, MobListSetting ml, int clipTop, int clipBottom) {''', 'mob click signature')
rep('''            if (leftClick && in(e.x(), e.y(), allX, actionY, 34, 15)) { ml.setAll(true); followTarget = null; save(); return true; }
            if (leftClick && in(e.x(), e.y(), noneX, actionY, 42, 15)) { ml.setAll(false); followTarget = null; save(); return true; }''', '''            boolean actionsVisible = actionY >= clipTop && actionY + 15 <= clipBottom;
            if (leftClick && actionsVisible && in(e.x(), e.y(), allX, actionY, 34, 15)) { ml.setAll(true); followTarget = null; save(); return true; }
            if (leftClick && actionsVisible && in(e.x(), e.y(), noneX, actionY, 42, 15)) { ml.setAll(false); followTarget = null; save(); return true; }''', 'mob click actions clip')
rep('''            if (leftClick && in(e.x(), e.y(), pageX, actionY, 18, 15)) { mobPage = (mobPage - 1 + pages) % pages; return true; }
            if (leftClick && in(e.x(), e.y(), pageX + 53, actionY, 18, 15)) { mobPage = (mobPage + 1) % pages; return true; }
            if (rightClick && in(e.x(), e.y(), sx, sy, sw, 18)) { ml.reset(); mobPage = 0; followTarget = null; save(); return true; }''', '''            if (leftClick && actionsVisible && in(e.x(), e.y(), pageX, actionY, 18, 15)) { mobPage = (mobPage - 1 + pages) % pages; return true; }
            if (leftClick && actionsVisible && in(e.x(), e.y(), pageX + 53, actionY, 18, 15)) { mobPage = (mobPage + 1) % pages; return true; }
            if (rightClick && sy >= clipTop && sy + 18 <= clipBottom && in(e.x(), e.y(), sx, sy, sw, 18)) { ml.reset(); mobPage = 0; followTarget = null; save(); return true; }''', 'mob click page clip')
rep('''                if (leftClick && in(e.x(), e.y(), cx, cy, cellW, 18)) {''', '''                if (leftClick && cy >= clipTop && cy + 18 <= clipBottom && in(e.x(), e.y(), cx, cy, cellW, 18)) {''', 'mob click cell clip')

# Add wheel handling and scroll helpers before branding renderer.
anchor = '''        static void drawRainbowBlockBrand(GuiGraphicsExtractor g, int x, int y, int scale) {'''
insert = '''        @Override
        public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
            int bw = panelW(), bh = panelH(), x = panelX(), y = panelY();
            int bodyY = y + 39;
            int footerY = y + bh - 25;
            int railX = x + 10, railW = 98;
            int modsX = railX + railW + 8, modsW = Math.min(198, Math.max(154, bw / 3 - 22));
            int detailX = modsX + modsW + 8;
            int detailW = x + bw - 10 - detailX;
            int step = Math.max(18, (int) Math.round(Math.abs(scrollY) * 28.0));
            if (scrollY == 0.0) return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);

            int moduleTop = bodyY + 23, moduleBottom = footerY - 9;
            if (in(mouseX, mouseY, modsX, bodyY, modsW, Math.max(1, footerY - 6 - bodyY))) {
                int max = Math.max(0, categoryCount(selectedCategory) * 22 - Math.max(1, moduleBottom - moduleTop));
                modulesScroll = clampScroll(modulesScroll + (scrollY < 0.0 ? step : -step), max);
                return true;
            }

            if (selectedMod != null && in(mouseX, mouseY, detailX, bodyY, detailW, Math.max(1, footerY - 6 - bodyY))) {
                int settingsTop = bodyY + 81;
                int settingsBottom = footerY - 9;
                int max = Math.max(0, settingsContentHeight(selectedMod) - Math.max(1, settingsBottom - settingsTop));
                settingsScroll = clampScroll(settingsScroll + (scrollY < 0.0 ? step : -step), max);
                return true;
            }
            return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
        }

        private int settingsContentHeight(Mod mod) {
            if (mod == null) return 0;
            int h = 0;
            for (Setting setting : mod.settings) h += setting instanceof MobListSetting ? MOB_SELECTOR_HEIGHT : 24;
            return h;
        }

        private static int clampScroll(int value, int max) {
            return Math.max(0, Math.min(Math.max(0, max), value));
        }

        private static void drawScrollBar(GuiGraphicsExtractor g, int x, int y, int height, int value, int max, int accent) {
            if (max <= 0 || height <= 8) return;
            g.fill(x, y, x + 2, y + height, 0x302D3943);
            int thumb = Math.max(18, (int) Math.round(height * (height / (double) (height + max))));
            int travel = Math.max(1, height - thumb);
            int top = y + (int) Math.round(travel * (value / (double) max));
            g.fill(x, top, x + 2, top + thumb, accent);
        }

''' + anchor
rep(anchor, insert, 'wheel helpers')

p.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.18.0+26.3' not in g:
    raise SystemExit('gradle version target missing')
gp.write_text(g.replace('mod_version=0.18.0+26.3', 'mod_version=0.19.0+26.3', 1))
