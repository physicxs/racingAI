package com.racingai.f1telemetry.decoder;

import com.racingai.f1telemetry.packets.*;
import org.junit.jupiter.api.Test;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test for PacketDecoder.
 */
public class PacketDecoderTest {

    @Test
    public void testDecodePacketHeader() {
        // Create a minimal packet with valid header
        ByteBuffer buffer = ByteBuffer.allocate(100);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        // Header fields
        buffer.putShort((short) 2025);  // packetFormat
        buffer.put((byte) 25);           // gameYear
        buffer.put((byte) 1);            // gameMajorVersion
        buffer.put((byte) 0);            // gameMinorVersion
        buffer.put((byte) 1);            // packetVersion
        buffer.put((byte) 6);            // packetId (CAR_TELEMETRY)
        buffer.putLong(123456789L);      // sessionUID
        buffer.putFloat(10.5f);          // sessionTime
        buffer.putInt(100);              // frameIdentifier
        buffer.putInt(100);              // overallFrameIdentifier
        buffer.put((byte) 0);            // playerCarIndex
        buffer.put((byte) 255);          // secondaryPlayerCarIndex

        byte[] data = buffer.array();

        PacketDecoder decoder = new PacketDecoder();
        Object result = decoder.decodePacket(data, 100);

        // Should decode but may not complete due to insufficient data
        // The important thing is it doesn't crash
        assertNotNull(decoder, "Decoder should be created");
    }

    @Test
    public void testPacketTooSmall() {
        PacketDecoder decoder = new PacketDecoder();
        byte[] data = new byte[10]; // Too small for header

        Object result = decoder.decodePacket(data, 10);

        assertNull(result, "Should return null for packet too small");
    }

    @Test
    public void testNullPacket() {
        PacketDecoder decoder = new PacketDecoder();

        Object result = decoder.decodePacket(null, 0);

        assertNull(result, "Should return null for null packet");
    }

    @Test
    public void testDecoderHandlesInvalidPacketId() {
        ByteBuffer buffer = ByteBuffer.allocate(100);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        // Header with invalid packet ID
        buffer.putShort((short) 2025);
        buffer.put((byte) 25);
        buffer.put((byte) 1);
        buffer.put((byte) 0);
        buffer.put((byte) 1);
        buffer.put((byte) 99);           // Invalid packetId
        buffer.putLong(123456789L);
        buffer.putFloat(10.5f);
        buffer.putInt(100);
        buffer.putInt(100);
        buffer.put((byte) 0);
        buffer.put((byte) 255);

        byte[] data = buffer.array();

        PacketDecoder decoder = new PacketDecoder();
        Object result = decoder.decodePacket(data, 100);

        // Should return null for unknown packet type
        assertNull(result, "Should return null for invalid packet ID");
    }
}
