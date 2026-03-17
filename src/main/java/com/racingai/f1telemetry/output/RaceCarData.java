package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Minimal car data for the allCars array in JSON output.
 * Contains only what's needed for track map placement.
 */
public class RaceCarData {

    @JsonProperty("carIndex")
    private int carIndex;

    @JsonProperty("position")
    private int position;

    @JsonProperty("lapDistance")
    private float lapDistance;

    @JsonProperty("lapNumber")
    private int lapNumber;

    @JsonProperty("world_pos_m")
    private WorldPosition worldPosM;

    public RaceCarData() {
    }

    public RaceCarData(int carIndex, int position, float lapDistance, int lapNumber) {
        this.carIndex = carIndex;
        this.position = position;
        this.lapDistance = lapDistance;
        this.lapNumber = lapNumber;
    }

    public RaceCarData(int carIndex, int position, float lapDistance, int lapNumber, WorldPosition worldPosM) {
        this.carIndex = carIndex;
        this.position = position;
        this.lapDistance = lapDistance;
        this.lapNumber = lapNumber;
        this.worldPosM = worldPosM;
    }

    public int getCarIndex() { return carIndex; }
    public void setCarIndex(int carIndex) { this.carIndex = carIndex; }

    public int getPosition() { return position; }
    public void setPosition(int position) { this.position = position; }

    public float getLapDistance() { return lapDistance; }
    public void setLapDistance(float lapDistance) { this.lapDistance = lapDistance; }

    public int getLapNumber() { return lapNumber; }
    public void setLapNumber(int lapNumber) { this.lapNumber = lapNumber; }

    public WorldPosition getWorldPosM() { return worldPosM; }
    public void setWorldPosM(WorldPosition worldPosM) { this.worldPosM = worldPosM; }
}
