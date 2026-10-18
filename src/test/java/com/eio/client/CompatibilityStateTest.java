package com.eio.client;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

final class CompatibilityStateTest {
    @Test
    void correctionStartsPauseAndRecordsMetadata() {
        CompatibilityState state = new CompatibilityState();
        state.onServerCorrection(17, 4, 1_000L);

        assertTrue(state.paused());
        assertEquals(4, state.pauseTicks());
        assertEquals(1L, state.correctionCount());
        assertEquals(17, state.lastCorrectionId());
        assertEquals(1_000L, state.lastCorrectionEpochMillis());
    }

    @Test
    void pauseCountsDownDeterministically() {
        CompatibilityState state = new CompatibilityState();
        state.onServerCorrection(1, 2, 1L);

        state.tick();
        assertTrue(state.paused());
        assertEquals(1, state.pauseTicks());
        state.tick();
        assertFalse(state.paused());
        assertEquals(0, state.pauseTicks());
    }

    @Test
    void repeatedCorrectionExtendsButNeverShortensPause() {
        CompatibilityState state = new CompatibilityState();
        state.onServerCorrection(1, 6, 1L);
        state.tick();
        state.onServerCorrection(2, 2, 2L);

        assertEquals(5, state.pauseTicks());
        assertEquals(2L, state.correctionCount());
        assertEquals(2, state.lastCorrectionId());
    }

    @Test
    void clearPausePreservesTelemetry() {
        CompatibilityState state = new CompatibilityState();
        state.onServerCorrection(9, 5, 123L);
        state.clearPause();

        assertFalse(state.paused());
        assertEquals(1L, state.correctionCount());
        assertEquals(9, state.lastCorrectionId());
    }
}
