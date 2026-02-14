package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Tyre wear data for JSON output.
 * Values in percentage (0-100).
 */
public class TyreWearData {

    @JsonProperty("rearLeft")
    private float rearLeft;

    @JsonProperty("rearRight")
    private float rearRight;

    @JsonProperty("frontLeft")
    private float frontLeft;

    @JsonProperty("frontRight")
    private float frontRight;

    public TyreWearData() {
    }

    public TyreWearData(float rearLeft, float rearRight, float frontLeft, float frontRight) {
        this.rearLeft = rearLeft;
        this.rearRight = rearRight;
        this.frontLeft = frontLeft;
        this.frontRight = frontRight;
    }

    // Getters and setters
    public float getRearLeft() {
        return rearLeft;
    }

    public void setRearLeft(float rearLeft) {
        this.rearLeft = rearLeft;
    }

    public float getRearRight() {
        return rearRight;
    }

    public void setRearRight(float rearRight) {
        this.rearRight = rearRight;
    }

    public float getFrontLeft() {
        return frontLeft;
    }

    public void setFrontLeft(float frontLeft) {
        this.frontLeft = frontLeft;
    }

    public float getFrontRight() {
        return frontRight;
    }

    public void setFrontRight(float frontRight) {
        this.frontRight = frontRight;
    }
}
