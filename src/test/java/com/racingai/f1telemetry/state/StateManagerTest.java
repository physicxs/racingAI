package com.racingai.f1telemetry.state;

import com.racingai.f1telemetry.packets.*;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test for StateManager.
 */
public class StateManagerTest {

    @Test
    public void testStateManagerCreation() {
        StateManager manager = new StateManager();
        assertNotNull(manager, "StateManager should be created");
        assertNotNull(manager.getSessionState(), "SessionState should be initialized");
    }

    @Test
    public void testProcessNullPacket() {
        StateManager manager = new StateManager();
        // Should not throw exception
        manager.processPacket(null);
    }

    @Test
    public void testMotionPacketUpdatesState() {
        StateManager manager = new StateManager();
        SessionState state = manager.getSessionState();

        // Create a motion packet
        PacketHeader header = createHeader((short) 0, 100L, 1.0f);
        CarMotionData[] motionData = new CarMotionData[22];
        for (int i = 0; i < 22; i++) {
            CarMotionData motion = new CarMotionData();
            motion.setWorldPositionX(100.0f + i);
            motion.setWorldPositionY(0.0f);
            motion.setWorldPositionZ(200.0f + i);
            motion.setWorldVelocityX(50.0f);
            motion.setWorldVelocityY(0.0f);
            motion.setWorldVelocityZ(70.0f);
            motion.setgForceLateral(0.5f);
            motion.setgForceLongitudinal(1.2f);
            motion.setgForceVertical(-0.3f);
            motionData[i] = motion;
        }

        PacketMotionData packet = new PacketMotionData();
        packet.setHeader(header);
        packet.setCarMotionData(motionData);

        // Process the packet
        manager.processPacket(packet);

        // Verify state was updated
        assertEquals(100L, state.getFrameIdentifier(), "Frame ID should be updated");
        assertEquals(1.0f, state.getSessionTime(), "Session time should be updated");

        // Verify car state was updated
        CarState car0 = state.getCar(0);
        assertNotNull(car0, "Car 0 should exist");
        assertEquals(100.0f, car0.getWorldPositionX(), 0.01f, "Car 0 position X should be updated");
        assertEquals(0.5f, car0.getGForceLateral(), 0.01f, "Car 0 G-force lateral should be updated");
    }

    @Test
    public void testLapDataPacketUpdatesState() {
        StateManager manager = new StateManager();
        SessionState state = manager.getSessionState();

        // Create a lap data packet
        PacketHeader header = createHeader((short) 0, 200L, 2.0f);
        LapData[] lapData = new LapData[22];
        for (int i = 0; i < 22; i++) {
            LapData lap = new LapData();
            lap.setLastLapTimeInMS(90000L + i * 1000);
            lap.setCurrentLapTimeInMS(30000L);
            lap.setLapDistance(1500.0f + i * 100);
            lap.setTotalDistance(5000.0f);
            lap.setCarPosition((short) (i + 1));
            lap.setCurrentLapNum((short) 5);
            lap.setGridPosition((short) (i + 1));
            lap.setDriverStatus((short) 4); // on track
            lapData[i] = lap;
        }

        PacketLapData packet = new PacketLapData();
        packet.setHeader(header);
        packet.setLapData(lapData);

        // Process the packet
        manager.processPacket(packet);

        // Verify state was updated
        CarState car0 = state.getCar(0);
        assertNotNull(car0, "Car 0 should exist");
        assertEquals(90000L, car0.getLastLapTimeInMS(), "Car 0 last lap time should be updated");
        assertEquals(1, car0.getCarPosition(), "Car 0 position should be updated");
        assertEquals(5, car0.getCurrentLapNum(), "Car 0 lap number should be updated");
        assertTrue(car0.isActive(), "Car 0 should be active");
    }

    @Test
    public void testTelemetryPacketUpdatesState() {
        StateManager manager = new StateManager();
        SessionState state = manager.getSessionState();

        // Create a telemetry packet
        PacketHeader header = createHeader((short) 0, 300L, 3.0f);
        CarTelemetryData[] telemetryData = new CarTelemetryData[22];
        for (int i = 0; i < 22; i++) {
            CarTelemetryData telemetry = new CarTelemetryData();
            telemetry.setSpeed(250 + i * 5);
            telemetry.setGear((byte) 7);
            telemetry.setThrottle(0.8f);
            telemetry.setBrake(0.0f);
            telemetry.setEngineRPM(12000);
            telemetryData[i] = telemetry;
        }

        PacketCarTelemetryData packet = new PacketCarTelemetryData();
        packet.setHeader(header);
        packet.setCarTelemetryData(telemetryData);

        // Process the packet
        manager.processPacket(packet);

        // Verify state was updated
        CarState car0 = state.getCar(0);
        assertNotNull(car0, "Car 0 should exist");
        assertEquals(250, car0.getSpeed(), "Car 0 speed should be updated");
        assertEquals(7, car0.getGear(), "Car 0 gear should be updated");
        assertEquals(0.8f, car0.getThrottle(), 0.01f, "Car 0 throttle should be updated");
    }

    private PacketHeader createHeader(short playerIndex, long frameId, float sessionTime) {
        PacketHeader header = new PacketHeader();
        header.setPlayerCarIndex(playerIndex);
        header.setFrameIdentifier(frameId);
        header.setSessionTime(sessionTime);
        header.setSessionUID(123456789L);
        return header;
    }
}
