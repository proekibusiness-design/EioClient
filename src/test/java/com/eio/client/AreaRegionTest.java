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
        assertEquals(70, r.topY);
        assertEquals(65, r.bottomY);
        assertEquals(5, r.width());
        assertEquals(8, r.length());
        assertEquals(6, r.depth());
    }

    @Test
    void containsOnlyConfiguredVolume() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 2), 3);
        assertTrue(r.contains(new BlockPos(1, 63, 1)));
        assertFalse(r.contains(new BlockPos(3, 63, 1)));
        assertFalse(r.contains(new BlockPos(1, 60, 1)));
    }

    @Test
    void splitsDepthIntoFiveBlockTopDownLayers() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 70, 0), new BlockPos(2, 70, 2), 13);
        assertNotNull(r);
        assertEquals(3, r.layerCount());
        assertEquals(70, r.layerTopY(0));
        assertEquals(66, r.layerBottomY(0));
        assertEquals(65, r.layerTopY(1));
        assertEquals(61, r.layerBottomY(1));
        assertEquals(60, r.layerTopY(2));
        assertEquals(58, r.layerBottomY(2));
    }

    @Test
    void exactFiveBlockDepthUsesOneLayer() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(1, 64, 1), 5);
        assertNotNull(r);
        assertEquals(1, r.layerCount());
        assertEquals(64, r.layerTopY(0));
        assertEquals(60, r.layerBottomY(0));
    }

    @Test
    void partialFinalLayerDoesNotExceedRequestedDepth() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(1, 64, 1), 6);
        assertNotNull(r);
        assertEquals(2, r.layerCount());
        assertEquals(64, r.layerTopY(0));
        assertEquals(60, r.layerBottomY(0));
        assertEquals(59, r.layerTopY(1));
        assertEquals(59, r.layerBottomY(1));
        assertFalse(r.hasLayer(2));
    }

    @Test
    void serpentineNavigationDoesNotLeaveBounds() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(2, 64, 1), 2);
        assertEquals(new BlockPos(0, 64, 0), r.navigationCell(0, 64));
        assertEquals(new BlockPos(1, 64, 0), r.navigationCell(1, 64));
        assertEquals(new BlockPos(2, 64, 0), r.navigationCell(2, 64));
        assertEquals(new BlockPos(2, 64, 1), r.navigationCell(3, 64));
        assertEquals(new BlockPos(1, 64, 1), r.navigationCell(4, 64));
        assertEquals(new BlockPos(0, 64, 1), r.navigationCell(5, 64));
    }

    @Test
    void serpentinePathMovesOneCellAtATimeAndReversesEachLane() {
        AreaRegion r = AreaRegion.from(new BlockPos(-2, 70, 5), new BlockPos(1, 70, 7), 4);
        BlockPos previous = r.navigationCell(0, 70);
        assertNotNull(previous);
        for (int i = 1; i < r.navigationCells(); i++) {
            BlockPos next = r.navigationCell(i, 70);
            int manhattan = Math.abs(next.getX() - previous.getX()) + Math.abs(next.getZ() - previous.getZ());
            assertEquals(1, manhattan, "serpentine path must not jump between lane cells");
            previous = next;
        }
        assertEquals(new BlockPos(1, 70, 5), r.navigationCell(3, 70));
        assertEquals(new BlockPos(1, 70, 6), r.navigationCell(4, 70));
        assertEquals(new BlockPos(0, 70, 6), r.navigationCell(5, 70));
    }

    @Test
    void rejectsOversizedNavigationArea() {
        AreaRegion r = AreaRegion.from(new BlockPos(0, 64, 0), new BlockPos(AreaRegion.MAX_SIDE, 64, 0), 1);
        assertNotNull(r);
        assertFalse(r.supportedSize());
        assertEquals(0, r.navigationCells());
    }
}
