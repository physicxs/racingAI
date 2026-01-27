package com.racingai.f1telemetry;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * F1 2025 UDP Telemetry Ingestion Application
 *
 * This application receives F1 2025 UDP telemetry data on port 20777,
 * decodes packets, maintains a live state model, and outputs a JSON
 * telemetry stream at 30 Hz.
 *
 * Scope: Data ingestion only - no racing AI or coaching logic.
 */
public class F1TelemetryApp {

    private static final Logger logger = LoggerFactory.getLogger(F1TelemetryApp.class);

    private static final int DEFAULT_UDP_PORT = 20777;
    private static final int OUTPUT_RATE_HZ = 30;

    public static void main(String[] args) {
        logger.info("F1 2025 Telemetry Ingestion System - Starting...");
        logger.info("UDP Port: {}", DEFAULT_UDP_PORT);
        logger.info("Output Rate: {} Hz", OUTPUT_RATE_HZ);

        // Phase 1: Project setup complete
        // Future phases will implement:
        // - UDP receiver
        // - Packet decoder
        // - State management
        // - Nearby car selection
        // - JSON output stream

        logger.info("Phase 1: Project structure initialized successfully");
        logger.info("Ready for implementation of UDP receiver and packet decoding");
    }
}
