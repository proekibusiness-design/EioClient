package com.eio.client;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

final class SingleIntentQueueTest {
    @Test
    void firstIntentWinsUntilFlushed() {
        SingleIntentQueue<String> queue = new SingleIntentQueue<>();
        assertTrue(queue.offer("first"));
        assertFalse(queue.offer("second"));
        assertEquals("first", queue.poll());
        assertFalse(queue.hasPending());
    }

    @Test
    void pollAllowsNextTickIntent() {
        SingleIntentQueue<Integer> queue = new SingleIntentQueue<>();
        assertTrue(queue.offer(1));
        assertEquals(1, queue.poll());
        assertTrue(queue.offer(2));
        assertEquals(2, queue.poll());
    }

    @Test
    void clearDropsStaleIntent() {
        SingleIntentQueue<Object> queue = new SingleIntentQueue<>();
        Object value = new Object();
        assertTrue(queue.offer(value));
        queue.clear();
        assertNull(queue.poll());
        assertFalse(queue.hasPending());
    }

    @Test
    void nullIsNeverQueued() {
        SingleIntentQueue<Object> queue = new SingleIntentQueue<>();
        assertFalse(queue.offer(null));
        assertNull(queue.poll());
    }
}
