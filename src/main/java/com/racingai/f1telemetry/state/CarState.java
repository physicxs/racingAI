package com.racingai.f1telemetry.state;

/**
 * Represents the merged telemetry state of a single car.
 *
 * This class consolidates data from multiple packet types:
 * - Motion: position, velocity, G-forces
 * - Lap Data: lap times, position, distance
 * - Telemetry: speed, gear, throttle, brake, temperatures
 * - Damage: tyre wear, wing damage
 */
public class CarState {

    private final int carIndex;

    // Motion data
    private float worldPositionX;
    private float worldPositionY;
    private float worldPositionZ;
    private float worldVelocityX;
    private float worldVelocityY;
    private float worldVelocityZ;
    private float gForceLateral;
    private float gForceLongitudinal;
    private float gForceVertical;

    // Lap data
    private long lastLapTimeInMS;
    private long currentLapTimeInMS;
    private float lapDistance;
    private float totalDistance;
    private short carPosition;
    private short currentLapNum;
    private short gridPosition;
    private short driverStatus;
    private double deltaToRaceLeaderSeconds;

    // Telemetry data
    private int speed; // km/h
    private short gear;
    private float throttle; // 0.0 to 1.0
    private float steer;    // -1.0 to 1.0
    private float brake;    // 0.0 to 1.0
    private int engineRPM;
    private int engineTemperature;
    private float[] tyresPressure = new float[4]; // [RL, RR, FL, FR]

    // Damage data
    private float[] tyresWear = new float[4]; // [RL, RR, FL, FR]
    private float frontLeftWingDamage;
    private float frontRightWingDamage;
    private float rearWingDamage;

    // Metadata
    private long lastUpdateTimeMs;

    public CarState(int carIndex) {
        this.carIndex = carIndex;
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Motion data setters
    public void updateMotion(float worldPosX, float worldPosY, float worldPosZ,
                            float worldVelX, float worldVelY, float worldVelZ,
                            float gLateral, float gLongitudinal, float gVertical) {
        this.worldPositionX = worldPosX;
        this.worldPositionY = worldPosY;
        this.worldPositionZ = worldPosZ;
        this.worldVelocityX = worldVelX;
        this.worldVelocityY = worldVelY;
        this.worldVelocityZ = worldVelZ;
        this.gForceLateral = gLateral;
        this.gForceLongitudinal = gLongitudinal;
        this.gForceVertical = gVertical;
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Lap data setters
    public void updateLapData(long lastLapTime, long currentLapTime, float lapDist, float totalDist,
                             short position, short lapNum, short grid, short status,
                             double deltaToLeader) {
        this.lastLapTimeInMS = lastLapTime;
        this.currentLapTimeInMS = currentLapTime;
        this.lapDistance = lapDist;
        this.totalDistance = totalDist;
        this.carPosition = position;
        this.currentLapNum = lapNum;
        this.gridPosition = grid;
        this.driverStatus = status;
        this.deltaToRaceLeaderSeconds = deltaToLeader;
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Telemetry data setters
    public void updateTelemetry(int speed, short gear, float throttle, float steer, float brake,
                               int rpm, int engineTemp, float[] tyrePressure) {
        this.speed = speed;
        this.gear = gear;
        this.throttle = throttle;
        this.steer = steer;
        this.brake = brake;
        this.engineRPM = rpm;
        this.engineTemperature = engineTemp;
        if (tyrePressure != null && tyrePressure.length == 4) {
            System.arraycopy(tyrePressure, 0, this.tyresPressure, 0, 4);
        }
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Damage data setters
    public void updateDamage(float[] tyreWear, float flWingDamage, float frWingDamage, float rearWingDamage) {
        if (tyreWear != null && tyreWear.length == 4) {
            System.arraycopy(tyreWear, 0, this.tyresWear, 0, 4);
        }
        this.frontLeftWingDamage = flWingDamage;
        this.frontRightWingDamage = frWingDamage;
        this.rearWingDamage = rearWingDamage;
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Getters
    public int getCarIndex() { return carIndex; }

    public float getWorldPositionX() { return worldPositionX; }
    public float getWorldPositionY() { return worldPositionY; }
    public float getWorldPositionZ() { return worldPositionZ; }
    public float getWorldVelocityX() { return worldVelocityX; }
    public float getWorldVelocityY() { return worldVelocityY; }
    public float getWorldVelocityZ() { return worldVelocityZ; }
    public float getGForceLateral() { return gForceLateral; }
    public float getGForceLongitudinal() { return gForceLongitudinal; }
    public float getGForceVertical() { return gForceVertical; }

    public long getLastLapTimeInMS() { return lastLapTimeInMS; }
    public long getCurrentLapTimeInMS() { return currentLapTimeInMS; }
    public float getLapDistance() { return lapDistance; }
    public float getTotalDistance() { return totalDistance; }
    public short getCarPosition() { return carPosition; }
    public short getCurrentLapNum() { return currentLapNum; }
    public short getGridPosition() { return gridPosition; }
    public short getDriverStatus() { return driverStatus; }
    public double getDeltaToRaceLeaderSeconds() { return deltaToRaceLeaderSeconds; }

    public int getSpeed() { return speed; }
    public short getGear() { return gear; }
    public float getThrottle() { return throttle; }
    public float getSteer() { return steer; }
    public float getBrake() { return brake; }
    public int getEngineRPM() { return engineRPM; }
    public int getEngineTemperature() { return engineTemperature; }
    public float[] getTyresPressure() { return tyresPressure; }

    public float[] getTyresWear() { return tyresWear; }
    public float getFrontLeftWingDamage() { return frontLeftWingDamage; }
    public float getFrontRightWingDamage() { return frontRightWingDamage; }
    public float getRearWingDamage() { return rearWingDamage; }

    public long getLastUpdateTimeMs() { return lastUpdateTimeMs; }

    /**
     * Check if this car is actively racing (on track).
     * Driver status: 1=flying lap, 2=in lap, 3=out lap, 4=on track
     * Excludes 0=in garage
     */
    public boolean isActive() {
        return driverStatus >= 1 && driverStatus <= 4;
    }
}
