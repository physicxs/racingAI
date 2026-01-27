package com.racingai.f1telemetry.packets;

/**
 * Motion packet - 1349 bytes.
 *
 * Contains all motion data for all cars on track.
 * Sent while player is in control.
 */
public class PacketMotionData {

    private PacketHeader header;
    private CarMotionData[] carMotionData;

    public PacketMotionData() {
        this.carMotionData = new CarMotionData[PacketConstants.MAX_CARS];
        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            this.carMotionData[i] = new CarMotionData();
        }
    }

    public PacketHeader getHeader() {
        return header;
    }

    public void setHeader(PacketHeader header) {
        this.header = header;
    }

    public CarMotionData[] getCarMotionData() {
        return carMotionData;
    }

    public void setCarMotionData(CarMotionData[] carMotionData) {
        this.carMotionData = carMotionData;
    }

    public CarMotionData getCarMotionData(int index) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            return carMotionData[index];
        }
        return null;
    }

    public void setCarMotionData(int index, CarMotionData data) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            this.carMotionData[index] = data;
        }
    }
}
