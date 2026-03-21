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

    @JsonProperty("world_pos_m")
    private WorldPosition worldPosM;

    // Orientation
    @JsonProperty("yaw")
    private float yaw;

    @JsonProperty("pitch")
    private float pitch;

    @JsonProperty("roll")
    private float roll;

    // G-forces
    @JsonProperty("gForceLateral")
    private float gForceLateral;

    @JsonProperty("gForceLongitudinal")
    private float gForceLongitudinal;

    // DRS
    @JsonProperty("drs")
    private int drs;

    @JsonProperty("drsAllowed")
    private int drsAllowed;

    // ERS
    @JsonProperty("ersDeployMode")
    private int ersDeployMode;

    @JsonProperty("ersStoreEnergy")
    private float ersStoreEnergy;

    @JsonProperty("ersDeployedThisLap")
    private float ersDeployedThisLap;

    @JsonProperty("ersHarvestedThisLapMGUK")
    private float ersHarvestedThisLapMGUK;

    @JsonProperty("ersHarvestedThisLapMGUH")
    private float ersHarvestedThisLapMGUH;

    // Tyre info
    @JsonProperty("tyreSurfaceTemp")
    private int[] tyreSurfaceTemp;

    @JsonProperty("tyreInnerTemp")
    private int[] tyreInnerTemp;

    @JsonProperty("tyreCompound")
    private int tyreCompound;

    @JsonProperty("tyreCompoundVisual")
    private int tyreCompoundVisual;

    @JsonProperty("tyresAgeLaps")
    private int tyresAgeLaps;

    @JsonProperty("tyreDamage")
    private int[] tyreDamage;

    // Brake temps
    @JsonProperty("brakeTemp")
    private int[] brakeTemp;

    // Damage
    @JsonProperty("frontLeftWingDamage")
    private float frontLeftWingDamage;

    @JsonProperty("frontRightWingDamage")
    private float frontRightWingDamage;

    @JsonProperty("rearWingDamage")
    private float rearWingDamage;

    @JsonProperty("floorDamage")
    private int floorDamage;

    @JsonProperty("diffuserDamage")
    private int diffuserDamage;

    @JsonProperty("sidepodDamage")
    private int sidepodDamage;

    // Flags
    @JsonProperty("vehicleFiaFlags")
    private int vehicleFiaFlags;

    public PlayerData() {
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

    public WorldPosition getWorldPosM() {
        return worldPosM;
    }

    public void setWorldPosM(WorldPosition worldPosM) {
        this.worldPosM = worldPosM;
    }

    public void setYaw(float yaw) { this.yaw = yaw; }
    public void setPitch(float pitch) { this.pitch = pitch; }
    public void setRoll(float roll) { this.roll = roll; }
    public void setGForceLateral(float g) { this.gForceLateral = g; }
    public void setGForceLongitudinal(float g) { this.gForceLongitudinal = g; }
    public void setDrs(int drs) { this.drs = drs; }
    public void setDrsAllowed(int drsAllowed) { this.drsAllowed = drsAllowed; }
    public void setErsDeployMode(int mode) { this.ersDeployMode = mode; }
    public void setErsStoreEnergy(float e) { this.ersStoreEnergy = e; }
    public void setErsDeployedThisLap(float e) { this.ersDeployedThisLap = e; }
    public void setErsHarvestedThisLapMGUK(float e) { this.ersHarvestedThisLapMGUK = e; }
    public void setErsHarvestedThisLapMGUH(float e) { this.ersHarvestedThisLapMGUH = e; }
    public void setTyreSurfaceTemp(int[] t) { this.tyreSurfaceTemp = t; }
    public void setTyreInnerTemp(int[] t) { this.tyreInnerTemp = t; }
    public void setTyreCompound(int c) { this.tyreCompound = c; }
    public void setTyreCompoundVisual(int c) { this.tyreCompoundVisual = c; }
    public void setTyresAgeLaps(int a) { this.tyresAgeLaps = a; }
    public void setTyreDamage(int[] d) { this.tyreDamage = d; }
    public void setBrakeTemp(int[] t) { this.brakeTemp = t; }
    public void setFrontLeftWingDamage(float d) { this.frontLeftWingDamage = d; }
    public void setFrontRightWingDamage(float d) { this.frontRightWingDamage = d; }
    public void setRearWingDamage(float d) { this.rearWingDamage = d; }
    public void setFloorDamage(int d) { this.floorDamage = d; }
    public void setDiffuserDamage(int d) { this.diffuserDamage = d; }
    public void setSidepodDamage(int d) { this.sidepodDamage = d; }
    public void setVehicleFiaFlags(int f) { this.vehicleFiaFlags = f; }
}
