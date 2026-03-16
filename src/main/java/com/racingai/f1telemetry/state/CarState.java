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
    private float yaw;
    private float pitch;
    private float roll;

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
    private short drs; // 0=off, 1=on
    private short[] tyresSurfaceTemperature = new short[4];
    private short[] tyresInnerTemperature = new short[4];
    private int[] brakesTemperature = new int[4];

    // Damage data
    private float[] tyresWear = new float[4]; // [RL, RR, FL, FR]
    private float frontLeftWingDamage;
    private float frontRightWingDamage;
    private float rearWingDamage;
    private short floorDamage;
    private short diffuserDamage;
    private short sidepodDamage;
    private short[] tyresDamage = new short[4];

    // Car status data (from CarStatus packet)
    private short drsAllowed; // 0=not allowed, 1=allowed
    private short ersDeployMode; // 0=none, 1=medium, 2=hotlap, 3=overtake
    private float ersStoreEnergy;
    private float ersDeployedThisLap;
    private float ersHarvestedThisLapMGUK;
    private float ersHarvestedThisLapMGUH;
    private short actualTyreCompound;
    private short visualTyreCompound;
    private short tyresAgeLaps;
    private byte vehicleFiaFlags; // -1=invalid, 0=none, 1=green, 2=blue, 3=yellow

    // Metadata
    private long lastUpdateTimeMs;

    public CarState(int carIndex) {
        this.carIndex = carIndex;
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Motion data setters
    public void updateMotion(float worldPosX, float worldPosY, float worldPosZ,
                            float worldVelX, float worldVelY, float worldVelZ,
                            float gLateral, float gLongitudinal, float gVertical,
                            float yaw, float pitch, float roll) {
        this.worldPositionX = worldPosX;
        this.worldPositionY = worldPosY;
        this.worldPositionZ = worldPosZ;
        this.worldVelocityX = worldVelX;
        this.worldVelocityY = worldVelY;
        this.worldVelocityZ = worldVelZ;
        this.gForceLateral = gLateral;
        this.gForceLongitudinal = gLongitudinal;
        this.gForceVertical = gVertical;
        this.yaw = yaw;
        this.pitch = pitch;
        this.roll = roll;
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
                               int rpm, int engineTemp, float[] tyrePressure,
                               short drs, short[] tyreSurfTemp, short[] tyreInnerTemp,
                               int[] brakeTemp) {
        this.speed = speed;
        this.gear = gear;
        this.throttle = throttle;
        this.steer = steer;
        this.brake = brake;
        this.engineRPM = rpm;
        this.engineTemperature = engineTemp;
        this.drs = drs;
        if (tyrePressure != null && tyrePressure.length == 4) {
            System.arraycopy(tyrePressure, 0, this.tyresPressure, 0, 4);
        }
        if (tyreSurfTemp != null && tyreSurfTemp.length == 4) {
            System.arraycopy(tyreSurfTemp, 0, this.tyresSurfaceTemperature, 0, 4);
        }
        if (tyreInnerTemp != null && tyreInnerTemp.length == 4) {
            System.arraycopy(tyreInnerTemp, 0, this.tyresInnerTemperature, 0, 4);
        }
        if (brakeTemp != null && brakeTemp.length == 4) {
            System.arraycopy(brakeTemp, 0, this.brakesTemperature, 0, 4);
        }
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Damage data setters
    public void updateDamage(float[] tyreWear, float flWingDamage, float frWingDamage,
                            float rearWingDamage, short floorDmg, short diffuserDmg,
                            short sidepodDmg, short[] tyreDmg) {
        if (tyreWear != null && tyreWear.length == 4) {
            System.arraycopy(tyreWear, 0, this.tyresWear, 0, 4);
        }
        this.frontLeftWingDamage = flWingDamage;
        this.frontRightWingDamage = frWingDamage;
        this.rearWingDamage = rearWingDamage;
        this.floorDamage = floorDmg;
        this.diffuserDamage = diffuserDmg;
        this.sidepodDamage = sidepodDmg;
        if (tyreDmg != null && tyreDmg.length == 4) {
            System.arraycopy(tyreDmg, 0, this.tyresDamage, 0, 4);
        }
        this.lastUpdateTimeMs = System.currentTimeMillis();
    }

    // Car status data setters
    public void updateCarStatus(short drsAllowed, short ersDeployMode, float ersStoreEnergy,
                               float ersDeployedThisLap, float ersHarvestedMGUK,
                               float ersHarvestedMGUH, short actualTyreCompound,
                               short visualTyreCompound, short tyresAgeLaps,
                               byte vehicleFiaFlags) {
        this.drsAllowed = drsAllowed;
        this.ersDeployMode = ersDeployMode;
        this.ersStoreEnergy = ersStoreEnergy;
        this.ersDeployedThisLap = ersDeployedThisLap;
        this.ersHarvestedThisLapMGUK = ersHarvestedMGUK;
        this.ersHarvestedThisLapMGUH = ersHarvestedMGUH;
        this.actualTyreCompound = actualTyreCompound;
        this.visualTyreCompound = visualTyreCompound;
        this.tyresAgeLaps = tyresAgeLaps;
        this.vehicleFiaFlags = vehicleFiaFlags;
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

    public float getYaw() { return yaw; }
    public float getPitch() { return pitch; }
    public float getRoll() { return roll; }

    public short getDrs() { return drs; }
    public short[] getTyresSurfaceTemperature() { return tyresSurfaceTemperature; }
    public short[] getTyresInnerTemperature() { return tyresInnerTemperature; }
    public int[] getBrakesTemperature() { return brakesTemperature; }

    public float[] getTyresWear() { return tyresWear; }
    public float getFrontLeftWingDamage() { return frontLeftWingDamage; }
    public float getFrontRightWingDamage() { return frontRightWingDamage; }
    public float getRearWingDamage() { return rearWingDamage; }
    public short getFloorDamage() { return floorDamage; }
    public short getDiffuserDamage() { return diffuserDamage; }
    public short getSidepodDamage() { return sidepodDamage; }
    public short[] getTyresDamage() { return tyresDamage; }

    public short getDrsAllowed() { return drsAllowed; }
    public short getErsDeployMode() { return ersDeployMode; }
    public float getErsStoreEnergy() { return ersStoreEnergy; }
    public float getErsDeployedThisLap() { return ersDeployedThisLap; }
    public float getErsHarvestedThisLapMGUK() { return ersHarvestedThisLapMGUK; }
    public float getErsHarvestedThisLapMGUH() { return ersHarvestedThisLapMGUH; }
    public short getActualTyreCompound() { return actualTyreCompound; }
    public short getVisualTyreCompound() { return visualTyreCompound; }
    public short getTyresAgeLaps() { return tyresAgeLaps; }
    public byte getVehicleFiaFlags() { return vehicleFiaFlags; }

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
