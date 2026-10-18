package com.eio.client;

/**
 * Small, Minecraft-independent state holder for server position correction telemetry.
 * It deliberately contains no packet mutation or anti-cheat specific behavior.
 */
final class CompatibilityState {
    private long correctionCount;
    private int pauseTicks;
    private int lastCorrectionId = -1;
    private long lastCorrectionEpochMillis;

    synchronized void onServerCorrection(int id, int requestedPauseTicks, long nowMillis) {
        correctionCount++;
        lastCorrectionId = id;
        lastCorrectionEpochMillis = nowMillis;
        pauseTicks = Math.max(pauseTicks, Math.max(0, requestedPauseTicks));
    }

    synchronized void tick() {
        if (pauseTicks > 0) pauseTicks--;
    }

    synchronized boolean paused() {
        return pauseTicks > 0;
    }

    synchronized int pauseTicks() {
        return pauseTicks;
    }

    synchronized long correctionCount() {
        return correctionCount;
    }

    synchronized int lastCorrectionId() {
        return lastCorrectionId;
    }

    synchronized long lastCorrectionEpochMillis() {
        return lastCorrectionEpochMillis;
    }

    synchronized void clearPause() {
        pauseTicks = 0;
    }
}
