package com.eio.client;

/**
 * A deliberately tiny first-wins queue for actions that should occur at most once per client tick.
 * It contains no Minecraft or networking code, which makes the scheduling rule independently testable.
 */
final class SingleIntentQueue<T> {
    private T pending;

    synchronized boolean offer(T value) {
        if (value == null || pending != null) return false;
        pending = value;
        return true;
    }

    synchronized T poll() {
        T value = pending;
        pending = null;
        return value;
    }

    synchronized void clear() {
        pending = null;
    }

    synchronized boolean hasPending() {
        return pending != null;
    }
}
