package com.racingai.f1telemetry.packets;

/**
 * Car status packet (ID 7).
 *
 * Contains status data for all cars including DRS availability,
 * ERS deployment, tyre compound, and FIA flags.
 */
public class PacketCarStatusData {

    private PacketHeader header;
    private CarStatusData[] carStatusData;

    public PacketCarStatusData() {
        this.carStatusData = new CarStatusData[PacketConstants.MAX_CARS];
        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            this.carStatusData[i] = new CarStatusData();
        }
    }

    public PacketHeader getHeader() {
        return header;
    }

    public void setHeader(PacketHeader header) {
        this.header = header;
    }

    public CarStatusData[] getCarStatusData() {
        return carStatusData;
    }

    public void setCarStatusData(int index, CarStatusData data) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            this.carStatusData[index] = data;
        }
    }
}
