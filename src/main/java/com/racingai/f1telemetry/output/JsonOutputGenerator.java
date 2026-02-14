package com.racingai.f1telemetry.output;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.racingai.f1telemetry.state.CarState;
import com.racingai.f1telemetry.state.NearbyCarsSelector;
import com.racingai.f1telemetry.state.SessionState;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * Generates JSON telemetry snapshots from session state.
 *
 * Outputs newline-delimited JSON (JSONL) containing:
 * - Player inputs (steering, throttle, brake, gear, speed)
 * - Player position and lap distance
 * - Nearby cars (up to 6 within 1.5s)
 * - Tyre wear data
 * - Session metadata
 */
public class JsonOutputGenerator {

    private static final Logger logger = LoggerFactory.getLogger(JsonOutputGenerator.class);

    private final ObjectMapper objectMapper;
    private final NearbyCarsSelector nearbyCarsSelector;

    public JsonOutputGenerator(NearbyCarsSelector nearbyCarsSelector) {
        this.objectMapper = new ObjectMapper();
        this.nearbyCarsSelector = nearbyCarsSelector;
    }

    /**
     * Generate a JSON telemetry snapshot from the current session state.
     *
     * @param sessionState The current session state
     * @return JSON string, or null if player car not available
     */
    public String generateSnapshot(SessionState sessionState) {
        CarState playerCar = sessionState.getPlayerCar();
        if (playerCar == null || !playerCar.isActive()) {
            return null;
        }

        try {
            // Build telemetry snapshot
            TelemetrySnapshot snapshot = new TelemetrySnapshot();
            snapshot.setTimestamp(System.currentTimeMillis());
            snapshot.setSessionTime(sessionState.getSessionTime());
            snapshot.setFrameId(sessionState.getFrameIdentifier());

            // Meta data (track ID)
            MetaData meta = buildMetaData(sessionState);
            snapshot.setMeta(meta);

            // Player data
            PlayerData player = buildPlayerData(playerCar);
            snapshot.setPlayer(player);

            // Nearby cars
            List<CarState> nearbyCars = nearbyCarsSelector.selectNearbyCars(sessionState);
            List<NearbyCarData> nearbyCarDataList = buildNearbyCarData(playerCar, nearbyCars);
            snapshot.setNearbyCars(nearbyCarDataList);

            // Serialize to JSON
            return objectMapper.writeValueAsString(snapshot);

        } catch (JsonProcessingException e) {
            logger.error("Failed to serialize telemetry snapshot: {}", e.getMessage());
            return null;
        }
    }

    /**
     * Build meta data from session state.
     */
    private MetaData buildMetaData(SessionState sessionState) {
        Byte trackId = sessionState.getTrackId();
        return new MetaData(trackId != null ? trackId.intValue() : null);
    }

    /**
     * Build player data from car state.
     */
    private PlayerData buildPlayerData(CarState playerCar) {
        PlayerData player = new PlayerData();
        player.setPosition(playerCar.getCarPosition());
        player.setLapNumber(playerCar.getCurrentLapNum());
        player.setLapDistance(playerCar.getLapDistance());
        player.setSpeed(playerCar.getSpeed());
        player.setGear(playerCar.getGear());
        player.setThrottle(playerCar.getThrottle());
        player.setBrake(playerCar.getBrake());
        player.setSteering(playerCar.getSteer());

        // Tyre wear
        float[] tyreWear = playerCar.getTyresWear();
        TyreWearData tyreWearData = new TyreWearData(
            tyreWear[0], // RL
            tyreWear[1], // RR
            tyreWear[2], // FL
            tyreWear[3]  // FR
        );
        player.setTyreWear(tyreWearData);

        return player;
    }

    /**
     * Build nearby car data list.
     */
    private List<NearbyCarData> buildNearbyCarData(CarState playerCar, List<CarState> nearbyCars) {
        List<NearbyCarData> nearbyCarDataList = new ArrayList<>();

        for (CarState car : nearbyCars) {
            double gap = NearbyCarsSelector.calculateGap(playerCar, car);
            WorldPosition worldPos = new WorldPosition(
                car.getWorldPositionX(),
                car.getWorldPositionY(),
                car.getWorldPositionZ()
            );
            NearbyCarData nearbyCarData = new NearbyCarData(
                car.getCarIndex(),
                car.getCarPosition(),
                gap,
                worldPos
            );
            nearbyCarDataList.add(nearbyCarData);
        }

        return nearbyCarDataList;
    }
}
