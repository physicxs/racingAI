package com.racingai.f1telemetry.utils;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * Utility class for reading F1 2025 binary packet data.
 *
 * Handles unsigned integer types and provides helper methods for common patterns.
 * Supports both little-endian and big-endian byte orders.
 */
public class ByteBufferReader {

    private final ByteBuffer buffer;

    public ByteBufferReader(byte[] data) {
        this.buffer = ByteBuffer.wrap(data);
        this.buffer.order(ByteOrder.LITTLE_ENDIAN); // F1 uses little-endian
    }

    public ByteBufferReader(byte[] data, ByteOrder order) {
        this.buffer = ByteBuffer.wrap(data);
        this.buffer.order(order);
    }

    /**
     * Sets the byte order for reading.
     */
    public void setByteOrder(ByteOrder order) {
        buffer.order(order);
    }

    /**
     * Gets current position in buffer.
     */
    public int position() {
        return buffer.position();
    }

    /**
     * Sets position in buffer.
     */
    public void position(int newPosition) {
        buffer.position(newPosition);
    }

    /**
     * Reads unsigned 8-bit integer (uint8).
     */
    public short readUInt8() {
        return (short) (buffer.get() & 0xFF);
    }

    /**
     * Reads signed 8-bit integer (int8).
     */
    public byte readInt8() {
        return buffer.get();
    }

    /**
     * Reads unsigned 16-bit integer (uint16).
     */
    public int readUInt16() {
        return buffer.getShort() & 0xFFFF;
    }

    /**
     * Reads signed 16-bit integer (int16).
     */
    public short readInt16() {
        return buffer.getShort();
    }

    /**
     * Reads unsigned 32-bit integer (uint32).
     */
    public long readUInt32() {
        return buffer.getInt() & 0xFFFFFFFFL;
    }

    /**
     * Reads signed 32-bit integer (int32).
     */
    public int readInt32() {
        return buffer.getInt();
    }

    /**
     * Reads unsigned 64-bit integer (uint64).
     */
    public long readUInt64() {
        return buffer.getLong();
    }

    /**
     * Reads 32-bit float.
     */
    public float readFloat() {
        return buffer.getFloat();
    }

    /**
     * Reads 64-bit double.
     */
    public double readDouble() {
        return buffer.getDouble();
    }

    /**
     * Reads a fixed-length string (null-terminated or padded).
     */
    public String readString(int length) {
        byte[] bytes = new byte[length];
        buffer.get(bytes);

        // Find null terminator
        int nullIndex = -1;
        for (int i = 0; i < bytes.length; i++) {
            if (bytes[i] == 0) {
                nullIndex = i;
                break;
            }
        }

        if (nullIndex >= 0) {
            return new String(bytes, 0, nullIndex, StandardCharsets.UTF_8);
        } else {
            return new String(bytes, StandardCharsets.UTF_8);
        }
    }

    /**
     * Reads an array of unsigned 8-bit integers.
     */
    public short[] readUInt8Array(int length) {
        short[] array = new short[length];
        for (int i = 0; i < length; i++) {
            array[i] = readUInt8();
        }
        return array;
    }

    /**
     * Reads an array of unsigned 16-bit integers.
     */
    public int[] readUInt16Array(int length) {
        int[] array = new int[length];
        for (int i = 0; i < length; i++) {
            array[i] = readUInt16();
        }
        return array;
    }

    /**
     * Reads an array of floats.
     */
    public float[] readFloatArray(int length) {
        float[] array = new float[length];
        for (int i = 0; i < length; i++) {
            array[i] = readFloat();
        }
        return array;
    }

    /**
     * Checks if there are remaining bytes to read.
     */
    public boolean hasRemaining() {
        return buffer.hasRemaining();
    }

    /**
     * Gets number of remaining bytes.
     */
    public int remaining() {
        return buffer.remaining();
    }
}
