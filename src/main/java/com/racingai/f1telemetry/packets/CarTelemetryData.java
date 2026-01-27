package com.racingai.f1telemetry.packets;

/**
 * Telemetry data for one car.
 *
 * Contains player inputs (steering, throttle, brake, clutch, gear)
 * and car telemetry (speed, RPM, temperatures, pressures).
 * Essential for JSON output stream.
 */
public class CarTelemetryData {

    private int speed;                      // uint16 - Speed (km/h)
    private float throttle;                 // 0.0 to 1.0
    private float steer;                    // -1.0 (full left) to 1.0 (full right)
    private float brake;                    // 0.0 to 1.0
    private short clutch;                   // uint8 - 0 to 100
    private byte gear;                      // int8 - 1-8, N=0, R=-1
    private int engineRPM;                  // uint16
    private short drs;                      // uint8 - 0=off, 1=on
    private short revLightsPercent;         // uint8 - Percentage
    private int revLightsBitValue;          // uint16 - Bit flags
    private int[] brakesTemperature;        // uint16[4] - Celsius
    private short[] tyresSurfaceTemperature; // uint8[4] - Celsius
    private short[] tyresInnerTemperature;  // uint8[4] - Celsius
    private int engineTemperature;          // uint16 - Celsius
    private float[] tyresPressure;          // float[4] - PSI
    private short[] surfaceType;            // uint8[4] - Surface type

    public CarTelemetryData() {
        this.brakesTemperature = new int[4];
        this.tyresSurfaceTemperature = new short[4];
        this.tyresInnerTemperature = new short[4];
        this.tyresPressure = new float[4];
        this.surfaceType = new short[4];
    }

    // Getters and Setters

    public int getSpeed() {
        return speed;
    }

    public void setSpeed(int speed) {
        this.speed = speed;
    }

    public float getThrottle() {
        return throttle;
    }

    public void setThrottle(float throttle) {
        this.throttle = throttle;
    }

    public float getSteer() {
        return steer;
    }

    public void setSteer(float steer) {
        this.steer = steer;
    }

    public float getBrake() {
        return brake;
    }

    public void setBrake(float brake) {
        this.brake = brake;
    }

    public short getClutch() {
        return clutch;
    }

    public void setClutch(short clutch) {
        this.clutch = clutch;
    }

    public byte getGear() {
        return gear;
    }

    public void setGear(byte gear) {
        this.gear = gear;
    }

    public int getEngineRPM() {
        return engineRPM;
    }

    public void setEngineRPM(int engineRPM) {
        this.engineRPM = engineRPM;
    }

    public short getDrs() {
        return drs;
    }

    public void setDrs(short drs) {
        this.drs = drs;
    }

    public short getRevLightsPercent() {
        return revLightsPercent;
    }

    public void setRevLightsPercent(short revLightsPercent) {
        this.revLightsPercent = revLightsPercent;
    }

    public int getRevLightsBitValue() {
        return revLightsBitValue;
    }

    public void setRevLightsBitValue(int revLightsBitValue) {
        this.revLightsBitValue = revLightsBitValue;
    }

    public int[] getBrakesTemperature() {
        return brakesTemperature;
    }

    public void setBrakesTemperature(int[] brakesTemperature) {
        this.brakesTemperature = brakesTemperature;
    }

    public short[] getTyresSurfaceTemperature() {
        return tyresSurfaceTemperature;
    }

    public void setTyresSurfaceTemperature(short[] tyresSurfaceTemperature) {
        this.tyresSurfaceTemperature = tyresSurfaceTemperature;
    }

    public short[] getTyresInnerTemperature() {
        return tyresInnerTemperature;
    }

    public void setTyresInnerTemperature(short[] tyresInnerTemperature) {
        this.tyresInnerTemperature = tyresInnerTemperature;
    }

    public int getEngineTemperature() {
        return engineTemperature;
    }

    public void setEngineTemperature(int engineTemperature) {
        this.engineTemperature = engineTemperature;
    }

    public float[] getTyresPressure() {
        return tyresPressure;
    }

    public void setTyresPressure(float[] tyresPressure) {
        this.tyresPressure = tyresPressure;
    }

    public short[] getSurfaceType() {
        return surfaceType;
    }

    public void setSurfaceType(short[] surfaceType) {
        this.surfaceType = surfaceType;
    }
}
