package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Session metadata for JSON output.
 */
public class MetaData {

    @JsonProperty("track_id")
    private Integer trackId;

    @JsonProperty("track_length")
    private Integer trackLength;

    @JsonProperty("safety_car")
    private Integer safetyCarStatus;

    @JsonProperty("weather")
    private Integer weather;

    @JsonProperty("track_temp")
    private Integer trackTemperature;

    @JsonProperty("air_temp")
    private Integer airTemperature;

    @JsonProperty("total_laps")
    private Integer totalLaps;

    public MetaData() {
    }

    public MetaData(Integer trackId, Integer trackLength) {
        this.trackId = trackId;
        this.trackLength = trackLength;
    }

    // Getters and setters
    public Integer getTrackId() { return trackId; }
    public void setTrackId(Integer trackId) { this.trackId = trackId; }
    public Integer getTrackLength() { return trackLength; }
    public void setTrackLength(Integer trackLength) { this.trackLength = trackLength; }
    public Integer getSafetyCarStatus() { return safetyCarStatus; }
    public void setSafetyCarStatus(Integer s) { this.safetyCarStatus = s; }
    public Integer getWeather() { return weather; }
    public void setWeather(Integer w) { this.weather = w; }
    public Integer getTrackTemperature() { return trackTemperature; }
    public void setTrackTemperature(Integer t) { this.trackTemperature = t; }
    public Integer getAirTemperature() { return airTemperature; }
    public void setAirTemperature(Integer t) { this.airTemperature = t; }
    public Integer getTotalLaps() { return totalLaps; }
    public void setTotalLaps(Integer l) { this.totalLaps = l; }
}
