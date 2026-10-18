package com.eio.client;

import net.minecraft.core.BlockPos;

/**
 * Immutable horizontal quarry bounds plus a top-down mining depth.
 * Kept separate from client input code so region math can be regression tested.
 */
final class AreaRegion {
    static final int MAX_SIDE = 128;

    final int minX;
    final int maxX;
    final int minZ;
    final int maxZ;
    final int surfaceY;
    final int topY;
    final int bottomY;

    private AreaRegion(int minX, int maxX, int minZ, int maxZ, int surfaceY, int topY, int bottomY) {
        this.minX = minX;
        this.maxX = maxX;
        this.minZ = minZ;
        this.maxZ = maxZ;
        this.surfaceY = surfaceY;
        this.topY = topY;
        this.bottomY = bottomY;
    }

    static AreaRegion from(BlockPos a, BlockPos b, int depth) {
        if (a == null || b == null) return null;
        int safeDepth = Math.max(5, Math.min(64, depth));
        int surface = Math.max(a.getY(), b.getY());
        int mineTop = surface - 1;
        return new AreaRegion(
                Math.min(a.getX(), b.getX()), Math.max(a.getX(), b.getX()),
                Math.min(a.getZ(), b.getZ()), Math.max(a.getZ(), b.getZ()),
                surface, mineTop, surface - safeDepth);
    }

    int width() { return maxX - minX + 1; }
    int length() { return maxZ - minZ + 1; }
    int depth() { return topY - bottomY + 1; }

    int layerCount() { return (depth() + 4) / 5; }

    int layerTop(int layer) {
        if (layer < 0 || layer >= layerCount()) throw new IllegalArgumentException("layer " + layer);
        return topY - layer * 5;
    }

    int layerBottom(int layer) {
        return Math.max(bottomY, layerTop(layer) - 4);
    }

    boolean containsInLayer(BlockPos pos, int layer) {
        return contains(pos) && layer >= 0 && layer < layerCount()
                && pos.getY() <= layerTop(layer) && pos.getY() >= layerBottom(layer);
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
                + " | surfaceY " + surfaceY + " | mineY " + topY + ".." + bottomY
                + " | " + width() + "x" + length() + "x" + depth();
    }
}
