package com.racingai.f1telemetry.packets;

/**
 * Session data packet - 753 bytes.
 *
 * Contains session metadata including track, weather, session type, and timing.
 * Essential for JSON output context.
 *
 * Note: This is a simplified version with key fields for Phase 2.
 * Additional fields (marshal zones, weather forecast, etc.) can be added later.
 */
public class PacketSessionData {

    private PacketHeader header;
    private short weather;                  // uint8 - 0=clear, 1=light cloud, 2=overcast, 3=light rain, 4=heavy rain, 5=storm
    private byte trackTemperature;          // int8 - Degrees Celsius
    private byte airTemperature;            // int8 - Degrees Celsius
    private short totalLaps;                // uint8
    private int trackLength;                // uint16 - Metres
    private short sessionType;              // uint8 - See appendix
    private byte trackId;                   // int8 - -1 for unknown
    private short formula;                  // uint8 - 0=F1 Modern, 1=F1 Classic, etc.
    private int sessionTimeLeft;            // uint16 - Seconds
    private int sessionDuration;            // uint16 - Seconds
    private short pitSpeedLimit;            // uint8 - km/h
    private short gamePaused;               // uint8 - 0=not paused, 1=paused
    private short isSpectating;             // uint8
    private short spectatorCarIndex;        // uint8
    private short sliProNativeSupport;      // uint8
    private short safetyCarStatus;          // uint8 - 0=no safety car, 1=full, 2=virtual, 3=formation lap
    private short networkGame;              // uint8 - 0=offline, 1=online

    public PacketSessionData() {
    }

    // Getters and Setters

    public PacketHeader getHeader() {
        return header;
    }

    public void setHeader(PacketHeader header) {
        this.header = header;
    }

    public short getWeather() {
        return weather;
    }

    public void setWeather(short weather) {
        this.weather = weather;
    }

    public byte getTrackTemperature() {
        return trackTemperature;
    }

    public void setTrackTemperature(byte trackTemperature) {
        this.trackTemperature = trackTemperature;
    }

    public byte getAirTemperature() {
        return airTemperature;
    }

    public void setAirTemperature(byte airTemperature) {
        this.airTemperature = airTemperature;
    }

    public short getTotalLaps() {
        return totalLaps;
    }

    public void setTotalLaps(short totalLaps) {
        this.totalLaps = totalLaps;
    }

    public int getTrackLength() {
        return trackLength;
    }

    public void setTrackLength(int trackLength) {
        this.trackLength = trackLength;
    }

    public short getSessionType() {
        return sessionType;
    }

    public void setSessionType(short sessionType) {
        this.sessionType = sessionType;
    }

    public byte getTrackId() {
        return trackId;
    }

    public void setTrackId(byte trackId) {
        this.trackId = trackId;
    }

    public short getFormula() {
        return formula;
    }

    public void setFormula(short formula) {
        this.formula = formula;
    }

    public int getSessionTimeLeft() {
        return sessionTimeLeft;
    }

    public void setSessionTimeLeft(int sessionTimeLeft) {
        this.sessionTimeLeft = sessionTimeLeft;
    }

    public int getSessionDuration() {
        return sessionDuration;
    }

    public void setSessionDuration(int sessionDuration) {
        this.sessionDuration = sessionDuration;
    }

    public short getPitSpeedLimit() {
        return pitSpeedLimit;
    }

    public void setPitSpeedLimit(short pitSpeedLimit) {
        this.pitSpeedLimit = pitSpeedLimit;
    }

    public short getGamePaused() {
        return gamePaused;
    }

    public void setGamePaused(short gamePaused) {
        this.gamePaused = gamePaused;
    }

    public short getIsSpectating() {
        return isSpectating;
    }

    public void setIsSpectating(short isSpectating) {
        this.isSpectating = isSpectating;
    }

    public short getSpectatorCarIndex() {
        return spectatorCarIndex;
    }

    public void setSpectatorCarIndex(short spectatorCarIndex) {
        this.spectatorCarIndex = spectatorCarIndex;
    }

    public short getSliProNativeSupport() {
        return sliProNativeSupport;
    }

    public void setSliProNativeSupport(short sliProNativeSupport) {
        this.sliProNativeSupport = sliProNativeSupport;
    }

    public short getSafetyCarStatus() {
        return safetyCarStatus;
    }

    public void setSafetyCarStatus(short safetyCarStatus) {
        this.safetyCarStatus = safetyCarStatus;
    }

    public short getNetworkGame() {
        return networkGame;
    }

    public void setNetworkGame(short networkGame) {
        this.networkGame = networkGame;
    }
}
