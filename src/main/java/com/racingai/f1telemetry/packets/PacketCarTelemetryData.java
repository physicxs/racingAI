package com.racingai.f1telemetry.packets;

/**
 * Car telemetry packet - 1352 bytes.
 *
 * Contains telemetry data for all cars including inputs, speed, gear, RPM, temperatures.
 * Essential for player state output.
 */
public class PacketCarTelemetryData {

    private PacketHeader header;
    private CarTelemetryData[] carTelemetryData;
    private short mfdPanelIndex;                    // uint8 - 255 = closed
    private short mfdPanelIndexSecondaryPlayer;     // uint8
    private byte suggestedGear;                     // int8 - 1-8, 0 = no suggestion

    public PacketCarTelemetryData() {
        this.carTelemetryData = new CarTelemetryData[PacketConstants.MAX_CARS];
        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            this.carTelemetryData[i] = new CarTelemetryData();
        }
    }

    public PacketHeader getHeader() {
        return header;
    }

    public void setHeader(PacketHeader header) {
        this.header = header;
    }

    public CarTelemetryData[] getCarTelemetryData() {
        return carTelemetryData;
    }

    public void setCarTelemetryData(CarTelemetryData[] carTelemetryData) {
        this.carTelemetryData = carTelemetryData;
    }

    public CarTelemetryData getCarTelemetryData(int index) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            return carTelemetryData[index];
        }
        return null;
    }

    public void setCarTelemetryData(int index, CarTelemetryData data) {
        if (index >= 0 && index < PacketConstants.MAX_CARS) {
            this.carTelemetryData[index] = data;
        }
    }

    public short getMfdPanelIndex() {
        return mfdPanelIndex;
    }

    public void setMfdPanelIndex(short mfdPanelIndex) {
        this.mfdPanelIndex = mfdPanelIndex;
    }

    public short getMfdPanelIndexSecondaryPlayer() {
        return mfdPanelIndexSecondaryPlayer;
    }

    public void setMfdPanelIndexSecondaryPlayer(short mfdPanelIndexSecondaryPlayer) {
        this.mfdPanelIndexSecondaryPlayer = mfdPanelIndexSecondaryPlayer;
    }

    public byte getSuggestedGear() {
        return suggestedGear;
    }

    public void setSuggestedGear(byte suggestedGear) {
        this.suggestedGear = suggestedGear;
    }
}
