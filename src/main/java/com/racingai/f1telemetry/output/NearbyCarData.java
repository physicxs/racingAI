package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Nearby car data for JSON output.
 */
public class NearbyCarData {

    @JsonProperty("carIndex")
    private int carIndex;

    @JsonProperty("position")
    private int position;

    @JsonProperty("gap")
    private double gap;

    public NearbyCarData() {
    }

    public NearbyCarData(int carIndex, int position, double gap) {
        this.carIndex = carIndex;
        this.position = position;
        this.gap = gap;
    }

    // Getters and setters
    public int getCarIndex() {
        return carIndex;
    }

    public void setCarIndex(int carIndex) {
        this.carIndex = carIndex;
    }

    public int getPosition() {
        return position;
    }

    public void setPosition(int position) {
        this.position = position;
    }

    public double getGap() {
        return gap;
    }

    public void setGap(double gap) {
        this.gap = gap;
    }
}
