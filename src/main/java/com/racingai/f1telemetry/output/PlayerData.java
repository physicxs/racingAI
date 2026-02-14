package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Player car telemetry data for JSON output.
 */
public class PlayerData {

    @JsonProperty("position")
    private int position;

    @JsonProperty("lapNumber")
    private int lapNumber;

    @JsonProperty("lapDistance")
    private float lapDistance;

    @JsonProperty("speed")
    private int speed;

    @JsonProperty("gear")
    private int gear;

    @JsonProperty("throttle")
    private float throttle;

    @JsonProperty("brake")
    private float brake;

    @JsonProperty("steering")
    private float steering;

    @JsonProperty("tyreWear")
    private TyreWearData tyreWear;

    public PlayerData() {
    }

    public PlayerData(int position, int lapNumber, float lapDistance, int speed, int gear,
                     float throttle, float brake, float steering, TyreWearData tyreWear) {
        this.position = position;
        this.lapNumber = lapNumber;
        this.lapDistance = lapDistance;
        this.speed = speed;
        this.gear = gear;
        this.throttle = throttle;
        this.brake = brake;
        this.steering = steering;
        this.tyreWear = tyreWear;
    }

    // Getters and setters
    public int getPosition() {
        return position;
    }

    public void setPosition(int position) {
        this.position = position;
    }

    public int getLapNumber() {
        return lapNumber;
    }

    public void setLapNumber(int lapNumber) {
        this.lapNumber = lapNumber;
    }

    public float getLapDistance() {
        return lapDistance;
    }

    public void setLapDistance(float lapDistance) {
        this.lapDistance = lapDistance;
    }

    public int getSpeed() {
        return speed;
    }

    public void setSpeed(int speed) {
        this.speed = speed;
    }

    public int getGear() {
        return gear;
    }

    public void setGear(int gear) {
        this.gear = gear;
    }

    public float getThrottle() {
        return throttle;
    }

    public void setThrottle(float throttle) {
        this.throttle = throttle;
    }

    public float getBrake() {
        return brake;
    }

    public void setBrake(float brake) {
        this.brake = brake;
    }

    public float getSteering() {
        return steering;
    }

    public void setSteering(float steering) {
        this.steering = steering;
    }

    public TyreWearData getTyreWear() {
        return tyreWear;
    }

    public void setTyreWear(TyreWearData tyreWear) {
        this.tyreWear = tyreWear;
    }
}
