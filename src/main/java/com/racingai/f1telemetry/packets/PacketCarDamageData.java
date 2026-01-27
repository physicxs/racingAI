package com.racingai.f1telemetry.packets;

/**
 * Car damage packet - 1041 bytes.
 *
 * Contains damage data for all cars including tyre wear.
 * Tyre wear data is essential for JSON output.
 * Note: May be restricted in online multiplayer.
 */
public class PacketCarDamageData {

    private PacketHeader header;
    private CarDamageData[] carDamageData;

    public PacketCarDamageData() {
        this.carDamageData = new CarDamageData[PacketConstants.MAX_CARS];
        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            this.carDamageData[i] = new CarDamageData();
        }
    }

    public PacketHeader getHeader() {
        return header;
    }

    public void setHeader(PacketHeader header) {
        this.header = header;
    }

    public CarDamageData[] getCarDamageData() {
        return carDamageData;
    }

    public void setCarDamageData(CarDamageData[] carDamageData) {
        this.carDamageData = carDamageData;
    }

    public CarDamageData getCarDamageData(int index) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            return carDamageData[index];
        }
        return null;
    }

    public void setCarDamageData(int index, CarDamageData data) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            this.carDamageData[index] = data;
        }
    }
}
