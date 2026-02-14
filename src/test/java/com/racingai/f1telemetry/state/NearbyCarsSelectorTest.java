package com.racingai.f1telemetry.state;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Test for NearbyCarsSelector.
 */
public class NearbyCarsSelectorTest {

    @Test
    public void testSelectNearbyCars_BasicSelection() {
        SessionState state = createTestSession();
        NearbyCarsSelector selector = new NearbyCarsSelector();

        // Set player at position 5 with delta = 5.0s
        CarState player = state.getCar(4); // index 4 = position 5
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 5, (short) 3, (short) 5, (short) 4, 5.0);

        // Set cars around player
        setupCar(state.getCar(0), 1, 0.0, true);  // P1: Leader, gap = -5.0s (ahead, outside 1.5s)
        setupCar(state.getCar(1), 2, 3.0, true);  // P2: gap = -2.0s (ahead, outside 1.5s)
        setupCar(state.getCar(2), 3, 4.2, true);  // P3: gap = -0.8s (ahead, within 1.5s)
        setupCar(state.getCar(3), 4, 4.7, true);  // P4: gap = -0.3s (ahead, within 1.5s)
        setupCar(state.getCar(5), 6, 5.5, true);  // P6: gap = +0.5s (behind, within 1.5s)
        setupCar(state.getCar(6), 7, 6.2, true);  // P7: gap = +1.2s (behind, within 1.5s)
        setupCar(state.getCar(7), 8, 7.5, true);  // P8: gap = +2.5s (behind, outside 1.5s)

        List<CarState> nearby = selector.selectNearbyCars(state);

        // Should select 4 cars within 1.5s: P3, P4 ahead, P6, P7 behind
        assertEquals(4, nearby.size(), "Should select 4 nearby cars");

