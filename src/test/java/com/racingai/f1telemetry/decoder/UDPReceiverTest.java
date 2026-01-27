package com.racingai.f1telemetry.decoder;

import org.junit.jupiter.api.Test;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test for UDPReceiver.
 */
public class UDPReceiverTest {

    @Test
    public void testUDPReceiverStartsAndStops() throws IOException, InterruptedException {
        // Create receiver on port 20777
        UDPReceiver receiver = new UDPReceiver(20777);

        assertFalse(receiver.isRunning(), "Receiver should not be running initially");

        // Start receiver
        receiver.start();
        Thread.sleep(100); // Give it time to start

        assertTrue(receiver.isRunning(), "Receiver should be running after start");
        assertEquals(20777, receiver.getPort(), "Port should match");

        // Stop receiver
        receiver.stop();
        Thread.sleep(100); // Give it time to stop

        assertFalse(receiver.isRunning(), "Receiver should not be running after stop");
    }

    @Test
    public void testListenerRegistration() throws IOException {
        UDPReceiver receiver = new UDPReceiver(20778);

        final boolean[] packetReceived = {false};
        final boolean[] errorReceived = {false};

        PacketListener listener = new PacketListener() {
            @Override
            public void onPacketReceived(byte[] data, int length) {
                packetReceived[0] = true;
            }

            @Override
            public void onError(Exception error) {
                errorReceived[0] = true;
            }
        };

        receiver.addListener(listener);
        receiver.start();

        // Receiver should start successfully
        assertTrue(receiver.isRunning(), "Receiver should be running");

        receiver.stop();
    }
}
