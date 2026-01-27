package com.racingai.f1telemetry.decoder;

import java.nio.ByteBuffer;

/**
 * Callback interface for receiving raw UDP packets.
 *
 * Implementations can process packets asynchronously as they arrive.
 */
public interface PacketListener {

    /**
     * Called when a UDP packet is received.
     *
     * @param data Raw packet data
     * @param length Length of the packet in bytes
     */
    void onPacketReceived(byte[] data, int length);

    /**
     * Called when an error occurs in the UDP receiver.
     *
     * @param error The exception that occurred
     */
    void onError(Exception error);
}
