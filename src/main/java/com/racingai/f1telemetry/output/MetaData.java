package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Session metadata for JSON output.
 */
public class MetaData {

    @JsonProperty("track_id")
    private Integer trackId;

    public MetaData() {
    }

    public MetaData(Integer trackId) {
        this.trackId = trackId;
    }

    // Getters and setters
    public Integer getTrackId() {
        return trackId;
    }

    public void setTrackId(Integer trackId) {
        this.trackId = trackId;
    }
}
