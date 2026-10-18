package com.eio.client;

import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

final class AreaRegionTest {
    @Test
    void normalizesCornersAndDepth() {
        AreaRegion r = AreaRegion.from(new BlockPos(12, 70, -3), new BlockPos(8, 68, 4), 6);
        assertNotNull(r);
        assertEquals(8, r.minX);
        assertEquals(12, r.maxX);
        assertEquals(-3, r.minZ);
        assertEquals(4, r.maxZ);
        assertEquals(70, r.surfaceY);
        assertEquals(69, r.topY);
        assertEquals(64, r.bottomY);
        assertEquals(5, r.width());
        assertEquals(8, r.length());
        assertEquals(6, r.depth());
    }

    @Test
    void containsOnlyConfiguredVolume() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 2), 5);
        assertTrue(r.contains(new BlockPos(1, 63, 1)));
        assertTrue(r.contains(new BlockPos(1, 59, 1)));
        assertFalse(r.contains(new BlockPos(1, 64, 1)), "surface marker Y itself must never be mined");
        assertFalse(r.contains(new BlockPos(3, 63, 1)));
        assertFalse(r.contains(new BlockPos(1, 58, 1)));
    }

    @Test
    void serpentineNavigationDoesNotLeaveBounds() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 1), 2);
        assertEquals(new BlockPos(0, 63, 0), r.navigationCell(0, 64));
        assertEquals(new BlockPos(1, 63, 0), r.navigationCell(1, 64));
        assertEquals(new BlockPos(2, 63, 0), r.navigationCell(2, 64));
        assertEquals(new BlockPos(2, 63, 1), r.navigationCell(3, 64));
        assertEquals(new BlockPos(1, 63, 1), r.navigationCell(4, 64));
        assertEquals(new BlockPos(0, 63, 1), r.navigationCell(5, 64));
    }

    @Test
    void rejectsOversizedNavigationArea() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(AreaRegion.MAX_SIDE, 64, 0), 1);
        assertNotNull(r);
        assertFalse(r.supportedSize());
        assertEquals(0, r.navigationCells());
    }

    @Test
    void excavatesFiveBlocksAtATimeStrictlyBelowSurface() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 70, 0), new BlockPos(3, 70, 3), 12);
        assertEquals(70, r.surfaceY);
        assertEquals(69, r.topY);
        assertEquals(58, r.bottomY);
        assertEquals(3, r.layerCount());
        assertEquals(69, r.layerTop(0));
        assertEquals(65, r.layerBottom(0));
        assertEquals(64, r.layerTop(1));
        assertEquals(60, r.layerBottom(1));
        assertEquals(59, r.layerTop(2));
        assertEquals(58, r.layerBottom(2));
        assertTrue(r.containsInLayer(new BlockPos(1, 65, 1), 0));
        assertFalse(r.containsInLayer(new BlockPos(1, 64, 1), 0));
        assertFalse(r.contains(new BlockPos(1, 70, 1)));
    }
}
