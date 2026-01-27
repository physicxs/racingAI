/**
 * Live telemetry state management.
 *
 * Maintains merged state from multiple packet sources:
 * - Player car state (inputs, position, telemetry)
 * - Per-car state for all 22 cars
 * - Session and track metadata
 * - Latest frame and session timestamps
 *
 * Handles packet arrival at different rates and merges into unified state.
 */
package com.racingai.f1telemetry.state;