        // Verify cars are correct
        assertEquals(2, nearby.get(0).getCarIndex(), "First should be P3 (index 2)");
        assertEquals(3, nearby.get(1).getCarIndex(), "Second should be P4 (index 3)");
        assertEquals(5, nearby.get(2).getCarIndex(), "Third should be P6 (index 5)");
        assertEquals(6, nearby.get(3).getCarIndex(), "Fourth should be P7 (index 6)");
    }

    @Test
    public void testSelectNearbyCars_PreferAhead() {
        SessionState state = createTestSession();
        state.updateSessionMetadata(12345L, 10.0f, 300L, (short) 5); // Set player index to 5
        NearbyCarsSelector selector = new NearbyCarsSelector();

        CarState player = state.getCar(5); // P6
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 6, (short) 3, (short) 6, (short) 4, 10.0);

        // 5 cars ahead within range
        setupCar(state.getCar(0), 1, 9.0, true);  // gap = -1.0s
        setupCar(state.getCar(1), 2, 9.2, true);  // gap = -0.8s
        setupCar(state.getCar(2), 3, 9.4, true);  // gap = -0.6s
        setupCar(state.getCar(3), 4, 9.6, true);  // gap = -0.4s
        setupCar(state.getCar(4), 5, 9.8, true);  // gap = -0.2s

        // 3 cars behind within range
        setupCar(state.getCar(6), 7, 10.5, true); // gap = +0.5s
        setupCar(state.getCar(7), 8, 11.0, true); // gap = +1.0s
        setupCar(state.getCar(8), 9, 11.3, true); // gap = +1.3s

        List<CarState> nearby = selector.selectNearbyCars(state);

        // Should select 4 ahead + 2 behind = 6 total
        assertEquals(6, nearby.size(), "Should select 6 cars");

        // First 4 should be ahead
        for (int i = 0; i < 4; i++) {
            assertTrue(nearby.get(i).getCarPosition() < 6,
                "First 4 should be ahead of player");
        }

        // Last 2 should be behind
        for (int i = 4; i < 6; i++) {
            assertTrue(nearby.get(i).getCarPosition() > 6,
                "Last 2 should be behind player");
        }
    }

    @Test
    public void testSelectNearbyCars_OnlyInactiveCars() {
        SessionState state = createTestSession();
        NearbyCarsSelector selector = new NearbyCarsSelector();

        CarState player = state.getCar(0);
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 1, (short) 3, (short) 1, (short) 4, 0.0);

        // All other cars inactive
        for (int i = 1; i < 22; i++) {
            setupCar(state.getCar(i), i + 1, i * 0.5, false);
        }

        List<CarState> nearby = selector.selectNearbyCars(state);

        assertEquals(0, nearby.size(), "Should return empty list when all cars inactive");
    }

    @Test
    public void testSelectNearbyCars_InactivePlayer() {
        SessionState state = createTestSession();
        NearbyCarsSelector selector = new NearbyCarsSelector();

        CarState player = state.getCar(0);
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 1, (short) 3, (short) 1, (short) 0, 0.0); // driverStatus = 0 (inactive)

        List<CarState> nearby = selector.selectNearbyCars(state);

        assertEquals(0, nearby.size(), "Should return empty list when player is inactive");
    }

    @Test
    public void testSelectNearbyCars_FewCarsAvailable() {
        SessionState state = createTestSession();
        state.updateSessionMetadata(12345L, 10.0f, 300L, (short) 0); // Set player index to 0
        NearbyCarsSelector selector = new NearbyCarsSelector();

        CarState player = state.getCar(0);
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 1, (short) 3, (short) 1, (short) 4, 0.0);

        // Only 2 cars within range
        setupCar(state.getCar(1), 2, 0.5, true);  // gap = +0.5s
        setupCar(state.getCar(2), 3, 1.2, true);  // gap = +1.2s

        List<CarState> nearby = selector.selectNearbyCars(state);

        assertEquals(2, nearby.size(), "Should return 2 cars when only 2 available");
    }

    @Test
    public void testCalculateGap() {
        CarState player = new CarState(0);
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 5, (short) 3, (short) 5, (short) 4, 10.0);

        CarState ahead = new CarState(1);
        ahead.updateLapData(90000L, 30000L, 1600.0f, 5000.0f,
            (short) 4, (short) 3, (short) 4, (short) 4, 8.5);

        CarState behind = new CarState(2);
        behind.updateLapData(90000L, 30000L, 1400.0f, 5000.0f,
            (short) 6, (short) 3, (short) 6, (short) 4, 11.5);

        double gapAhead = NearbyCarsSelector.calculateGap(player, ahead);
        double gapBehind = NearbyCarsSelector.calculateGap(player, behind);

        assertEquals(-1.5, gapAhead, 0.01, "Car ahead should have negative gap");
        assertEquals(1.5, gapBehind, 0.01, "Car behind should have positive gap");
    }

    @Test
    public void testCustomConfiguration() {
        SessionState state = createTestSession();
        state.updateSessionMetadata(12345L, 10.0f, 300L, (short) 10); // Set player index to 10
        // Custom: 3.0s gap, max 4 cars, 3 ahead, 1 behind
        NearbyCarsSelector selector = new NearbyCarsSelector(3.0, 4, 3, 1);

        CarState player = state.getCar(10);
        player.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) 11, (short) 3, (short) 11, (short) 4, 20.0);

        // Setup cars with larger gaps
        setupCar(state.getCar(0), 1, 17.5, true);  // gap = -2.5s (within 3.0s)
        setupCar(state.getCar(1), 2, 18.0, true);  // gap = -2.0s
        setupCar(state.getCar(2), 3, 19.0, true);  // gap = -1.0s
        setupCar(state.getCar(3), 4, 19.5, true);  // gap = -0.5s
        setupCar(state.getCar(11), 12, 21.0, true); // gap = +1.0s
        setupCar(state.getCar(12), 13, 22.0, true); // gap = +2.0s

        List<CarState> nearby = selector.selectNearbyCars(state);

        assertEquals(4, nearby.size(), "Should respect max cars = 4");

        // Should have 3 ahead, 1 behind
        int aheadCount = 0;
        int behindCount = 0;
        for (CarState car : nearby) {
            if (car.getCarPosition() < 11) {
                aheadCount++;
            } else {
                behindCount++;
            }
        }

        assertEquals(3, aheadCount, "Should have 3 cars ahead");
        assertEquals(1, behindCount, "Should have 1 car behind");
    }

    // Helper methods

    private SessionState createTestSession() {
        SessionState state = new SessionState();
        state.updateSessionMetadata(12345L, 10.0f, 300L, (short) 4);
        return state;
    }

    private void setupCar(CarState car, int position, double deltaToLeader, boolean active) {
        car.updateLapData(90000L, 30000L, 1500.0f, 5000.0f,
            (short) position, (short) 3, (short) position,
            (short) (active ? 4 : 0), deltaToLeader);
    }
}
