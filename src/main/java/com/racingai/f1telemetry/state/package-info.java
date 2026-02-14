/**
 * State management for live telemetry data.
 *
 * This package maintains a unified state model that merges data from
 * multiple packet types into a coherent representation of the current
 * racing session.
 *
 * Key classes:
 * - CarState: Represents the merged state of a single car
 * - SessionState: Holds all cars and session metadata
 * - StateManager: Processes packets and updates the state
 */
package com.racingai.f1telemetry.state;
