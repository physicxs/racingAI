package com.racingai.f1telemetry.state;

import com.racingai.f1telemetry.packets.PacketConstants;

/**
 * Represents the complete session state including all cars.
 *
 * This class maintains a thread-safe snapshot of the current racing state,
 * updated as UDP packets arrive.
 */
public class SessionState {

    private final CarState[] cars;
    private short playerCarIndex;

    // Session metadata
    private long sessionUID;
    private float sessionTime;
    private long frameIdentifier;

    public SessionState() {
        this.cars = new CarState[PacketConstants.MAX_CARS];
        for (int i = 0; i < PacketConstants.MAX_CARS; i++) {
            this.cars[i] = new CarState(i);
        }
        this.playerCarIndex = 0;
    }

    /**
     * Get the state of a specific car.
     *
     * @param carIndex Index of the car (0-21)
     * @return CarState for the specified car, or null if index is invalid
     */
    public CarState getCar(int carIndex) {
        if (carIndex < 0 || carIndex >= PacketConstants.MAX_CARS) {
            return null;
        }
        return cars[carIndex];
    }

    /**
     * Get all car states.
     *
     * @return Array of all 22 car states
     */
    public CarState[] getAllCars() {
        return cars;
    }

    /**
     * Get the player's car state.
     *
     * @return CarState for the player
     */
    public CarState getPlayerCar() {
        return getCar(playerCarIndex);
    }

    /**
     * Update session metadata from packet header.
     */
    public synchronized void updateSessionMetadata(long sessionUID, float sessionTime,
                                                   long frameId, short playerIndex) {
        this.sessionUID = sessionUID;
        this.sessionTime = sessionTime;
        this.frameIdentifier = frameId;
        this.playerCarIndex = playerIndex;
    }

    // Getters
    public short getPlayerCarIndex() { return playerCarIndex; }
    public long getSessionUID() { return sessionUID; }
    public float getSessionTime() { return sessionTime; }
    public long getFrameIdentifier() { return frameIdentifier; }
}
