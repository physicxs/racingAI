package com.racingai.f1telemetry.packets;

/**
 * Per-car status data from the Car Status packet (ID 7).
 *
 * Contains DRS availability, ERS deployment, tyre compound,
 * and FIA flag information.
 */
public class CarStatusData {

    private short tractionControl;      // uint8: 0=off, 1=medium, 2=full
    private short antiLockBrakes;       // uint8: 0=off, 1=on
    private short fuelMix;              // uint8: 0=lean, 1=standard, 2=rich, 3=max
    private short frontBrakeBias;       // uint8: percentage
    private short pitLimiterStatus;     // uint8: 0=off, 1=on
    private float fuelInTank;           // current fuel mass
    private float fuelCapacity;         // fuel capacity
    private float fuelRemainingLaps;    // fuel remaining in terms of laps
    private int maxRPM;                 // uint16: max RPM
    private int idleRPM;               // uint16: idle RPM
    private short maxGears;             // uint8: maximum number of gears
    private short drsAllowed;           // uint8: 0=not allowed, 1=allowed
    private int drsActivationDistance;  // uint16: distance in metres
    private short actualTyreCompound;   // uint8: F1 Modern - 16=C5..20=C1, 7=inter, 8=wet
    private short visualTyreCompound;   // uint8: F1 visual - 16=soft..18=hard, 7=inter, 8=wet
    private short tyresAgeLaps;         // uint8: age in laps of current set
    private byte vehicleFiaFlags;       // int8: -1=invalid, 0=none, 1=green, 2=blue, 3=yellow
    private float enginePowerICE;       // ICE engine power
    private float enginePowerMGUK;      // MGU-K engine power
    private float ersStoreEnergy;       // ERS energy store in Joules
    private short ersDeployMode;        // uint8: 0=none, 1=medium, 2=hotlap, 3=overtake
    private float ersHarvestedThisLapMGUK;  // ERS energy harvested this lap by MGU-K
    private float ersHarvestedThisLapMGUH;  // ERS energy harvested this lap by MGU-H
    private float ersDeployedThisLap;       // ERS energy deployed this lap
    private short networkPaused;        // uint8: whether car is paused in network game

    public CarStatusData() {
    }

    // Getters and setters
    public short getTractionControl() { return tractionControl; }
    public void setTractionControl(short tractionControl) { this.tractionControl = tractionControl; }

    public short getAntiLockBrakes() { return antiLockBrakes; }
    public void setAntiLockBrakes(short antiLockBrakes) { this.antiLockBrakes = antiLockBrakes; }

    public short getFuelMix() { return fuelMix; }
    public void setFuelMix(short fuelMix) { this.fuelMix = fuelMix; }

    public short getFrontBrakeBias() { return frontBrakeBias; }
    public void setFrontBrakeBias(short frontBrakeBias) { this.frontBrakeBias = frontBrakeBias; }

    public short getPitLimiterStatus() { return pitLimiterStatus; }
    public void setPitLimiterStatus(short pitLimiterStatus) { this.pitLimiterStatus = pitLimiterStatus; }

    public float getFuelInTank() { return fuelInTank; }
    public void setFuelInTank(float fuelInTank) { this.fuelInTank = fuelInTank; }

    public float getFuelCapacity() { return fuelCapacity; }
    public void setFuelCapacity(float fuelCapacity) { this.fuelCapacity = fuelCapacity; }

    public float getFuelRemainingLaps() { return fuelRemainingLaps; }
    public void setFuelRemainingLaps(float fuelRemainingLaps) { this.fuelRemainingLaps = fuelRemainingLaps; }

    public int getMaxRPM() { return maxRPM; }
    public void setMaxRPM(int maxRPM) { this.maxRPM = maxRPM; }

    public int getIdleRPM() { return idleRPM; }
    public void setIdleRPM(int idleRPM) { this.idleRPM = idleRPM; }

    public short getMaxGears() { return maxGears; }
    public void setMaxGears(short maxGears) { this.maxGears = maxGears; }

    public short getDrsAllowed() { return drsAllowed; }
    public void setDrsAllowed(short drsAllowed) { this.drsAllowed = drsAllowed; }

    public int getDrsActivationDistance() { return drsActivationDistance; }
    public void setDrsActivationDistance(int drsActivationDistance) { this.drsActivationDistance = drsActivationDistance; }

    public short getActualTyreCompound() { return actualTyreCompound; }
    public void setActualTyreCompound(short actualTyreCompound) { this.actualTyreCompound = actualTyreCompound; }

    public short getVisualTyreCompound() { return visualTyreCompound; }
    public void setVisualTyreCompound(short visualTyreCompound) { this.visualTyreCompound = visualTyreCompound; }

    public short getTyresAgeLaps() { return tyresAgeLaps; }
    public void setTyresAgeLaps(short tyresAgeLaps) { this.tyresAgeLaps = tyresAgeLaps; }

    public byte getVehicleFiaFlags() { return vehicleFiaFlags; }
    public void setVehicleFiaFlags(byte vehicleFiaFlags) { this.vehicleFiaFlags = vehicleFiaFlags; }

    public float getEnginePowerICE() { return enginePowerICE; }
    public void setEnginePowerICE(float enginePowerICE) { this.enginePowerICE = enginePowerICE; }

    public float getEnginePowerMGUK() { return enginePowerMGUK; }
    public void setEnginePowerMGUK(float enginePowerMGUK) { this.enginePowerMGUK = enginePowerMGUK; }

    public float getErsStoreEnergy() { return ersStoreEnergy; }
    public void setErsStoreEnergy(float ersStoreEnergy) { this.ersStoreEnergy = ersStoreEnergy; }

    public short getErsDeployMode() { return ersDeployMode; }
    public void setErsDeployMode(short ersDeployMode) { this.ersDeployMode = ersDeployMode; }

    public float getErsHarvestedThisLapMGUK() { return ersHarvestedThisLapMGUK; }
    public void setErsHarvestedThisLapMGUK(float ersHarvestedThisLapMGUK) { this.ersHarvestedThisLapMGUK = ersHarvestedThisLapMGUK; }

    public float getErsHarvestedThisLapMGUH() { return ersHarvestedThisLapMGUH; }
    public void setErsHarvestedThisLapMGUH(float ersHarvestedThisLapMGUH) { this.ersHarvestedThisLapMGUH = ersHarvestedThisLapMGUH; }

    public float getErsDeployedThisLap() { return ersDeployedThisLap; }
    public void setErsDeployedThisLap(float ersDeployedThisLap) { this.ersDeployedThisLap = ersDeployedThisLap; }

    public short getNetworkPaused() { return networkPaused; }
    public void setNetworkPaused(short networkPaused) { this.networkPaused = networkPaused; }
}
