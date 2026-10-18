from pathlib import Path
import json

src = Path('eio26/EioClient.java')
s = src.read_text()


def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit('patch target not found: ' + label)
    s = s.replace(old, new, count)

if 'public static final String VERSION = "0.26.0";' not in s:
    rep('public static final String VERSION = "0.25.0";', 'public static final String VERSION = "0.26.0";', 'version')
    rep('public static final String BUILD_ID = "EIO-025-GUI1";', 'public static final String BUILD_ID = "EIO-026-AREA1";', 'build id')

    rep('''    private static final Set<BlockPos> NUKER_SKIPPED = new HashSet<>();
    private static boolean attackForced;''', '''    private static final Set<BlockPos> NUKER_SKIPPED = new HashSet<>();
    private static BlockPos areaMineTarget;
    private static int areaMineRearmTicks;
    private static int areaMineAimTicks;
    private static int areaNavIndex;
    private static int areaMoveTicks;
    private static int areaMinedThisPass;
    private static boolean areaMoveRequested;
    private static boolean areaComplete;
    private static final Set<BlockPos> AREA_MINE_SKIPPED = new HashSet<>();
    private static boolean attackForced;''', 'area runtime fields')

    rep('''        mod("Tool Saver", "Mining", "Stops Eio mining automation before the held damageable tool reaches the configured remaining durability.", -1)''', '''        mod("Area Miner", "Mining", "Mines a user-defined rectangular area to a chosen depth and can move through the selected coordinates.", -1)
                .point("Corner A", "Stand at the first horizontal corner and left-click this row to set it here. Right-click clears it.")
                .point("Corner B", "Stand at the opposite horizontal corner and left-click this row to set it here. Right-click clears it.")
                .num("Depth", 8.0, 1.0, 64.0, 1.0, "Number of blocks to mine downward from the higher corner Y level.")
                .num("Retarget Delay", 1.0, 1.0, 4.0, 1.0, "Ticks to release attack before starting the next area target.")
                .num("Aim Timeout", 14.0, 4.0, 50.0, 1.0, "Ticks allowed to line up with a target before temporarily skipping it.")
                .num("Move Timeout", 100.0, 20.0, 240.0, 5.0, "Ticks allowed to reach one navigation cell before moving to the next cell.")
                .bool("Auto Move", true, "Move through the configured rectangle when no mineable block is currently in normal interaction range.")
                .bool("Sprint", false, "Sprint while Area Miner is navigating between cells.")
                .bool("Auto Jump", true, "Jump over simple one-block obstacles while Area Miner is moving.")
                .bool("Exposed Only", true, "Mine only blocks with an air-adjacent face, exposing deeper layers progressively.")
                .bool("Face Block", true, "Turn your view toward the current Area Miner target.");
        mod("Tool Saver", "Mining", "Stops Eio mining automation before the held damageable tool reaches the configured remaining durability.", -1)''', 'area module')

    rep('''                        .then(ClientCommands.literal("waypoint")''', '''                        .then(ClientCommands.literal("area")
                                .then(ClientCommands.literal("pos1").executes(c -> {
                                    Minecraft mc = Minecraft.getInstance();
                                    if (mc.player == null) return 0;
                                    Mod area = find("Area Miner");
                                    area.point("Corner A").set(mc.player.blockPosition());
                                    resetAreaRuntime(); save();
                                    c.getSource().sendFeedback(Component.literal("Area corner A set to " + area.point("Corner A").display()));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("pos2").executes(c -> {
                                    Minecraft mc = Minecraft.getInstance();
                                    if (mc.player == null) return 0;
                                    Mod area = find("Area Miner");
                                    area.point("Corner B").set(mc.player.blockPosition());
                                    resetAreaRuntime(); save();
                                    c.getSource().sendFeedback(Component.literal("Area corner B set to " + area.point("Corner B").display()));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("clear").executes(c -> {
                                    Mod area = find("Area Miner");
                                    area.point("Corner A").reset(); area.point("Corner B").reset();
                                    resetAreaRuntime(); save();
                                    c.getSource().sendFeedback(Component.literal("Area Miner corners cleared"));
                                    return 1;
                                }))
                                .then(ClientCommands.literal("status").executes(c -> {
                                    c.getSource().sendFeedback(Component.literal(areaStatus(find("Area Miner"))));
                                    return 1;
                                })))
                        .then(ClientCommands.literal("waypoint")''', 'area commands')

    rep('''                else if (setting instanceof MobListSetting ml) p.setProperty("mobfilter." + m.name + "." + setting.name, ml.disabledCsv());''', '''                else if (setting instanceof MobListSetting ml) p.setProperty("mobfilter." + m.name + "." + setting.name, ml.disabledCsv());
                else if (setting instanceof PointSetting point && point.value != null) p.setProperty("point." + m.name + "." + setting.name, point.csv());''', 'snapshot point')
    rep('p.setProperty("_schema", "4");', 'p.setProperty("_schema", "5");', 'schema')

    rep('''                else if (setting instanceof MobListSetting ml) ml.reset();
                if (setting instanceof MobListSetting ml) {
                    ml.loadDisabledCsv(p.getProperty("mobfilter." + m.name + "." + setting.name, ""));
                    continue;
                }
                String v = p.getProperty("setting." + m.name + "." + setting.name);''', '''                else if (setting instanceof MobListSetting ml) ml.reset();
                else if (setting instanceof PointSetting point) point.reset();
                if (setting instanceof MobListSetting ml) {
                    ml.loadDisabledCsv(p.getProperty("mobfilter." + m.name + "." + setting.name, ""));
                    continue;
                }
                if (setting instanceof PointSetting point) {
                    point.load(p.getProperty("point." + m.name + "." + setting.name));
                    continue;
                }
                String v = p.getProperty("setting." + m.name + "." + setting.name);''', 'apply point')

    rep('''            NUKER_SKIPPED.clear();
            clickAccumulator = 0.0;''', '''            NUKER_SKIPPED.clear();
            resetAreaRuntime();
            clickAccumulator = 0.0;''', 'worldless area cleanup', 1)

    rep('''        Mod chunkMiner = find("Chunk Miner");
        Mod nuker = find("Nuker");
        Mod bright = find("Fullbright");''', '''        Mod chunkMiner = find("Chunk Miner");
        Mod nuker = find("Nuker");
        Mod areaMiner = find("Area Miner");
        Mod bright = find("Fullbright");''', 'area module lookup')

    rep('''        boolean shouldForceForward = !correctionPause && walk.enabled;
        if (!correctionPause && follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;''', '''        areaMoveRequested = !correctionPause && areaMiner.enabled && areaMiner.bool("Auto Move").value
                && updateAreaNavigation(mc, areaMiner);
        boolean areaOwnsMovement = areaMiner.enabled && areaMiner.bool("Auto Move").value;
        boolean shouldForceForward = areaMoveRequested || (!areaOwnsMovement && !correctionPause && walk.enabled);
        if (!areaOwnsMovement && !correctionPause && follow.enabled) shouldForceForward |= runFollow(mc, follow);
        if (!areaOwnsMovement && !correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Auto Walk").value) shouldForceForward = true;''', 'area movement ownership')

    rep('''        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }''', '''        if (!correctionPause && tunnelMiner.enabled && tunnelMiner.bool("Sprint").value && mc.options.keyUp.isDown() && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }
        if (areaMoveRequested && areaMiner.bool("Sprint").value && !mc.player.horizontalCollision) {
            mc.player.setSprinting(true);
        }''', 'area sprint')

    rep('''        if (miningAllowed) {
            if (nuker.enabled) {''', '''        if (miningAllowed) {
            if (areaMiner.enabled) {
                if (!areaConfigured(areaMiner)) {
                    areaMineTarget = null;
                } else {
                    if (areaMineTarget != null && mc.level.getBlockState(areaMineTarget).isAir()) {
                        areaMinedThisPass++;
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                        areaMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                    } else if (areaMineTarget != null && !validAreaMineTarget(mc, areaMiner, areaMineTarget)) {
                        AREA_MINE_SKIPPED.add(areaMineTarget.immutable());
                        areaMineTarget = null;
                        areaMineAimTicks = 0;
                        areaMineRearmTicks = Math.max(1, (int) Math.round(areaMiner.num("Retarget Delay").value));
                    }
                    if (areaMineRearmTicks > 0) {
                        areaMineRearmTicks--;
                    } else {
                        if (areaMineTarget == null) {
                            areaMineTarget = findAreaMineTarget(mc, areaMiner);
                            areaMineAimTicks = 0;
                            if (areaMineTarget == null && !AREA_MINE_SKIPPED.isEmpty()) {
                                AREA_MINE_SKIPPED.clear();
                                areaMineTarget = findAreaMineTarget(mc, areaMiner);
                            }
                        }
                        if (areaMineTarget != null) {
                            if (areaMiner.bool("Face Block").value) faceBlock(mc.player, areaMineTarget);
                            boolean aimed = mc.hitResult instanceof BlockHitResult hit && hit.getBlockPos().equals(areaMineTarget);
                            if (aimed) {
                                shouldForceAttack = true;
                                areaMineAimTicks = 0;
                            } else if (++areaMineAimTicks >= Math.max(4, (int) Math.round(areaMiner.num("Aim Timeout").value))) {
                                AREA_MINE_SKIPPED.add(areaMineTarget.immutable());
                                areaMineTarget = null;
                                areaMineAimTicks = 0;
                                areaMineRearmTicks = 1;
                            }
                        }
                    }
                }
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                chunkMineTarget = null;
                chunkMineRearmTicks = 0;
                chunkMineAimTicks = 0;
            } else if (nuker.enabled) {''', 'area mining priority')

    rep('''            } else {
                nukerTarget = null;
                nukerRearmTicks = 0;''', '''            } else {
                resetAreaRuntime();
                nukerTarget = null;
                nukerRearmTicks = 0;''', 'area reset when other mining inactive', 1)

    rep('''        } else {
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
            nukerTarget = null;''', '''        } else {
            areaMineTarget = null;
            areaMineRearmTicks = 0;
            areaMineAimTicks = 0;
            areaMoveRequested = false;
            chunkMineTarget = null;
            chunkMineRearmTicks = 0;
            chunkMineAimTicks = 0;
            nukerTarget = null;''', 'area pause cleanup')

    rep('''        boolean shouldForceJump = !correctionPause && ((autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater()));''', '''        boolean shouldForceJump = !correctionPause && ((autoJump.enabled && mc.player.horizontalCollision && mc.player.onGround())
                || (autoSwim.enabled && mc.player.isInWater())
                || (areaMoveRequested && areaMiner.bool("Auto Jump").value && mc.player.horizontalCollision && mc.player.onGround()));''', 'area auto jump')

    helper_anchor = '''    private static boolean validChunkMineTarget(Minecraft mc, Mod chunk, BlockPos pos) {'''
    helpers = '''    private static AreaRegion areaRegion(Mod area) {
        if (area == null) return null;
        PointSetting a = area.point("Corner A"), b = area.point("Corner B");
        return AreaRegion.from(a.value, b.value, (int) Math.round(area.num("Depth").value));
    }

    private static boolean areaConfigured(Mod area) {
        AreaRegion region = areaRegion(area);
        return region != null && region.supportedSize();
    }

    private static String areaStatus(Mod area) {
        AreaRegion region = areaRegion(area);
        if (region == null) return "Area Miner: set Corner A and Corner B";
        if (!region.supportedSize()) return "Area Miner: maximum supported area is " + AreaRegion.MAX_SIDE + "x" + AreaRegion.MAX_SIDE;
        return "Area Miner: " + region.summary() + (areaComplete ? " | complete" : " | nav " + (areaNavIndex + 1) + "/" + region.navigationCells());
    }

    private static void resetAreaRuntime() {
        areaMineTarget = null;
        areaMineRearmTicks = 0;
        areaMineAimTicks = 0;
        areaNavIndex = 0;
        areaMoveTicks = 0;
        areaMinedThisPass = 0;
        areaMoveRequested = false;
        areaComplete = false;
        AREA_MINE_SKIPPED.clear();
    }

    private static boolean validAreaMineTarget(Minecraft mc, Mod area, BlockPos pos) {
        if (mc.player == null || mc.level == null || pos == null) return false;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize() || !region.contains(pos)) return false;
        if (!withinVanillaBlockRange(mc, pos)) return false;
        var state = mc.level.getBlockState(pos);
        if (state.isAir() || state.getDestroySpeed(mc.level, pos) < 0.0f) return false;
        return !area.bool("Exposed Only").value || isExposedBlock(mc, pos);
    }

    private static BlockPos findAreaMineTarget(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null) return null;
        AreaRegion region = areaRegion(area);
        if (region == null || !region.supportedSize()) return null;
        BlockPos origin = mc.player.blockPosition();
        int radius = 6;
        BlockPos best = null;
        double bestSq = Double.MAX_VALUE;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    if (AREA_MINE_SKIPPED.contains(pos) || !validAreaMineTarget(mc, area, pos)) continue;
                    double px = pos.getX() + 0.5 - mc.player.getX();
                    double py = pos.getY() + 0.5 - mc.player.getY();
                    double pz = pos.getZ() + 0.5 - mc.player.getZ();
                    double d = px * px + py * py + pz * pz;
                    if (d < bestSq) { bestSq = d; best = pos.immutable(); }
                }
            }
        }
        return best;
    }

    private static boolean updateAreaNavigation(Minecraft mc, Mod area) {
        if (mc.player == null || mc.level == null || !areaConfigured(area) || areaComplete) return false;
        if (areaMineTarget != null || areaMineRearmTicks > 0) { areaMoveTicks = 0; return false; }
        BlockPos reachable = findAreaMineTarget(mc, area);
        if (reachable != null) {
            areaMineTarget = reachable;
            areaMineAimTicks = 0;
            areaMoveTicks = 0;
            return false;
        }
        AreaRegion region = areaRegion(area);
        if (region == null) return false;

        double px = mc.player.getX(), pz = mc.player.getZ();
        boolean outside = px < region.minX + 0.15 || px > region.maxX + 0.85
                || pz < region.minZ + 0.15 || pz > region.maxZ + 0.85;
        double goalX, goalZ;
        if (outside) {
            goalX = region.clampX(px) + 0.5;
            goalZ = region.clampZ(pz) + 0.5;
        } else {
            int cells = region.navigationCells();
            if (cells <= 0) return false;
            if (areaNavIndex >= cells) {
                if (areaMinedThisPass <= 0) {
                    areaComplete = true;
                    area.enabled = false;
                    save();
                    notifyMessage("AREA MINER COMPLETE", 0xFF75DDA8, 3000L);
                    return false;
                }
                areaNavIndex = 0;
                areaMinedThisPass = 0;
                AREA_MINE_SKIPPED.clear();
            }
            BlockPos nav = region.navigationCell(areaNavIndex, mc.player.blockPosition().getY());
            if (nav == null) return false;
            goalX = nav.getX() + 0.5;
            goalZ = nav.getZ() + 0.5;
        }

        double dx = goalX - px, dz = goalZ - pz;
        double distance = Math.sqrt(dx * dx + dz * dz);
        if (!outside && distance < 0.72) {
            areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        if (++areaMoveTicks >= Math.max(20, (int) Math.round(area.num("Move Timeout").value))) {
            if (!outside) areaNavIndex++;
            areaMoveTicks = 0;
            return false;
        }
        faceHorizontal(mc.player, goalX, goalZ);
        return distance > 0.45;
    }

    private static void faceHorizontal(Player player, double x, double z) {
        double dx = x - player.getX();
        double dz = z - player.getZ();
        if (dx * dx + dz * dz > 1.0E-6) player.setYRot((float) (Math.toDegrees(Math.atan2(dz, dx)) - 90.0));
    }

''' + helper_anchor
    rep(helper_anchor, helpers, 'area helper functions')

    rep('''            if ((m.name.equals("AutoWalk") || m.name.equals("Follow") || m.name.equals("Tunnel Miner"))
                    && !find("AutoWalk").enabled && !find("Follow").enabled
                    && !find("Tunnel Miner").enabled && forwardForced) {''', '''            if ((m.name.equals("AutoWalk") || m.name.equals("Follow") || m.name.equals("Tunnel Miner") || m.name.equals("Area Miner"))
                    && !find("AutoWalk").enabled && !find("Follow").enabled
                    && !find("Tunnel Miner").enabled && !find("Area Miner").enabled && forwardForced) {''', 'area forward toggle cleanup')
    rep('''            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner") || m.name.equals("Nuker"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && !find("Nuker").enabled && attackForced) {''', '''            if ((m.name.equals("Auto Mine") || m.name.equals("Tunnel Miner") || m.name.equals("Chunk Miner") || m.name.equals("Nuker") || m.name.equals("Area Miner"))
                    && !find("Auto Mine").enabled && !find("Tunnel Miner").enabled && !find("Chunk Miner").enabled && !find("Nuker").enabled
                    && !find("Area Miner").enabled && attackForced) {''', 'area attack toggle cleanup')
    rep('''            if (m.name.equals("Nuker")) {
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                NUKER_SKIPPED.clear();
            }''', '''            if (m.name.equals("Nuker")) {
                nukerTarget = null;
                nukerRearmTicks = 0;
                nukerAimTicks = 0;
                NUKER_SKIPPED.clear();
            }
            if (m.name.equals("Area Miner")) resetAreaRuntime();''', 'area module toggle cleanup')

    rep('''        NUKER_SKIPPED.clear();
        clickAccumulator = 0.0;''', '''        NUKER_SKIPPED.clear();
        resetAreaRuntime();
        clickAccumulator = 0.0;''', 'correction area cleanup', 1)
    rep('''        NUKER_SKIPPED.clear();
        clickAccumulator = 0.0;''', '''        NUKER_SKIPPED.clear();
        resetAreaRuntime();
        clickAccumulator = 0.0;''', 'runtime area cleanup', 1)

    rep('''            else if (setting instanceof MobListSetting ml) ml.reset();''', '''            else if (setting instanceof MobListSetting ml) ml.reset();
            else if (setting instanceof PointSetting point) point.reset();''', 'module point reset')

    rep('''            if (miningHud.bool("Target").value) {
                BlockPos miningPos = chunkMineTarget;
                if (miningPos == null && mc.hitResult instanceof BlockHitResult hit) miningPos = hit.getBlockPos();''', '''            if (miningHud.bool("Target").value) {
                BlockPos miningPos = areaMineTarget != null ? areaMineTarget : (nukerTarget != null ? nukerTarget : chunkMineTarget);
                if (miningPos == null && mc.hitResult instanceof BlockHitResult hit) miningPos = hit.getBlockPos();''', 'mining hud target priority')
    rep('''            if (miningHud.bool("Tool").value) {''', '''            if (find("Area Miner").enabled || areaComplete) {
                g.text(mc.font, trim(areaStatus(find("Area Miner")), 70), 5, y, 0xFF8FDCC0, true);
                y += 11;
            }
            if (miningHud.bool("Tool").value) {''', 'area hud status')

    rep('''    private static final class MobListSetting extends Setting {''', '''    private static final class PointSetting extends Setting {
        BlockPos value;
        PointSetting(String name, String description) { super(name, description); }
        void set(BlockPos pos) { value = pos == null ? null : pos.immutable(); }
        void reset() { value = null; }
        String csv() { return value == null ? "" : value.getX() + "," + value.getY() + "," + value.getZ(); }
        void load(String raw) {
            reset();
            if (raw == null || raw.isBlank()) return;
            try {
                String[] p = raw.split(",");
                if (p.length == 3) value = new BlockPos(Integer.parseInt(p[0].trim()), Integer.parseInt(p[1].trim()), Integer.parseInt(p[2].trim()));
            } catch (Exception ignored) {}
        }
        String display() { return value == null ? "SET HERE" : value.getX() + " " + value.getY() + " " + value.getZ(); }
    }

    private static final class MobListSetting extends Setting {''', 'point setting class')

    rep('''        Mod mobList(String name, String[] ids, String description) { settings.add(new MobListSetting(name, ids, description)); return this; }
        BoolSetting bool(String name)''', '''        Mod mobList(String name, String[] ids, String description) { settings.add(new MobListSetting(name, ids, description)); return this; }
        Mod point(String name, String description) { settings.add(new PointSetting(name, description)); return this; }
        BoolSetting bool(String name)''', 'point builder')
    rep('''        MobListSetting mobList(String name) { for (Setting s : settings) if (s instanceof MobListSetting ml && ml.name.equals(name)) return ml; throw new IllegalArgumentException(name); }''', '''        MobListSetting mobList(String name) { for (Setting s : settings) if (s instanceof MobListSetting ml && ml.name.equals(name)) return ml; throw new IllegalArgumentException(name); }
        PointSetting point(String name) { for (Setting s : settings) if (s instanceof PointSetting point && point.name.equals(name)) return point; throw new IllegalArgumentException(name); }''', 'point accessor')

    rep('''        private int panelW() { return Math.max(430, Math.min(720, width - 18)); }
        private int panelH() { return Math.max(270, Math.min(410, height - 18)); }''', '''        private int panelW() { return Math.max(450, Math.min(760, width - 16)); }
        private int panelH() { return Math.max(280, Math.min(430, height - 16)); }''', 'modern panel dimensions')
    s = s.replace('int railX = x + 10, railW = 108;', 'int railX = x + 10, railW = 122;')
    s = s.replace('modsW = Math.min(198, Math.max(154, bw / 3 - 22))', 'modsW = Math.min(210, Math.max(160, bw / 3 - 22))')
    rep('''            g.fill(x, y, x + bw, y + bh, 0x56090E14);
            g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x18131A22);''', '''            g.fill(x, y, x + bw, y + bh, 0x4A090E14);
            g.fill(x + 1, y + 1, x + bw - 1, y + bh - 1, 0x12131A22);
            g.fill(x + 2, y + 2, x + bw - 2, y + 3, 0x26384A58);''', 'modern glass shell')
    rep('''            g.text(font, "CATEGORIES", railX + 8, bodyY + 8, 0xFF738592, false);''', '''            g.text(font, "NAVIGATION", railX + 8, bodyY + 8, 0xFF738592, false);''', 'navigation label')

    rep('''                        } else if (fullyVisible && setting instanceof NumSetting n) {
                            double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);''', '''                        } else if (fullyVisible && setting instanceof PointSetting point) {
                            g.text(font, trim(point.name, 13), sx + 7, sy + 7, 0xFFD4DCE2, false);
                            String value = point.display();
                            int buttonW = point.value == null ? 58 : Math.min(116, font.width(value) + 12);
                            int bx = sx + sw - buttonW - 10;
                            g.fill(bx, sy + 4, sx + sw - 10, sy + 18, hover ? 0x6A31566B : 0x46304758);
                            g.centeredText(font, trim(value, 18), bx + buttonW / 2, sy + 7, point.value == null ? 0xFF9EDCFA : 0xFFB9E8D1);
                        } else if (fullyVisible && setting instanceof NumSetting n) {
                            double ratio = (n.value - n.min) / Math.max(0.0001, n.max - n.min);''', 'point render')
    rep('''            String hint = "WHEEL scrolls each panel  •  LMB open/toggle  •  RMB reset";''', '''            String hint = "WHEEL panel scroll  •  LMB select/set  •  RMB reset/clear";''', 'modern footer hint')

    rep('''                        if (rightClick) {
                            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                        } else if (leftClick) {
                            if (setting instanceof BoolSetting b) b.value = !b.value;
                            else if (setting instanceof NumSetting n) {''', '''                        if (rightClick) {
                            if (setting instanceof BoolSetting b) b.value = b.defaultValue;
                            else if (setting instanceof NumSetting n) n.set(n.defaultValue);
                            else if (setting instanceof PointSetting point) { point.reset(); resetAreaRuntime(); }
                        } else if (leftClick) {
                            if (setting instanceof BoolSetting b) b.value = !b.value;
                            else if (setting instanceof PointSetting point) {
                                Minecraft mc = Minecraft.getInstance();
                                if (mc.player != null) { point.set(mc.player.blockPosition()); resetAreaRuntime(); }
                            }
                            else if (setting instanceof NumSetting n) {''', 'point click handling')

    rep('''                                    + " bound=" + bound + " | GUI=720x410 modern-scroll-glass | config=" + configSource''', '''                                    + " bound=" + bound + " | GUI=760x430 modern-nav-glass | config=" + configSource''', 'doctor gui string')

src.write_text(s)

gp = Path('gradle.properties')
g = gp.read_text()
if 'mod_version=0.25.0+26.3' in g:
    g = g.replace('mod_version=0.25.0+26.3', 'mod_version=0.26.0+26.3', 1)
elif 'mod_version=0.26.0+26.3' not in g:
    raise SystemExit('unexpected gradle version')
gp.write_text(g)

lang_path = Path('src/main/resources/assets/eioclient/lang/en_us.json')
lang = json.loads(lang_path.read_text())
lang['key.eioclient.area_miner'] = 'Area Miner'
lang_path.write_text(json.dumps(lang, indent=2) + '\n')
