package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Represents a single telemetry snapshot for JSON output.
 * This is output at 30 Hz as newline-delimited JSON.
 */
public class TelemetrySnapshot {

    @JsonProperty("timestamp")
    private long timestamp;

    @JsonProperty("sessionTime")
    private float sessionTime;

    @JsonProperty("frameId")
    private long frameId;

    @JsonProperty("player")
    private PlayerData player;

    @JsonProperty("nearbyCars")
    private List<NearbyCarData> nearbyCars;

    public TelemetrySnapshot() {
    }

    public TelemetrySnapshot(long timestamp, float sessionTime, long frameId,
                            PlayerData player, List<NearbyCarData> nearbyCars) {
        this.timestamp = timestamp;
        this.sessionTime = sessionTime;
        this.frameId = frameId;
        this.player = player;
        this.nearbyCars = nearbyCars;
    }

    // Getters and setters
    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    public float getSessionTime() {
        return sessionTime;
    }

    public void setSessionTime(float sessionTime) {
        this.sessionTime = sessionTime;
    }

    public long getFrameId() {
        return frameId;
    }

    public void setFrameId(long frameId) {
        this.frameId = frameId;
    }

    public PlayerData getPlayer() {
        return player;
    }

    public void setPlayer(PlayerData player) {
        this.player = player;
    }

    public List<NearbyCarData> getNearbyCars() {
        return nearbyCars;
    }

    public void setNearbyCars(List<NearbyCarData> nearbyCars) {
        this.nearbyCars = nearbyCars;
    }
}
