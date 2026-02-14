package com.racingai.f1telemetry.state;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Selects nearby cars based on time gap to the player.
 *
 * This class implements the logic to identify cars that are racing close
 * to the player, useful for providing situational awareness.
 *
 * Selection criteria:
 * - Cars must be active (on track)
 * - Within configured time gap (default 1.5 seconds)
 * - Prefer cars ahead of player (e.g., 4 ahead, 2 behind)
 * - Maximum of 6 cars total
 */
public class NearbyCarsSelector {

    private final double maxTimeGapSeconds;
    private final int maxNearbyCars;
    private final int preferAheadCount;
    private final int preferBehindCount;

    /**
     * Create a nearby cars selector with default settings.
     * - Max time gap: 1.5 seconds
     * - Max cars: 6 (4 ahead, 2 behind)
     */
    public NearbyCarsSelector() {
        this(1.5, 6, 4, 2);
    }

    /**
     * Create a nearby cars selector with custom settings.
     *
     * @param maxTimeGapSeconds Maximum time gap to consider a car "nearby"
     * @param maxNearbyCars Maximum total nearby cars to return
     * @param preferAheadCount Preferred number of cars ahead
     * @param preferBehindCount Preferred number of cars behind
     */
    public NearbyCarsSelector(double maxTimeGapSeconds, int maxNearbyCars,
                             int preferAheadCount, int preferBehindCount) {
        this.maxTimeGapSeconds = maxTimeGapSeconds;
        this.maxNearbyCars = maxNearbyCars;
        this.preferAheadCount = preferAheadCount;
        this.preferBehindCount = preferBehindCount;
    }

    /**
     * Select nearby cars for the player.
     *
     * @param sessionState The current session state
     * @return List of nearby cars, sorted by position (ahead first, then behind)
     */
    public List<CarState> selectNearbyCars(SessionState sessionState) {
        CarState player = sessionState.getPlayerCar();
        if (player == null || !player.isActive()) {
            return new ArrayList<>();
        }

        double playerDelta = player.getDeltaToRaceLeaderSeconds();
        List<CarState> carsAhead = new ArrayList<>();
        List<CarState> carsBehind = new ArrayList<>();

        // Find all nearby cars
        for (CarState car : sessionState.getAllCars()) {
            if (car.getCarIndex() == player.getCarIndex()) {
                continue; // Skip player
            }

            if (!car.isActive()) {
                continue; // Skip inactive cars
            }

            double carDelta = car.getDeltaToRaceLeaderSeconds();
            double gapToPlayer = carDelta - playerDelta;

            // Check if within time gap
            if (Math.abs(gapToPlayer) <= maxTimeGapSeconds) {
                if (gapToPlayer < 0) {
                    // Car is ahead (closer to leader = smaller delta)
                    carsAhead.add(car);
                } else {
                    // Car is behind
                    carsBehind.add(car);
                }
            }
        }

        // Sort cars ahead by delta (closest to leader first)
        carsAhead.sort(Comparator.comparingDouble(CarState::getDeltaToRaceLeaderSeconds));

        // Sort cars behind by delta (closest to player first)
        carsBehind.sort(Comparator.comparingDouble(CarState::getDeltaToRaceLeaderSeconds));

        // Select preferred counts
        List<CarState> result = new ArrayList<>();

        int aheadCount = Math.min(preferAheadCount, carsAhead.size());
        int behindCount = Math.min(preferBehindCount, carsBehind.size());

        // Adjust if we have fewer than maxNearbyCars
        int totalAvailable = carsAhead.size() + carsBehind.size();
        if (aheadCount + behindCount < maxNearbyCars && totalAvailable > 0) {
            // Fill remaining slots
            int remaining = maxNearbyCars - (aheadCount + behindCount);

            // Add more from ahead if available
            int additionalAhead = Math.min(remaining, carsAhead.size() - aheadCount);
            aheadCount += additionalAhead;
            remaining -= additionalAhead;

            // Add more from behind if still have slots
            if (remaining > 0) {
                int additionalBehind = Math.min(remaining, carsBehind.size() - behindCount);
                behindCount += additionalBehind;
            }
        }

        // Add selected cars (ahead first, then behind)
        for (int i = 0; i < aheadCount; i++) {
            result.add(carsAhead.get(i));
        }
        for (int i = 0; i < behindCount; i++) {
            result.add(carsBehind.get(i));
        }

        return result;
    }

    /**
     * Calculate time gap between player and another car.
     *
     * @param player Player car state
     * @param other Other car state
     * @return Time gap in seconds (positive = other is behind, negative = other is ahead)
     */
    public static double calculateGap(CarState player, CarState other) {
        return other.getDeltaToRaceLeaderSeconds() - player.getDeltaToRaceLeaderSeconds();
    }
}
