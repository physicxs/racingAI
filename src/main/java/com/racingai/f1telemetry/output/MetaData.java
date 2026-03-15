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

    public MetaData() {
    }

    public MetaData(Integer trackId, Integer trackLength) {
        this.trackId = trackId;
        this.trackLength = trackLength;
    }

    // Getters and setters
    public Integer getTrackId() {
        return trackId;
    }

    public void setTrackId(Integer trackId) {
        this.trackId = trackId;
    }

    public Integer getTrackLength() {
        return trackLength;
    }

    public void setTrackLength(Integer trackLength) {
        this.trackLength = trackLength;
    }
}
