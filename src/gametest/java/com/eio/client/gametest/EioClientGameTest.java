package com.eio.client.gametest;

import com.eio.client.EioClient;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

@SuppressWarnings("UnstableApiUsage")
public final class EioClientGameTest implements FabricClientGameTest {
    @Override
    public void runTest(ClientGameTestContext context) {
        if (!"0.24.0".equals(EioClient.VERSION)) {
            throw new AssertionError("Unexpected Eio version: " + EioClient.VERSION);
        }

        try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
            context.waitFor(mc -> mc.player != null && mc.level != null && mc.isLocalServer());

            context.runOnClient(mc -> {
                if (mc.player == null || mc.level == null) {
                    throw new AssertionError("Integrated world did not provide client player/level");
                }
                if (!mc.isLocalServer()) {
                    throw new AssertionError("Expected integrated server during single-player GameTest");
                }

                // Exercise the server-authority recovery path without fabricating or mutating a network packet.
                EioClient.onServerPositionCorrection(4242);
            });

            // Default Compatibility Guard pause is four ticks. Waiting longer verifies the normal tick loop
            // survives the correction-recovery path and returns control to normal gameplay.
            context.waitTicks(6);
        }
    }
}
