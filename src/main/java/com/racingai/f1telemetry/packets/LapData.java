package com.racingai.f1telemetry.packets;

/**
 * Lap data for one car.
 *
 * Contains lap times, sector times, position data, and pit information.
 * Critical for nearby cars selection logic.
 */
public class LapData {

    private long lastLapTimeInMS;           // uint32
    private long currentLapTimeInMS;        // uint32
    private int sector1TimeMSPart;          // uint16
    private short sector1TimeMinutesPart;   // uint8
    private int sector2TimeMSPart;          // uint16
    private short sector2TimeMinutesPart;   // uint8
    private int deltaToCarInFrontMSPart;    // uint16
    private short deltaToCarInFrontMinutesPart; // uint8
    private int deltaToRaceLeaderMSPart;    // uint16
    private short deltaToRaceLeaderMinutesPart; // uint8
    private float lapDistance;              // Distance around lap (metres)
    private float totalDistance;            // Total distance in session (metres)
    private float safetyCarDelta;           // Delta in seconds for safety car
    private short carPosition;              // uint8 - Race position
    private short currentLapNum;            // uint8
    private short pitStatus;                // uint8 - 0=none, 1=pitting, 2=in pit area
    private short numPitStops;              // uint8
    private short sector;                   // uint8 - 0=sector1, 1=sector2, 2=sector3
    private short currentLapInvalid;        // uint8 - 0=valid, 1=invalid
    private short penalties;                // uint8 - Accumulated time penalties (seconds)
    private short totalWarnings;            // uint8
    private short cornerCuttingWarnings;    // uint8
    private short numUnservedDriveThroughPens; // uint8
    private short numUnservedStopGoPens;    // uint8
    private short gridPosition;             // uint8 - Starting grid position
    private short driverStatus;             // uint8 - 0=garage, 1=flying lap, 2=in lap, 3=out lap, 4=on track
    private short resultStatus;             // uint8 - 0=invalid, 1=inactive, 2=active, 3=finished, etc.
    private short pitLaneTimerActive;       // uint8 - 0=inactive, 1=active
    private int pitLaneTimeInLaneInMS;      // uint16
    private int pitStopTimerInMS;           // uint16
    private short pitStopShouldServePen;    // uint8
    private float speedTrapFastestSpeed;    // Fastest speed (kmph)
    private short speedTrapFastestLap;      // uint8 - Lap number (255=not set)

    public LapData() {
    }

    // Getters and Setters

    public long getLastLapTimeInMS() {
        return lastLapTimeInMS;
    }

    public void setLastLapTimeInMS(long lastLapTimeInMS) {
        this.lastLapTimeInMS = lastLapTimeInMS;
    }

    public long getCurrentLapTimeInMS() {
        return currentLapTimeInMS;
    }

    public void setCurrentLapTimeInMS(long currentLapTimeInMS) {
        this.currentLapTimeInMS = currentLapTimeInMS;
    }

    public int getSector1TimeMSPart() {
        return sector1TimeMSPart;
    }

    public void setSector1TimeMSPart(int sector1TimeMSPart) {
        this.sector1TimeMSPart = sector1TimeMSPart;
    }

    public short getSector1TimeMinutesPart() {
        return sector1TimeMinutesPart;
    }

    public void setSector1TimeMinutesPart(short sector1TimeMinutesPart) {
        this.sector1TimeMinutesPart = sector1TimeMinutesPart;
    }

    public int getSector2TimeMSPart() {
        return sector2TimeMSPart;
    }

    public void setSector2TimeMSPart(int sector2TimeMSPart) {
        this.sector2TimeMSPart = sector2TimeMSPart;
    }

    public short getSector2TimeMinutesPart() {
        return sector2TimeMinutesPart;
    }

    public void setSector2TimeMinutesPart(short sector2TimeMinutesPart) {
        this.sector2TimeMinutesPart = sector2TimeMinutesPart;
    }

    public int getDeltaToCarInFrontMSPart() {
        return deltaToCarInFrontMSPart;
    }

    public void setDeltaToCarInFrontMSPart(int deltaToCarInFrontMSPart) {
        this.deltaToCarInFrontMSPart = deltaToCarInFrontMSPart;
    }

    public short getDeltaToCarInFrontMinutesPart() {
        return deltaToCarInFrontMinutesPart;
    }

    public void setDeltaToCarInFrontMinutesPart(short deltaToCarInFrontMinutesPart) {
        this.deltaToCarInFrontMinutesPart = deltaToCarInFrontMinutesPart;
    }

    public int getDeltaToRaceLeaderMSPart() {
        return deltaToRaceLeaderMSPart;
    }

    public void setDeltaToRaceLeaderMSPart(int deltaToRaceLeaderMSPart) {
        this.deltaToRaceLeaderMSPart = deltaToRaceLeaderMSPart;
    }

    public short getDeltaToRaceLeaderMinutesPart() {
        return deltaToRaceLeaderMinutesPart;
    }

