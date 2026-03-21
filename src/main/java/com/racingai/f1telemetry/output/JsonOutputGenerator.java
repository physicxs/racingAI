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

            // All cars (for track map)
            List<RaceCarData> allCarsList = buildAllCarsData(sessionState, playerCar);
            snapshot.setAllCars(allCarsList);

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
        Integer trackLength = sessionState.getTrackLength();
        MetaData meta = new MetaData(trackId != null ? trackId.intValue() : null, trackLength);

        Short sc = sessionState.getSafetyCarStatus();
        if (sc != null) meta.setSafetyCarStatus(sc.intValue());
        Short w = sessionState.getWeather();
        if (w != null) meta.setWeather(w.intValue());
        Byte tt = sessionState.getTrackTemperature();
        if (tt != null) meta.setTrackTemperature(tt.intValue());
        Byte at = sessionState.getAirTemperature();
        if (at != null) meta.setAirTemperature(at.intValue());
        Short tl = sessionState.getTotalLaps();
        if (tl != null) meta.setTotalLaps(tl.intValue());

        return meta;
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

        // World position
        WorldPosition worldPos = new WorldPosition(
            playerCar.getWorldPositionX(),
            playerCar.getWorldPositionY(),
            playerCar.getWorldPositionZ()
        );
        player.setWorldPosM(worldPos);

        // Orientation
        player.setYaw(playerCar.getYaw());
        player.setPitch(playerCar.getPitch());
        player.setRoll(playerCar.getRoll());

        // G-forces
        player.setGForceLateral(playerCar.getGForceLateral());
        player.setGForceLongitudinal(playerCar.getGForceLongitudinal());

        // DRS
        player.setDrs(playerCar.getDrs());
        player.setDrsAllowed(playerCar.getDrsAllowed());

        // ERS
        player.setErsDeployMode(playerCar.getErsDeployMode());
        player.setErsStoreEnergy(playerCar.getErsStoreEnergy());
        player.setErsDeployedThisLap(playerCar.getErsDeployedThisLap());
        player.setErsHarvestedThisLapMGUK(playerCar.getErsHarvestedThisLapMGUK());
        player.setErsHarvestedThisLapMGUH(playerCar.getErsHarvestedThisLapMGUH());

        // Tyre temps (convert short[] to int[])
        short[] surfTemp = playerCar.getTyresSurfaceTemperature();
        player.setTyreSurfaceTemp(new int[]{surfTemp[0], surfTemp[1], surfTemp[2], surfTemp[3]});
        short[] innerTemp = playerCar.getTyresInnerTemperature();
        player.setTyreInnerTemp(new int[]{innerTemp[0], innerTemp[1], innerTemp[2], innerTemp[3]});

        // Tyre compound
        player.setTyreCompound(playerCar.getActualTyreCompound());
        player.setTyreCompoundVisual(playerCar.getVisualTyreCompound());
        player.setTyresAgeLaps(playerCar.getTyresAgeLaps());

        // Tyre damage
        short[] tyreDmg = playerCar.getTyresDamage();
        player.setTyreDamage(new int[]{tyreDmg[0], tyreDmg[1], tyreDmg[2], tyreDmg[3]});

        // Brake temps
        int[] brakeTemp = playerCar.getBrakesTemperature();
        player.setBrakeTemp(brakeTemp.clone());

        // Damage
        player.setFrontLeftWingDamage(playerCar.getFrontLeftWingDamage());
        player.setFrontRightWingDamage(playerCar.getFrontRightWingDamage());
        player.setRearWingDamage(playerCar.getRearWingDamage());
        player.setFloorDamage(playerCar.getFloorDamage());
        player.setDiffuserDamage(playerCar.getDiffuserDamage());
        player.setSidepodDamage(playerCar.getSidepodDamage());

        // FIA flags
        player.setVehicleFiaFlags(playerCar.getVehicleFiaFlags());

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

    /**
     * Build data for all active cars (for track map placement).
     */
    private List<RaceCarData> buildAllCarsData(SessionState sessionState, CarState playerCar) {
        List<RaceCarData> allCars = new ArrayList<>();
        CarState[] cars = sessionState.getAllCars();

        for (CarState car : cars) {
            if (car == null || car.getCarPosition() <= 0) {
                continue;
            }
            // Skip the player car (already shown separately)
            if (car.getCarIndex() == playerCar.getCarIndex()) {
                continue;
            }
            allCars.add(new RaceCarData(
                car.getCarIndex(),
                car.getCarPosition(),
                car.getLapDistance(),
                car.getCurrentLapNum(),
                new WorldPosition(
                    car.getWorldPositionX(),
                    car.getWorldPositionY(),
                    car.getWorldPositionZ()
                )
            ));
        }

        return allCars;
    }
}
