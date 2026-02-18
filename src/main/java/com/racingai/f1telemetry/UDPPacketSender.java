package com.racingai.f1telemetry;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * UDP packet sender for testing the F1 telemetry receiver.
 *
 * Sends mock F1 2025 telemetry packets to localhost:20777.
 * Useful for testing without the actual F1 game.
 */
public class UDPPacketSender {

    private static final String TARGET_HOST = "localhost";
    private static final int TARGET_PORT = 20777;

    public static void main(String[] args) throws Exception {
        System.out.println("F1 2025 UDP Packet Sender (Test Tool)");
        System.out.println("Sending mock packets to " + TARGET_HOST + ":" + TARGET_PORT);
        System.out.println("Press Ctrl+C to stop\n");

        DatagramSocket socket = new DatagramSocket();
        InetAddress address = InetAddress.getByName(TARGET_HOST);

        int packetsSent = 0;
        long startTime = System.currentTimeMillis();

        while (true) {
            // Send different packet types
            sendMotionPacket(socket, address, packetsSent);
            Thread.sleep(33); // ~30 Hz

            if (packetsSent % 10 == 0) {
                sendLapDataPacket(socket, address, packetsSent);
            }

            if (packetsSent % 10 == 0) {
                sendTelemetryPacket(socket, address, packetsSent);
            }

            // Send session packet once per second (~30 frames)
            if (packetsSent % 30 == 0) {
                sendSessionPacket(socket, address, packetsSent);
            }

            packetsSent++;

            if (packetsSent % 100 == 0) {
                long elapsed = (System.currentTimeMillis() - startTime) / 1000;
                System.out.printf("Sent %d packets (%.1f Hz)\n",
                    packetsSent, packetsSent / (double) elapsed);
            }
        }
    }

    private static void sendMotionPacket(DatagramSocket socket, InetAddress address, int frameId)
            throws Exception {
        ByteBuffer buffer = ByteBuffer.allocate(1349);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        // Header
        writeHeader(buffer, (byte) 0, frameId); // PacketId 0 = Motion

        // Motion data for 22 cars (60 bytes each)
        for (int i = 0; i < 22; i++) {
            // Position (3 floats = 12 bytes)
            buffer.putFloat(100.0f + i * 10);  // worldPositionX
            buffer.putFloat(0.0f);              // worldPositionY
            buffer.putFloat(200.0f + i * 10);  // worldPositionZ

            // Velocity (3 floats = 12 bytes)
            buffer.putFloat(50.0f);             // worldVelocityX
            buffer.putFloat(0.0f);              // worldVelocityY
            buffer.putFloat(70.0f);             // worldVelocityZ

            // Forward direction (3 int16 = 6 bytes)
            buffer.putShort((short) 0);         // worldForwardDirX
            buffer.putShort((short) 0);         // worldForwardDirY
            buffer.putShort((short) 32767);     // worldForwardDirZ

            // Right direction (3 int16 = 6 bytes)
            buffer.putShort((short) 32767);     // worldRightDirX
            buffer.putShort((short) 0);         // worldRightDirY
            buffer.putShort((short) 0);         // worldRightDirZ

            // G-forces (3 floats = 12 bytes)
            buffer.putFloat(0.5f);              // gForceLateral
            buffer.putFloat(1.2f);              // gForceLongitudinal
            buffer.putFloat(-0.3f);             // gForceVertical

            // Rotation (3 floats = 12 bytes)
            buffer.putFloat(0.1f);              // yaw
            buffer.putFloat(0.0f);              // pitch
            buffer.putFloat(0.0f);              // roll
        }

        sendPacket(socket, address, buffer.array());
    }

    private static void sendLapDataPacket(DatagramSocket socket, InetAddress address, int frameId)
            throws Exception {
        ByteBuffer buffer = ByteBuffer.allocate(1285);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        // Header
        writeHeader(buffer, (byte) 2, frameId); // PacketId 2 = Lap Data

        // Lap data for 22 cars
        for (int i = 0; i < 22; i++) {
            buffer.putInt(90000 + i * 1000);  // lastLapTimeInMS
            buffer.putInt(30000);              // currentLapTimeInMS
            buffer.putShort((short) 15000);    // sector1TimeMSPart
            buffer.put((byte) 0);              // sector1TimeMinutesPart
            buffer.putShort((short) 16000);    // sector2TimeMSPart
            buffer.put((byte) 0);              // sector2TimeMinutesPart
            buffer.putShort((short) 0);        // deltaToCarInFrontMSPart
            buffer.put((byte) 0);              // deltaToCarInFrontMinutesPart
            buffer.putShort((short) (i * 500)); // deltaToRaceLeaderMSPart
            buffer.put((byte) 0);              // deltaToRaceLeaderMinutesPart
            buffer.putFloat(1500.0f + i * 100); // lapDistance
            buffer.putFloat(5000.0f);          // totalDistance
            buffer.putFloat(0.0f);             // safetyCarDelta
            buffer.put((byte) (i + 1));        // carPosition
            buffer.put((byte) 5);              // currentLapNum
            buffer.put((byte) 0);              // pitStatus
            buffer.put((byte) 0);              // numPitStops
            buffer.put((byte) 0);              // sector
            buffer.put((byte) 0);              // currentLapInvalid
            buffer.put((byte) 0);              // penalties
            buffer.put((byte) 0);              // totalWarnings
            buffer.put((byte) 0);              // cornerCuttingWarnings
            buffer.put((byte) 0);              // numUnservedDriveThroughPens
            buffer.put((byte) 0);              // numUnservedStopGoPens
            buffer.put((byte) (i + 6));        // gridPosition (offset to avoid swap detection)
            buffer.put((byte) 4);              // driverStatus (4 = on track)
            buffer.put((byte) 2);              // resultStatus (2 = active)
            buffer.put((byte) 0);              // pitLaneTimerActive
            buffer.putShort((short) 0);        // pitLaneTimeInLaneInMS
            buffer.putShort((short) 0);        // pitStopTimerInMS
            buffer.put((byte) 0);              // pitStopShouldServePen
            buffer.putFloat(320.5f);           // speedTrapFastestSpeed
            buffer.put((byte) 3);              // speedTrapFastestLap
        }

        buffer.put((byte) 255);  // timeTrialPBCarIdx
        buffer.put((byte) 255);  // timeTrialRivalCarIdx

        sendPacket(socket, address, buffer.array());
    }

