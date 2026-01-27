package com.racingai.f1telemetry.packets;

/**
 * Motion data for one car.
 *
 * Contains world position, velocity, orientation, and G-force data.
 */
public class CarMotionData {

    private float worldPositionX;       // World space X position (metres)
    private float worldPositionY;       // World space Y position
    private float worldPositionZ;       // World space Z position
    private float worldVelocityX;       // Velocity in world space X (metres/s)
    private float worldVelocityY;       // Velocity in world space Y
    private float worldVelocityZ;       // Velocity in world space Z
    private short worldForwardDirX;     // int16 - World space forward X (normalised)
    private short worldForwardDirY;     // int16 - World space forward Y (normalised)
    private short worldForwardDirZ;     // int16 - World space forward Z (normalised)
    private short worldRightDirX;       // int16 - World space right X (normalised)
    private short worldRightDirY;       // int16 - World space right Y (normalised)
    private short worldRightDirZ;       // int16 - World space right Z (normalised)
    private float gForceLateral;        // Lateral G-Force component
    private float gForceLongitudinal;   // Longitudinal G-Force component
    private float gForceVertical;       // Vertical G-Force component
    private float yaw;                  // Yaw angle (radians)
    private float pitch;                // Pitch angle (radians)
    private float roll;                 // Roll angle (radians)

    public CarMotionData() {
    }

    // Getters and Setters

    public float getWorldPositionX() {
        return worldPositionX;
    }

    public void setWorldPositionX(float worldPositionX) {
        this.worldPositionX = worldPositionX;
    }

    public float getWorldPositionY() {
        return worldPositionY;
    }

    public void setWorldPositionY(float worldPositionY) {
        this.worldPositionY = worldPositionY;
    }

    public float getWorldPositionZ() {
        return worldPositionZ;
    }

    public void setWorldPositionZ(float worldPositionZ) {
        this.worldPositionZ = worldPositionZ;
    }

    public float getWorldVelocityX() {
        return worldVelocityX;
    }

    public void setWorldVelocityX(float worldVelocityX) {
        this.worldVelocityX = worldVelocityX;
    }

    public float getWorldVelocityY() {
        return worldVelocityY;
    }

    public void setWorldVelocityY(float worldVelocityY) {
        this.worldVelocityY = worldVelocityY;
    }

    public float getWorldVelocityZ() {
        return worldVelocityZ;
    }

    public void setWorldVelocityZ(float worldVelocityZ) {
        this.worldVelocityZ = worldVelocityZ;
    }

    public short getWorldForwardDirX() {
        return worldForwardDirX;
    }

    public void setWorldForwardDirX(short worldForwardDirX) {
        this.worldForwardDirX = worldForwardDirX;
    }

    public short getWorldForwardDirY() {
        return worldForwardDirY;
    }

    public void setWorldForwardDirY(short worldForwardDirY) {
        this.worldForwardDirY = worldForwardDirY;
    }

    public short getWorldForwardDirZ() {
        return worldForwardDirZ;
    }

    public void setWorldForwardDirZ(short worldForwardDirZ) {
        this.worldForwardDirZ = worldForwardDirZ;
    }

    public short getWorldRightDirX() {
        return worldRightDirX;
    }

    public void setWorldRightDirX(short worldRightDirX) {
        this.worldRightDirX = worldRightDirX;
    }

    public short getWorldRightDirY() {
        return worldRightDirY;
    }

    public void setWorldRightDirY(short worldRightDirY) {
        this.worldRightDirY = worldRightDirY;
    }

    public short getWorldRightDirZ() {
        return worldRightDirZ;
    }

    public void setWorldRightDirZ(short worldRightDirZ) {
        this.worldRightDirZ = worldRightDirZ;
    }

    public float getgForceLateral() {
        return gForceLateral;
    }

    public void setgForceLateral(float gForceLateral) {
        this.gForceLateral = gForceLateral;
    }

    public float getgForceLongitudinal() {
        return gForceLongitudinal;
    }

    public void setgForceLongitudinal(float gForceLongitudinal) {
        this.gForceLongitudinal = gForceLongitudinal;
    }

    public float getgForceVertical() {
        return gForceVertical;
    }

    public void setgForceVertical(float gForceVertical) {
        this.gForceVertical = gForceVertical;
    }

    public float getYaw() {
        return yaw;
    }

    public void setYaw(float yaw) {
        this.yaw = yaw;
    }

    public float getPitch() {
        return pitch;
    }

    public void setPitch(float pitch) {
        this.pitch = pitch;
    }

    public float getRoll() {
        return roll;
    }

    public void setRoll(float roll) {
        this.roll = roll;
    }
}
