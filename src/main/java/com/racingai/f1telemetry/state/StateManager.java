package com.racingai.f1telemetry.state;

import com.racingai.f1telemetry.packets.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Manages the live telemetry state by processing incoming packets.
 *
 * Thread-safe class that updates a SessionState instance as packets arrive.
 * Merges data from different packet types (Motion, Lap, Telemetry, Damage)
 * into a unified state model.
 */
public class StateManager {

    private static final Logger logger = LoggerFactory.getLogger(StateManager.class);

    private final SessionState sessionState;

    public StateManager() {
        this.sessionState = new SessionState();
    }

    /**
     * Process a decoded packet and update the session state.
     *
     * @param packet The decoded packet (Motion, Lap, Telemetry, or Damage)
     */
    public synchronized void processPacket(Object packet) {
        if (packet == null) {
            return;
        }

        if (packet instanceof PacketMotionData) {
            processMotionPacket((PacketMotionData) packet);
        } else if (packet instanceof PacketLapData) {
            processLapDataPacket((PacketLapData) packet);
        } else if (packet instanceof PacketCarTelemetryData) {
            processTelemetryPacket((PacketCarTelemetryData) packet);
        } else if (packet instanceof PacketCarDamageData) {
            processDamagePacket((PacketCarDamageData) packet);
        } else if (packet instanceof PacketSessionData) {
            processSessionPacket((PacketSessionData) packet);
        }
    }

    private void processMotionPacket(PacketMotionData packet) {
        // Update session metadata
        PacketHeader header = packet.getHeader();
        sessionState.updateSessionMetadata(
            header.getSessionUID(),
            header.getSessionTime(),
            header.getFrameIdentifier(),
            header.getPlayerCarIndex()
        );

        // Update motion data for all cars
        CarMotionData[] motionData = packet.getCarMotionData();
        for (int i = 0; i < motionData.length; i++) {
            CarMotionData motion = motionData[i];
            CarState car = sessionState.getCar(i);
            if (car != null) {
                car.updateMotion(
                    motion.getWorldPositionX(),
                    motion.getWorldPositionY(),
                    motion.getWorldPositionZ(),
                    motion.getWorldVelocityX(),
                    motion.getWorldVelocityY(),
                    motion.getWorldVelocityZ(),
                    motion.getgForceLateral(),
                    motion.getgForceLongitudinal(),
                    motion.getgForceVertical()
                );
            }
        }
    }

    private void processLapDataPacket(PacketLapData packet) {
        // Update session metadata
        PacketHeader header = packet.getHeader();
        sessionState.updateSessionMetadata(
            header.getSessionUID(),
            header.getSessionTime(),
            header.getFrameIdentifier(),
            header.getPlayerCarIndex()
        );

        // Update lap data for all cars
        LapData[] lapData = packet.getLapData();
        for (int i = 0; i < lapData.length; i++) {
            LapData lap = lapData[i];
            CarState car = sessionState.getCar(i);
            if (car != null) {
                car.updateLapData(
                    lap.getLastLapTimeInMS(),
                    lap.getCurrentLapTimeInMS(),
                    lap.getLapDistance(),
                    lap.getTotalDistance(),
                    lap.getCarPosition(),
                    lap.getCurrentLapNum(),
                    lap.getGridPosition(),
                    lap.getDriverStatus(),
                    lap.getDeltaToRaceLeaderSeconds()
                );
            }
        }
    }

    private void processTelemetryPacket(PacketCarTelemetryData packet) {
        // Update session metadata
        PacketHeader header = packet.getHeader();
        sessionState.updateSessionMetadata(
            header.getSessionUID(),
            header.getSessionTime(),
            header.getFrameIdentifier(),
            header.getPlayerCarIndex()
        );

        // Update telemetry data for all cars
        CarTelemetryData[] telemetryData = packet.getCarTelemetryData();
        for (int i = 0; i < telemetryData.length; i++) {
            CarTelemetryData telemetry = telemetryData[i];
            CarState car = sessionState.getCar(i);
            if (car != null) {
                car.updateTelemetry(
                    telemetry.getSpeed(),
                    telemetry.getGear(),
                    telemetry.getThrottle(),
                    telemetry.getSteer(),
                    telemetry.getBrake(),
                    telemetry.getEngineRPM(),
                    telemetry.getEngineTemperature(),
                    telemetry.getTyresPressure()
                );
            }
        }
    }

    private void processDamagePacket(PacketCarDamageData packet) {
        // Update session metadata
        PacketHeader header = packet.getHeader();
        sessionState.updateSessionMetadata(
            header.getSessionUID(),
            header.getSessionTime(),
            header.getFrameIdentifier(),
            header.getPlayerCarIndex()
        );

        // Update damage data for all cars
        CarDamageData[] damageData = packet.getCarDamageData();
        for (int i = 0; i < damageData.length; i++) {
            CarDamageData damage = damageData[i];
            CarState car = sessionState.getCar(i);
            if (car != null) {
                car.updateDamage(
                    damage.getTyresWear(),
                    damage.getFrontLeftWingDamage(),
                    damage.getFrontRightWingDamage(),
                    damage.getRearWingDamage()
                );
            }
        }
    }

    private void processSessionPacket(PacketSessionData packet) {
        // Update session metadata
        PacketHeader header = packet.getHeader();
        sessionState.updateSessionMetadata(
            header.getSessionUID(),
            header.getSessionTime(),
            header.getFrameIdentifier(),
            header.getPlayerCarIndex()
        );
        // Session-specific data can be added to SessionState in future if needed
    }

    /**
     * Get the current session state.
     *
     * @return The current SessionState
     */
    public SessionState getSessionState() {
        return sessionState;
    }
}
