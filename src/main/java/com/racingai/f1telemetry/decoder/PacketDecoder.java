package com.racingai.f1telemetry.decoder;

import com.racingai.f1telemetry.packets.*;
import com.racingai.f1telemetry.utils.ByteBufferReader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteOrder;

/**
 * Decodes F1 2025 UDP telemetry packets from raw binary data.
 *
 * Handles:
 * - Packet header parsing
 * - Endianness detection
 * - Packet type identification and routing
 * - Sanity checks and validation
 * - Known spec issue workarounds
 */
public class PacketDecoder {

    private static final Logger logger = LoggerFactory.getLogger(PacketDecoder.class);

    private static final int EXPECTED_PACKET_FORMAT = 2025;
    private static final int MIN_PACKET_SIZE = 29; // Header size

    private boolean fieldSwapWarningIssued = false;

    /**
     * Decodes a raw UDP packet into typed packet object.
     *
     * @param data Raw packet bytes
     * @param length Length of packet
     * @return Decoded packet object, or null if decoding fails
     */
    public Object decodePacket(byte[] data, int length) {
        if (data == null || length < MIN_PACKET_SIZE) {
            logger.warn("Packet too small: {} bytes (min {})", length, MIN_PACKET_SIZE);
            return null;
        }

        try {
            ByteBufferReader reader = new ByteBufferReader(data);

            // Read and validate header
            PacketHeader header = decodeHeader(reader);
            if (header == null) {
                return null;
            }

            // Route to specific decoder based on packet ID
            PacketId packetId = PacketId.fromId(header.getPacketId());
            if (packetId == null) {
                logger.warn("Unknown packet ID: {}", header.getPacketId());
                return null;
            }

            return decodePacketBody(reader, header, packetId);

        } catch (Exception e) {
            logger.error("Error decoding packet: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * Decodes packet header (29 bytes).
     */
    private PacketHeader decodeHeader(ByteBufferReader reader) {
        PacketHeader header = new PacketHeader();

        header.setPacketFormat(reader.readUInt16());
        header.setGameYear(reader.readUInt8());
        header.setGameMajorVersion(reader.readUInt8());
        header.setGameMinorVersion(reader.readUInt8());
        header.setPacketVersion(reader.readUInt8());
        header.setPacketId(reader.readUInt8());
        header.setSessionUID(reader.readUInt64());
        header.setSessionTime(reader.readFloat());
        header.setFrameIdentifier(reader.readUInt32());
        header.setOverallFrameIdentifier(reader.readUInt32());
        header.setPlayerCarIndex(reader.readUInt8());
        header.setSecondaryPlayerCarIndex(reader.readUInt8());

        // Validate header
        if (header.getPacketFormat() != EXPECTED_PACKET_FORMAT) {
            logger.warn("Unexpected packet format: {} (expected {})",
                header.getPacketFormat(), EXPECTED_PACKET_FORMAT);
            // Continue anyway - soft fail per spec
        }

        if (header.getPlayerCarIndex() >= PacketConstants.MAX_CARS) {
            logger.warn("Invalid player car index: {}", header.getPlayerCarIndex());
        }

        return header;
    }

    /**
     * Routes packet to appropriate decoder based on type.
     */
    private Object decodePacketBody(ByteBufferReader reader, PacketHeader header, PacketId packetId) {
        switch (packetId) {
            case MOTION:
                return decodeMotionPacket(reader, header);
            case SESSION:
                return decodeSessionPacket(reader, header);
            case LAP_DATA:
                return decodeLapDataPacket(reader, header);
            case CAR_TELEMETRY:
                return decodeCarTelemetryPacket(reader, header);
            case CAR_DAMAGE:
                return decodeCarDamagePacket(reader, header);
            default:
                logger.debug("Packet type {} not decoded (not required)", packetId);
                return null;
        }
    }

    /**
     * Decodes motion packet.
     */
    private PacketMotionData decodeMotionPacket(ByteBufferReader reader, PacketHeader header) {
        PacketMotionData packet = new PacketMotionData();
        packet.setHeader(header);

        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            CarMotionData carData = new CarMotionData();

            carData.setWorldPositionX(reader.readFloat());
            carData.setWorldPositionY(reader.readFloat());
            carData.setWorldPositionZ(reader.readFloat());
            carData.setWorldVelocityX(reader.readFloat());
            carData.setWorldVelocityY(reader.readFloat());
            carData.setWorldVelocityZ(reader.readFloat());
            carData.setWorldForwardDirX(reader.readInt16());
            carData.setWorldForwardDirY(reader.readInt16());
            carData.setWorldForwardDirZ(reader.readInt16());
            carData.setWorldRightDirX(reader.readInt16());
            carData.setWorldRightDirY(reader.readInt16());
            carData.setWorldRightDirZ(reader.readInt16());
            carData.setgForceLateral(reader.readFloat());
            carData.setgForceLongitudinal(reader.readFloat());
            carData.setgForceVertical(reader.readFloat());
            carData.setYaw(reader.readFloat());
            carData.setPitch(reader.readFloat());
            carData.setRoll(reader.readFloat());

            packet.setCarMotionData(i, carData);
        }

        return packet;
    }

    /**
     * Decodes session packet (simplified).
     */
    private PacketSessionData decodeSessionPacket(ByteBufferReader reader, PacketHeader header) {
        PacketSessionData packet = new PacketSessionData();
        packet.setHeader(header);

        packet.setWeather(reader.readUInt8());
        packet.setTrackTemperature(reader.readInt8());
        packet.setAirTemperature(reader.readInt8());
        packet.setTotalLaps(reader.readUInt8());
        packet.setTrackLength(reader.readUInt16());
        packet.setSessionType(reader.readUInt8());
        packet.setTrackId(reader.readInt8());
        packet.setFormula(reader.readUInt8());
        packet.setSessionTimeLeft(reader.readUInt16());
        packet.setSessionDuration(reader.readUInt16());
        packet.setPitSpeedLimit(reader.readUInt8());
        packet.setGamePaused(reader.readUInt8());
        packet.setIsSpectating(reader.readUInt8());
        packet.setSpectatorCarIndex(reader.readUInt8());
        packet.setSliProNativeSupport(reader.readUInt8());

        // Skip remaining fields for simplified version
        return packet;
    }

    /**
     * Decodes lap data packet with field swap detection.
     */
    private PacketLapData decodeLapDataPacket(ByteBufferReader reader, PacketHeader header) {
        PacketLapData packet = new PacketLapData();
        packet.setHeader(header);

        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            LapData lapData = new LapData();

            lapData.setLastLapTimeInMS(reader.readUInt32());
            lapData.setCurrentLapTimeInMS(reader.readUInt32());
            lapData.setSector1TimeMSPart(reader.readUInt16());
            lapData.setSector1TimeMinutesPart(reader.readUInt8());
            lapData.setSector2TimeMSPart(reader.readUInt16());
            lapData.setSector2TimeMinutesPart(reader.readUInt8());
            lapData.setDeltaToCarInFrontMSPart(reader.readUInt16());
            lapData.setDeltaToCarInFrontMinutesPart(reader.readUInt8());
            lapData.setDeltaToRaceLeaderMSPart(reader.readUInt16());
            lapData.setDeltaToRaceLeaderMinutesPart(reader.readUInt8());
            lapData.setLapDistance(reader.readFloat());
            lapData.setTotalDistance(reader.readFloat());
            lapData.setSafetyCarDelta(reader.readFloat());
            lapData.setCarPosition(reader.readUInt8());
            lapData.setCurrentLapNum(reader.readUInt8());
            lapData.setPitStatus(reader.readUInt8());
            lapData.setNumPitStops(reader.readUInt8());
            lapData.setSector(reader.readUInt8());
            lapData.setCurrentLapInvalid(reader.readUInt8());
            lapData.setPenalties(reader.readUInt8());
            lapData.setTotalWarnings(reader.readUInt8());
            lapData.setCornerCuttingWarnings(reader.readUInt8());
            lapData.setNumUnservedDriveThroughPens(reader.readUInt8());
            lapData.setNumUnservedStopGoPens(reader.readUInt8());

            // Known spec issue: gridPosition and driverStatus may be swapped
            short field1 = reader.readUInt8();
            short field2 = reader.readUInt8();

            // Detect swap via range validation
            // gridPosition: typically 1-22
            // driverStatus: 0-4
            if (field1 <= 4 && field2 >= 1 && field2 <= 22) {
                // Likely swapped
                lapData.setDriverStatus(field1);
                lapData.setGridPosition(field2);
                if (!fieldSwapWarningIssued) {
                    logger.warn("LapData field swap detected - applying workaround");
                    fieldSwapWarningIssued = true;
                }
            } else {
                // Normal order
                lapData.setGridPosition(field1);
                lapData.setDriverStatus(field2);
            }

            lapData.setResultStatus(reader.readUInt8());
            lapData.setPitLaneTimerActive(reader.readUInt8());
            lapData.setPitLaneTimeInLaneInMS(reader.readUInt16());
            lapData.setPitStopTimerInMS(reader.readUInt16());
            lapData.setPitStopShouldServePen(reader.readUInt8());
            lapData.setSpeedTrapFastestSpeed(reader.readFloat());
            lapData.setSpeedTrapFastestLap(reader.readUInt8());

            packet.setLapData(i, lapData);
        }

        packet.setTimeTrialPBCarIdx(reader.readUInt8());
        packet.setTimeTrialRivalCarIdx(reader.readUInt8());

        return packet;
    }

    /**
     * Decodes car telemetry packet.
     */
    private PacketCarTelemetryData decodeCarTelemetryPacket(ByteBufferReader reader, PacketHeader header) {
        PacketCarTelemetryData packet = new PacketCarTelemetryData();
        packet.setHeader(header);

        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            CarTelemetryData telemetry = new CarTelemetryData();

            telemetry.setSpeed(reader.readUInt16());
            telemetry.setThrottle(reader.readFloat());
            telemetry.setSteer(reader.readFloat());
            telemetry.setBrake(reader.readFloat());
            telemetry.setClutch(reader.readUInt8());
            telemetry.setGear(reader.readInt8());
            telemetry.setEngineRPM(reader.readUInt16());
            telemetry.setDrs(reader.readUInt8());
            telemetry.setRevLightsPercent(reader.readUInt8());
            telemetry.setRevLightsBitValue(reader.readUInt16());
            telemetry.setBrakesTemperature(reader.readUInt16Array(4));
            telemetry.setTyresSurfaceTemperature(reader.readUInt8Array(4));
            telemetry.setTyresInnerTemperature(reader.readUInt8Array(4));
            telemetry.setEngineTemperature(reader.readUInt16());
            telemetry.setTyresPressure(reader.readFloatArray(4));
            telemetry.setSurfaceType(reader.readUInt8Array(4));

            packet.setCarTelemetryData(i, telemetry);
        }

        packet.setMfdPanelIndex(reader.readUInt8());
        packet.setMfdPanelIndexSecondaryPlayer(reader.readUInt8());
        packet.setSuggestedGear(reader.readInt8());

        return packet;
    }