    public void setDeltaToRaceLeaderMinutesPart(short deltaToRaceLeaderMinutesPart) {
        this.deltaToRaceLeaderMinutesPart = deltaToRaceLeaderMinutesPart;
    }

    public float getLapDistance() {
        return lapDistance;
    }

    public void setLapDistance(float lapDistance) {
        this.lapDistance = lapDistance;
    }

    public float getTotalDistance() {
        return totalDistance;
    }

    public void setTotalDistance(float totalDistance) {
        this.totalDistance = totalDistance;
    }

    public float getSafetyCarDelta() {
        return safetyCarDelta;
    }

    public void setSafetyCarDelta(float safetyCarDelta) {
        this.safetyCarDelta = safetyCarDelta;
    }

    public short getCarPosition() {
        return carPosition;
    }

    public void setCarPosition(short carPosition) {
        this.carPosition = carPosition;
    }

    public short getCurrentLapNum() {
        return currentLapNum;
    }

    public void setCurrentLapNum(short currentLapNum) {
        this.currentLapNum = currentLapNum;
    }

    public short getPitStatus() {
        return pitStatus;
    }

    public void setPitStatus(short pitStatus) {
        this.pitStatus = pitStatus;
    }

    public short getNumPitStops() {
        return numPitStops;
    }

    public void setNumPitStops(short numPitStops) {
        this.numPitStops = numPitStops;
    }

    public short getSector() {
        return sector;
    }

    public void setSector(short sector) {
        this.sector = sector;
    }

    public short getCurrentLapInvalid() {
        return currentLapInvalid;
    }

    public void setCurrentLapInvalid(short currentLapInvalid) {
        this.currentLapInvalid = currentLapInvalid;
    }

    public short getPenalties() {
        return penalties;
    }

    public void setPenalties(short penalties) {
        this.penalties = penalties;
    }

    public short getTotalWarnings() {
        return totalWarnings;
    }

    public void setTotalWarnings(short totalWarnings) {
        this.totalWarnings = totalWarnings;
    }

    public short getCornerCuttingWarnings() {
        return cornerCuttingWarnings;
    }

    public void setCornerCuttingWarnings(short cornerCuttingWarnings) {
        this.cornerCuttingWarnings = cornerCuttingWarnings;
    }

    public short getNumUnservedDriveThroughPens() {
        return numUnservedDriveThroughPens;
    }

    public void setNumUnservedDriveThroughPens(short numUnservedDriveThroughPens) {
        this.numUnservedDriveThroughPens = numUnservedDriveThroughPens;
    }

    public short getNumUnservedStopGoPens() {
        return numUnservedStopGoPens;
    }

    public void setNumUnservedStopGoPens(short numUnservedStopGoPens) {
        this.numUnservedStopGoPens = numUnservedStopGoPens;
    }

    public short getGridPosition() {
        return gridPosition;
    }

    public void setGridPosition(short gridPosition) {
        this.gridPosition = gridPosition;
    }

    public short getDriverStatus() {
        return driverStatus;
    }

    public void setDriverStatus(short driverStatus) {
        this.driverStatus = driverStatus;
    }

    public short getResultStatus() {
        return resultStatus;
    }

    public void setResultStatus(short resultStatus) {
        this.resultStatus = resultStatus;
    }

    public short getPitLaneTimerActive() {
        return pitLaneTimerActive;
    }

    public void setPitLaneTimerActive(short pitLaneTimerActive) {
        this.pitLaneTimerActive = pitLaneTimerActive;
    }

    public int getPitLaneTimeInLaneInMS() {
        return pitLaneTimeInLaneInMS;
    }

    public void setPitLaneTimeInLaneInMS(int pitLaneTimeInLaneInMS) {
        this.pitLaneTimeInLaneInMS = pitLaneTimeInLaneInMS;
    }

    public int getPitStopTimerInMS() {
        return pitStopTimerInMS;
    }

    public void setPitStopTimerInMS(int pitStopTimerInMS) {
        this.pitStopTimerInMS = pitStopTimerInMS;
    }

    public short getPitStopShouldServePen() {
        return pitStopShouldServePen;
    }

    public void setPitStopShouldServePen(short pitStopShouldServePen) {
        this.pitStopShouldServePen = pitStopShouldServePen;
    }

    public float getSpeedTrapFastestSpeed() {
        return speedTrapFastestSpeed;
    }

    public void setSpeedTrapFastestSpeed(float speedTrapFastestSpeed) {
        this.speedTrapFastestSpeed = speedTrapFastestSpeed;
    }

    public short getSpeedTrapFastestLap() {
        return speedTrapFastestLap;
    }

    public void setSpeedTrapFastestLap(short speedTrapFastestLap) {
        this.speedTrapFastestLap = speedTrapFastestLap;
    }

    /**
     * Calculate delta to race leader in seconds.
     * Combines minutes and milliseconds parts.
     */
    public double getDeltaToRaceLeaderSeconds() {
        return (deltaToRaceLeaderMinutesPart * 60.0) + (deltaToRaceLeaderMSPart / 1000.0);
    }
}