    private static void sendTelemetryPacket(DatagramSocket socket, InetAddress address, int frameId)
            throws Exception {
        ByteBuffer buffer = ByteBuffer.allocate(1352);
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        // Header
        writeHeader(buffer, (byte) 6, frameId); // PacketId 6 = Car Telemetry

        // Telemetry data for 22 cars
        for (int i = 0; i < 22; i++) {
            buffer.putShort((short) (250 + i * 5)); // speed (km/h)
            buffer.putFloat(0.8f);                   // throttle
            buffer.putFloat(0.0f);                   // steer
            buffer.putFloat(0.0f);                   // brake
            buffer.put((byte) 0);                    // clutch
            buffer.put((byte) 7);                    // gear
            buffer.putShort((short) 12000);          // engineRPM
            buffer.put((byte) 0);                    // drs
            buffer.put((byte) 50);                   // revLightsPercent
            buffer.putShort((short) 0);              // revLightsBitValue

            // Brakes temperature [4]
            for (int j = 0; j < 4; j++) {
                buffer.putShort((short) 450);
            }
            // Tyres surface temperature [4]
            for (int j = 0; j < 4; j++) {
                buffer.put((byte) 85);
            }
            // Tyres inner temperature [4]
            for (int j = 0; j < 4; j++) {
                buffer.put((byte) 90);
            }
            buffer.putShort((short) 95);  // engineTemperature
            // Tyres pressure [4]
            for (int j = 0; j < 4; j++) {
                buffer.putFloat(23.5f);
            }
            // Surface type [4]
            for (int j = 0; j < 4; j++) {
                buffer.put((byte) 0);
            }
        }

        buffer.put((byte) 255);  // mfdPanelIndex
        buffer.put((byte) 255);  // mfdPanelIndexSecondaryPlayer
        buffer.put((byte) 0);    // suggestedGear

        sendPacket(socket, address, buffer.array());
    }

    private static void sendSessionPacket(DatagramSocket socket, InetAddress address, int frameId)
            throws Exception {
        ByteBuffer buffer = ByteBuffer.allocate(632);  // Session packet size
        buffer.order(ByteOrder.LITTLE_ENDIAN);

        // Header
        writeHeader(buffer, (byte) 1, frameId); // PacketId 1 = Session

        // Session data
        buffer.put((byte) 0);              // weather (0 = clear)
        buffer.put((byte) 25);             // trackTemperature (25°C)
        buffer.put((byte) 22);             // airTemperature (22°C)
        buffer.put((byte) 5);              // totalLaps
        buffer.putShort((short) 5303);     // trackLength (5303m = Melbourne)
        buffer.put((byte) 12);             // sessionType (12 = Time Trial)
        buffer.put((byte) 0);              // trackId (0 = Melbourne/Australia)
        buffer.put((byte) 0);              // formula (0 = F1 Modern)
        buffer.putShort((short) 3600);     // sessionTimeLeft (seconds)
        buffer.putShort((short) 3600);     // sessionDuration (seconds)
        buffer.put((byte) 80);             // pitSpeedLimit (80 km/h)
        buffer.put((byte) 0);              // gamePaused
        buffer.put((byte) 0);              // isSpectating
        buffer.put((byte) 255);            // spectatorCarIndex
        buffer.put((byte) 1);              // sliProNativeSupport
        buffer.put((byte) 0);              // safetyCarStatus

        // Fill rest with zeros (simplified - skip marshal zones, weather forecast, etc.)
        while (buffer.position() < buffer.capacity()) {
            buffer.put((byte) 0);
        }

        sendPacket(socket, address, buffer.array());
    }

    private static void writeHeader(ByteBuffer buffer, byte packetId, int frameId) {
        buffer.putShort((short) 2025);     // packetFormat
        buffer.put((byte) 25);              // gameYear
        buffer.put((byte) 1);               // gameMajorVersion
        buffer.put((byte) 0);               // gameMinorVersion
        buffer.put((byte) 1);               // packetVersion
        buffer.put(packetId);               // packetId
        buffer.putLong(123456789L);         // sessionUID
        buffer.putFloat(frameId * 0.033f);  // sessionTime
        buffer.putInt(frameId);             // frameIdentifier
        buffer.putInt(frameId);             // overallFrameIdentifier
        buffer.put((byte) 0);               // playerCarIndex
        buffer.put((byte) 255);             // secondaryPlayerCarIndex
    }

    private static void sendPacket(DatagramSocket socket, InetAddress address, byte[] data)
            throws Exception {
        DatagramPacket packet = new DatagramPacket(data, data.length, address, TARGET_PORT);
        socket.send(packet);
    }
}