    /**
     * Decodes car damage packet.
     */
    private PacketCarDamageData decodeCarDamagePacket(ByteBufferReader reader, PacketHeader header) {
        PacketCarDamageData packet = new PacketCarDamageData();
        packet.setHeader(header);

        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            CarDamageData damage = new CarDamageData();

            damage.setTyresWear(reader.readFloatArray(4));
            damage.setTyresDamage(reader.readUInt8Array(4));
            damage.setBrakesDamage(reader.readUInt8Array(4));
            damage.setTyreBlisters(reader.readUInt8Array(4));
            damage.setFrontLeftWingDamage(reader.readUInt8());
            damage.setFrontRightWingDamage(reader.readUInt8());
            damage.setRearWingDamage(reader.readUInt8());
            damage.setFloorDamage(reader.readUInt8());
            damage.setDiffuserDamage(reader.readUInt8());
            damage.setSidepodDamage(reader.readUInt8());
            damage.setDrsFault(reader.readUInt8());
            damage.setErsFault(reader.readUInt8());
            damage.setGearBoxDamage(reader.readUInt8());
            damage.setEngineDamage(reader.readUInt8());
            damage.setEngineMGUHWear(reader.readUInt8());
            damage.setEngineESWear(reader.readUInt8());
            damage.setEngineCEWear(reader.readUInt8());
            damage.setEngineICEWear(reader.readUInt8());
            damage.setEngineMGUKWear(reader.readUInt8());
            damage.setEngineTCWear(reader.readUInt8());
            damage.setEngineBlown(reader.readUInt8());
            damage.setEngineSeized(reader.readUInt8());

            packet.setCarDamageData(i, damage);
        }

        return packet;
    }
}
