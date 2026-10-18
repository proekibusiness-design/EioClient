package com.eio.client;

import net.minecraft.core.BlockPos;

/** Immutable quarry bounds, Corner-A-oriented serpentine navigation and top-down stage math. */
final class AreaRegion {
    static final int MAX_SIDE = 128;

    final int minX;
    final int maxX;
    final int minZ;
    final int maxZ;
    final int topY;
    final int bottomY;
    final int startX;
    final int startZ;
    final int xStep;
    final int zStep;

    private AreaRegion(int minX, int maxX, int minZ, int maxZ, int topY, int bottomY,
                       int startX, int startZ, int xStep, int zStep) {
        this.minX = minX;
        this.maxX = maxX;
        this.minZ = minZ;
        this.maxZ = maxZ;
        this.topY = topY;
        this.bottomY = bottomY;
        this.startX = startX;
        this.startZ = startZ;
        this.xStep = xStep;
        this.zStep = zStep;
    }

    static AreaRegion from(BlockPos a, BlockPos b, int depth) {
        if (a == null || b == null) return null;
        int safeDepth = Math.max(1, Math.min(64, depth));
        int top = Math.max(a.getY(), b.getY());
        int xs = Integer.compare(b.getX(), a.getX());
        int zs = Integer.compare(b.getZ(), a.getZ());
        if (xs == 0) xs = 1;
        if (zs == 0) zs = 1;
        return new AreaRegion(
                Math.min(a.getX(), b.getX()), Math.max(a.getX(), b.getX()),
                Math.min(a.getZ(), b.getZ()), Math.max(a.getZ(), b.getZ()),
                top, top - safeDepth + 1,
                a.getX(), a.getZ(), xs, zs);
    }

    int width() { return maxX - minX + 1; }
    int length() { return maxZ - minZ + 1; }
    int depth() { return topY - bottomY + 1; }

    boolean supportedSize() {
        return width() > 0 && length() > 0 && width() <= MAX_SIDE && length() <= MAX_SIDE;
    }

    int navigationCells() {
        if (!supportedSize()) return 0;
        return width() * length();
    }

    int stageCount(int stageHeight) {
        int h = Math.max(1, stageHeight);
        return (depth() + h - 1) / h;
    }

    int stageTopY(int stage, int stageHeight) {
        int h = Math.max(1, stageHeight);
        int count = stageCount(h);
        int s = Math.max(0, Math.min(Math.max(0, count - 1), stage));
        return topY - s * h;
    }

    int stageBottomY(int stage, int stageHeight) {
        int h = Math.max(1, stageHeight);
        return Math.max(bottomY, stageTopY(stage, h) - h + 1);
    }

    boolean contains(BlockPos pos) {
        return pos != null
                && pos.getX() >= minX && pos.getX() <= maxX
                && pos.getZ() >= minZ && pos.getZ() <= maxZ
                && pos.getY() >= bottomY && pos.getY() <= topY;
    }

    int clampX(double x) { return Math.max(minX, Math.min(maxX, (int) Math.floor(x))); }
    int clampZ(double z) { return Math.max(minZ, Math.min(maxZ, (int) Math.floor(z))); }

    BlockPos navigationCell(int index, int y) {
        int cells = navigationCells();
        if (cells <= 0 || index < 0 || index >= cells) return null;
        int row = index / width();
        int column = index % width();
        int along = (row & 1) == 0 ? column : width() - 1 - column;
        int x = startX + along * xStep;
        int z = startZ + row * zStep;
        int navY = Math.max(bottomY, Math.min(topY, y));
        if (x < minX || x > maxX || z < minZ || z > maxZ) return null;
        return new BlockPos(x, navY, z);
    }

    boolean isRowEnd(int index) {
        int cells = navigationCells();
        return cells > 0 && index >= 0 && index < cells && ((index + 1) % width()) == 0;
    }

    String summary() {
        return minX + "," + minZ + " -> " + maxX + "," + maxZ
                + " | Y " + topY + ".." + bottomY + " | " + width() + "x" + length() + "x" + depth();
    }
}
