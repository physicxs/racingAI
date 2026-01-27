package com.racingai.f1telemetry.packets;

/**
 * Lap data packet - 1285 bytes.
 *
 * Contains lap data for all cars including lap times, positions, and pit information.
 * Essential for nearby cars selection logic.
 */
public class PacketLapData {

    private PacketHeader header;
    private LapData[] lapData;
    private short timeTrialPBCarIdx;    // uint8 - 255 if invalid
    private short timeTrialRivalCarIdx; // uint8 - 255 if invalid

    public PacketLapData() {
        this.lapData = new LapData[PacketConstants.MAX_CARS];
        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            this.lapData[i] = new LapData();
        }
    }

    public PacketHeader getHeader() {
        return header;
    }

    public void setHeader(PacketHeader header) {
        this.header = header;
    }

    public LapData[] getLapData() {
        return lapData;
    }

    public void setLapData(LapData[] lapData) {
        this.lapData = lapData;
    }

    public LapData getLapData(int index) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            return lapData[index];
        }
        return null;
    }

    public void setLapData(int index, LapData data) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            this.lapData[index] = data;
        }
    }

    public short getTimeTrialPBCarIdx() {
        return timeTrialPBCarIdx;
    }

    public void setTimeTrialPBCarIdx(short timeTrialPBCarIdx) {
        this.timeTrialPBCarIdx = timeTrialPBCarIdx;
    }

    public short getTimeTrialRivalCarIdx() {
        return timeTrialRivalCarIdx;
    }

    public void setTimeTrialRivalCarIdx(short timeTrialRivalCarIdx) {
        this.timeTrialRivalCarIdx = timeTrialRivalCarIdx;
    }
}
