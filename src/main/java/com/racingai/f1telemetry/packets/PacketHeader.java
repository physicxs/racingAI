package com.racingai.f1telemetry.packets;

/**
 * Header for all F1 2025 UDP packets - 29 bytes.
 *
 * Contains metadata common to all packet types including:
 * - Packet format and version information
 * - Session and frame identifiers
 * - Player car index
 */
public class PacketHeader {

    private int packetFormat;           // uint16 - Expected to be 2025
    private short gameYear;             // uint8 - Game year (e.g., 25)
    private short gameMajorVersion;     // uint8 - Game major version
    private short gameMinorVersion;     // uint8 - Game minor version
    private short packetVersion;        // uint8 - Version of this packet type
    private short packetId;             // uint8 - Packet type identifier
    private long sessionUID;            // uint64 - Unique session identifier
    private float sessionTime;          // float - Session timestamp
    private long frameIdentifier;       // uint32 - Frame identifier
    private long overallFrameIdentifier; // uint32 - Overall frame identifier
    private short playerCarIndex;       // uint8 - Index of player's car
    private short secondaryPlayerCarIndex; // uint8 - Index of secondary player (255 if none)

    public PacketHeader() {
    }

    // Getters and Setters

    public int getPacketFormat() {
        return packetFormat;
    }

    public void setPacketFormat(int packetFormat) {
        this.packetFormat = packetFormat;
    }

    public short getGameYear() {
        return gameYear;
    }

    public void setGameYear(short gameYear) {
        this.gameYear = gameYear;
    }

    public short getGameMajorVersion() {
        return gameMajorVersion;
    }

    public void setGameMajorVersion(short gameMajorVersion) {
        this.gameMajorVersion = gameMajorVersion;
    }

    public short getGameMinorVersion() {
        return gameMinorVersion;
    }

    public void setGameMinorVersion(short gameMinorVersion) {
        this.gameMinorVersion = gameMinorVersion;
    }

    public short getPacketVersion() {
        return packetVersion;
    }

    public void setPacketVersion(short packetVersion) {
        this.packetVersion = packetVersion;
    }

    public short getPacketId() {
        return packetId;
    }

    public void setPacketId(short packetId) {
        this.packetId = packetId;
    }

    public long getSessionUID() {
        return sessionUID;
    }

    public void setSessionUID(long sessionUID) {
        this.sessionUID = sessionUID;
    }

    public float getSessionTime() {
        return sessionTime;
    }

    public void setSessionTime(float sessionTime) {
        this.sessionTime = sessionTime;
    }

    public long getFrameIdentifier() {
        return frameIdentifier;
    }

    public void setFrameIdentifier(long frameIdentifier) {
        this.frameIdentifier = frameIdentifier;
    }

    public long getOverallFrameIdentifier() {
        return overallFrameIdentifier;
    }

    public void setOverallFrameIdentifier(long overallFrameIdentifier) {
        this.overallFrameIdentifier = overallFrameIdentifier;
    }

    public short getPlayerCarIndex() {
        return playerCarIndex;
    }

    public void setPlayerCarIndex(short playerCarIndex) {
        this.playerCarIndex = playerCarIndex;
    }

    public short getSecondaryPlayerCarIndex() {
        return secondaryPlayerCarIndex;
    }

    public void setSecondaryPlayerCarIndex(short secondaryPlayerCarIndex) {
        this.secondaryPlayerCarIndex = secondaryPlayerCarIndex;
    }

    @Override
    public String toString() {
        return "PacketHeader{" +
                "packetFormat=" + packetFormat +
                ", gameYear=" + gameYear +
                ", packetId=" + packetId +
                ", sessionUID=" + sessionUID +
                ", sessionTime=" + sessionTime +
                ", frameIdentifier=" + frameIdentifier +
                ", playerCarIndex=" + playerCarIndex +
                '}';
    }
}
