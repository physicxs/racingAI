/**
 * JSON output stream generation.
 *
 * Produces newline-delimited JSON (JSONL/NDJSON) telemetry stream:
 * - 30 Hz frame rate
 * - Player state and inputs
 * - Nearby cars selection (up to 6 cars within 1.5s gap)
 * - Tyre wear data where available
 * - Session metadata
 */
package com.racingai.f1telemetry.output;
