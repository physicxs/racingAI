package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.racingai.f1telemetry.state.CarState;
import com.racingai.f1telemetry.state.NearbyCarsSelector;
import com.racingai.f1telemetry.state.SessionState;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for JsonOutputGenerator.
 */
public class JsonOutputGeneratorTest {

    private JsonOutputGenerator generator;
    private SessionState sessionState;
    private ObjectMapper objectMapper;

    @BeforeEach
    public void setUp() {
        NearbyCarsSelector selector = new NearbyCarsSelector();
        generator = new JsonOutputGenerator(selector);
        sessionState = new SessionState();
        objectMapper = new ObjectMapper();
    }

    @Test
    public void testGenerateSnapshotWithActivePlayer() throws Exception {
        // Set up session state with player car
        sessionState.updateSessionMetadata(123456789L, 100.5f, 5000L, (short) 0);

        CarState playerCar = sessionState.getCar(0);

        // Update player car with lap data (make active)
        playerCar.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
                               (short) 5, (short) 3, (short) 5, (short) 4, 10.5);

        // Update player car with telemetry
        playerCar.updateTelemetry(287, (short) 7, 0.85f, -0.15f, 0.0f,
                                 12000, 90, new float[]{23.5f, 23.6f, 23.4f, 23.5f});

        // Update player car with damage (tyre wear)
        playerCar.updateDamage(new float[]{10.5f, 11.2f, 8.3f, 9.1f}, 0.0f, 0.0f, 0.0f);

        // Add another car nearby
        CarState otherCar = sessionState.getCar(1);
        otherCar.updateLapData(89000L, 30000L, 1400.0f, 4900.0f,
                              (short) 4, (short) 3, (short) 4, (short) 4, 9.0);

        // Generate JSON
        String json = generator.generateSnapshot(sessionState);

        assertNotNull(json, "JSON should be generated for active player");

        // Parse and verify JSON structure
        JsonNode root = objectMapper.readTree(json);

        assertTrue(root.has("timestamp"), "Should have timestamp");
        assertTrue(root.has("sessionTime"), "Should have sessionTime");
        assertTrue(root.has("frameId"), "Should have frameId");
        assertTrue(root.has("player"), "Should have player");
        assertTrue(root.has("nearbyCars"), "Should have nearbyCars");

        // Verify session metadata
        assertEquals(100.5f, root.get("sessionTime").floatValue(), 0.01f);
        assertEquals(5000L, root.get("frameId").longValue());

        // Verify player data
        JsonNode player = root.get("player");
        assertEquals(5, player.get("position").intValue());
        assertEquals(3, player.get("lapNumber").intValue());
        assertEquals(1500.0f, player.get("lapDistance").floatValue(), 0.01f);
        assertEquals(287, player.get("speed").intValue());
        assertEquals(7, player.get("gear").intValue());
        assertEquals(0.85f, player.get("throttle").floatValue(), 0.01f);
        assertEquals(0.0f, player.get("brake").floatValue(), 0.01f);
        assertEquals(-0.15f, player.get("steering").floatValue(), 0.01f);

        // Verify tyre wear
        JsonNode tyreWear = player.get("tyreWear");
        assertNotNull(tyreWear, "Should have tyre wear data");
        assertEquals(10.5f, tyreWear.get("rearLeft").floatValue(), 0.01f);
        assertEquals(11.2f, tyreWear.get("rearRight").floatValue(), 0.01f);
        assertEquals(8.3f, tyreWear.get("frontLeft").floatValue(), 0.01f);
        assertEquals(9.1f, tyreWear.get("frontRight").floatValue(), 0.01f);

        // Verify nearby cars
        JsonNode nearbyCars = root.get("nearbyCars");
        assertTrue(nearbyCars.isArray(), "Nearby cars should be an array");
        assertEquals(1, nearbyCars.size(), "Should have 1 nearby car");

        JsonNode nearbyCarData = nearbyCars.get(0);
        assertEquals(1, nearbyCarData.get("carIndex").intValue());
        assertEquals(4, nearbyCarData.get("position").intValue());
        // Gap should be negative (car is ahead)
        assertTrue(nearbyCarData.get("gap").doubleValue() < 0, "Car ahead should have negative gap");
    }

    @Test
    public void testGenerateSnapshotWithInactivePlayer() {
        // Set up session state with inactive player
        sessionState.updateSessionMetadata(123456789L, 100.5f, 5000L, (short) 0);

        CarState playerCar = sessionState.getCar(0);

        // Update player car with lap data (inactive - status 0)
        playerCar.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
                               (short) 5, (short) 3, (short) 5, (short) 0, 10.5);

        // Generate JSON
        String json = generator.generateSnapshot(sessionState);

        assertNull(json, "JSON should be null for inactive player");
    }

    @Test
    public void testGenerateSnapshotWithNoNearbyCars() throws Exception {
        // Set up session state with player car only
        sessionState.updateSessionMetadata(123456789L, 100.5f, 5000L, (short) 0);

        CarState playerCar = sessionState.getCar(0);

        // Update player car (make active)
        playerCar.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
                               (short) 1, (short) 3, (short) 1, (short) 4, 0.0);
        playerCar.updateTelemetry(200, (short) 5, 0.5f, 0.0f, 0.0f,
                                 10000, 80, new float[]{23.0f, 23.0f, 23.0f, 23.0f});
        playerCar.updateDamage(new float[]{0.0f, 0.0f, 0.0f, 0.0f}, 0.0f, 0.0f, 0.0f);

        // Generate JSON
        String json = generator.generateSnapshot(sessionState);

        assertNotNull(json, "JSON should be generated");

        JsonNode root = objectMapper.readTree(json);
        JsonNode nearbyCars = root.get("nearbyCars");
        assertTrue(nearbyCars.isArray(), "Nearby cars should be an array");
        assertEquals(0, nearbyCars.size(), "Should have 0 nearby cars");
    }
}
