package com.eio.client;

import net.minecraft.core.BlockPos;

/** Immutable horizontal quarry bounds plus staged top-down mining depth. */
final class AreaRegion {
    static final int MAX_SIDE = 128;
    static final int STAGE_DEPTH = 5;

    final int minX;
    final int maxX;
    final int minZ;
    final int maxZ;
    final int topY;
    final int bottomY;

    private AreaRegion(int minX, int maxX, int minZ, int maxZ, int topY, int bottomY) {
        this.minX = minX;
        this.maxX = maxX;
        this.minZ = minZ;
        this.maxZ = maxZ;
        this.topY = topY;
        this.bottomY = bottomY;
    }

    static AreaRegion from(BlockPos a, BlockPos b, int depth) {
        if (a == null || b == null) return null;
        int safeDepth = Math.max(1, Math.min(64, depth));
        int top = Math.max(a.getY(), b.getY());
        return new AreaRegion(
                Math.min(a.getX(), b.getX()), Math.max(a.getX(), b.getX()),
                Math.min(a.getZ(), b.getZ()), Math.max(a.getZ(), b.getZ()),
                top, top - safeDepth + 1);
    }

    int width() { return maxX - minX + 1; }
    int length() { return maxZ - minZ + 1; }
    int depth() { return topY - bottomY + 1; }
    int stageCount() { return (depth() + STAGE_DEPTH - 1) / STAGE_DEPTH; }

    int stageTopY(int stage) {
        int safe = Math.max(0, Math.min(stageCount() - 1, stage));
        return topY - safe * STAGE_DEPTH;
    }

    int stageBottomY(int stage) {
        return Math.max(bottomY, stageTopY(stage) - STAGE_DEPTH + 1);
    }

    int stageLayerCount(int stage) {
        return stageTopY(stage) - stageBottomY(stage) + 1;
    }

    int stageLayerY(int stage, int layer) {
        int count = stageLayerCount(stage);
        int safeLayer = Math.max(0, Math.min(Math.max(0, count - 1), layer));
        return stageTopY(stage) - safeLayer;
    }

    boolean supportedSize() {
        return width() > 0 && length() > 0 && width() <= MAX_SIDE && length() <= MAX_SIDE;
    }

    int navigationCells() {
        if (!supportedSize()) return 0;
        return width() * length();
    }

    boolean contains(BlockPos pos) {
        return pos != null
                && pos.getX() >= minX && pos.getX() <= maxX
                && pos.getZ() >= minZ && pos.getZ() <= maxZ
                && pos.getY() >= bottomY && pos.getY() <= topY;
    }

    boolean containsStage(BlockPos pos, int stage) {
        return contains(pos) && stage >= 0 && stage < stageCount()
                && pos.getY() <= stageTopY(stage) && pos.getY() >= stageBottomY(stage);
    }

    boolean containsPlane(BlockPos pos, int stage, int layer) {
        return containsStage(pos, stage) && pos.getY() == stageLayerY(stage, layer);
    }

    int clampX(double x) { return Math.max(minX, Math.min(maxX, (int) Math.floor(x))); }
    int clampZ(double z) { return Math.max(minZ, Math.min(maxZ, (int) Math.floor(z))); }

    BlockPos navigationCell(int index, int y) {
        int cells = navigationCells();
        if (cells <= 0) return null;
        int normalized = Math.floorMod(index, cells);
        int row = normalized / width();
        int col = normalized % width();
        if ((row & 1) != 0) col = width() - 1 - col;
        int navY = Math.max(bottomY, Math.min(topY, y));
        return new BlockPos(minX + col, navY, minZ + row);
    }

    String summary() {
        return minX + "," + minZ + " -> " + maxX + "," + maxZ
                + " | Y " + topY + ".." + bottomY + " | " + width() + "x" + length() + "x" + depth();
    }
}
