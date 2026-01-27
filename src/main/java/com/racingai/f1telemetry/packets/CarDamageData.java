package com.racingai.f1telemetry.packets;

/**
 * Car damage data for one car.
 *
 * Contains tyre wear, tyre damage, and component damage information.
 * Tyre wear is critical for JSON output per specification.
 * Note: May be unavailable in online multiplayer.
 */
public class CarDamageData {

    private float[] tyresWear;              // float[4] - Percentage
    private short[] tyresDamage;            // uint8[4] - Percentage
    private short[] brakesDamage;           // uint8[4] - Percentage
    private short[] tyreBlisters;           // uint8[4] - Percentage
    private short frontLeftWingDamage;      // uint8 - Percentage
    private short frontRightWingDamage;     // uint8 - Percentage
    private short rearWingDamage;           // uint8 - Percentage
    private short floorDamage;              // uint8 - Percentage
    private short diffuserDamage;           // uint8 - Percentage
    private short sidepodDamage;            // uint8 - Percentage
    private short drsFault;                 // uint8 - 0=OK, 1=fault
    private short ersFault;                 // uint8 - 0=OK, 1=fault
    private short gearBoxDamage;            // uint8 - Percentage
    private short engineDamage;             // uint8 - Percentage
    private short engineMGUHWear;           // uint8 - Percentage
    private short engineESWear;             // uint8 - Percentage
    private short engineCEWear;             // uint8 - Percentage
    private short engineICEWear;            // uint8 - Percentage
    private short engineMGUKWear;           // uint8 - Percentage
    private short engineTCWear;             // uint8 - Percentage
    private short engineBlown;              // uint8 - 0=OK, 1=fault
    private short engineSeized;             // uint8 - 0=OK, 1=fault

    public CarDamageData() {
        this.tyresWear = new float[4];
        this.tyresDamage = new short[4];
        this.brakesDamage = new short[4];
        this.tyreBlisters = new short[4];
    }

    // Getters and Setters

    public float[] getTyresWear() {
        return tyresWear;
    }

    public void setTyresWear(float[] tyresWear) {
        this.tyresWear = tyresWear;
    }

    public short[] getTyresDamage() {
        return tyresDamage;
    }

    public void setTyresDamage(short[] tyresDamage) {
        this.tyresDamage = tyresDamage;
    }

    public short[] getBrakesDamage() {
        return brakesDamage;
    }

    public void setBrakesDamage(short[] brakesDamage) {
        this.brakesDamage = brakesDamage;
    }

    public short[] getTyreBlisters() {
        return tyreBlisters;
    }

    public void setTyreBlisters(short[] tyreBlisters) {
        this.tyreBlisters = tyreBlisters;
    }

    public short getFrontLeftWingDamage() {
        return frontLeftWingDamage;
    }

    public void setFrontLeftWingDamage(short frontLeftWingDamage) {
        this.frontLeftWingDamage = frontLeftWingDamage;
    }

    public short getFrontRightWingDamage() {
        return frontRightWingDamage;
    }

    public void setFrontRightWingDamage(short frontRightWingDamage) {
        this.frontRightWingDamage = frontRightWingDamage;
    }

    public short getRearWingDamage() {
        return rearWingDamage;
    }

    public void setRearWingDamage(short rearWingDamage) {
        this.rearWingDamage = rearWingDamage;
    }

    public short getFloorDamage() {
        return floorDamage;
    }

    public void setFloorDamage(short floorDamage) {
        this.floorDamage = floorDamage;
    }

    public short getDiffuserDamage() {
        return diffuserDamage;
    }

    public void setDiffuserDamage(short diffuserDamage) {
        this.diffuserDamage = diffuserDamage;
    }

    public short getSidepodDamage() {
        return sidepodDamage;
    }

    public void setSidepodDamage(short sidepodDamage) {
        this.sidepodDamage = sidepodDamage;
    }

    public short getDrsFault() {
        return drsFault;
    }

    public void setDrsFault(short drsFault) {
        this.drsFault = drsFault;
    }

    public short getErsFault() {
        return ersFault;
    }

    public void setErsFault(short ersFault) {
        this.ersFault = ersFault;
    }

    public short getGearBoxDamage() {
        return gearBoxDamage;
    }

    public void setGearBoxDamage(short gearBoxDamage) {
        this.gearBoxDamage = gearBoxDamage;
    }

    public short getEngineDamage() {
        return engineDamage;
    }

    public void setEngineDamage(short engineDamage) {
        this.engineDamage = engineDamage;
    }

    public short getEngineMGUHWear() {
        return engineMGUHWear;
    }

    public void setEngineMGUHWear(short engineMGUHWear) {
        this.engineMGUHWear = engineMGUHWear;
    }

    public short getEngineESWear() {
        return engineESWear;
    }

    public void setEngineESWear(short engineESWear) {
        this.engineESWear = engineESWear;
    }

    public short getEngineCEWear() {
        return engineCEWear;
    }

    public void setEngineCEWear(short engineCEWear) {
        this.engineCEWear = engineCEWear;
    }

    public short getEngineICEWear() {
        return engineICEWear;
    }

    public void setEngineICEWear(short engineICEWear) {
        this.engineICEWear = engineICEWear;
    }

    public short getEngineMGUKWear() {
        return engineMGUKWear;
    }

    public void setEngineMGUKWear(short engineMGUKWear) {
        this.engineMGUKWear = engineMGUKWear;
    }

    public short getEngineTCWear() {
        return engineTCWear;
    }

    public void setEngineTCWear(short engineTCWear) {
        this.engineTCWear = engineTCWear;
    }

    public short getEngineBlown() {
        return engineBlown;
    }

    public void setEngineBlown(short engineBlown) {
        this.engineBlown = engineBlown;
    }

    public short getEngineSeized() {
        return engineSeized;
    }

    public void setEngineSeized(short engineSeized) {
        this.engineSeized = engineSeized;
    }
}
