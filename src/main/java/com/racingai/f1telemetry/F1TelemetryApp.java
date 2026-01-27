package com.racingai.f1telemetry;

import com.racingai.f1telemetry.decoder.PacketListener;
import com.racingai.f1telemetry.decoder.UDPReceiver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicLong;

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

        // Phase 3: UDP receiver implementation
        UDPReceiver receiver = new UDPReceiver(DEFAULT_UDP_PORT);

        // Add a simple packet listener for testing
        AtomicLong packetCount = new AtomicLong(0);
        receiver.addListener(new PacketListener() {
            @Override
            public void onPacketReceived(byte[] data, int length) {
                long count = packetCount.incrementAndGet();
                if (count == 1) {
                    logger.info("First packet received: {} bytes", length);
                } else if (count % 100 == 0) {
                    logger.info("Packets received: {}", count);
                }
            }

            @Override
            public void onError(Exception error) {
                logger.error("Packet receiver error: {}", error.getMessage());
            }
        });

        // Start UDP receiver
        try {
            receiver.start();
            logger.info("UDP receiver started. Listening for F1 2025 telemetry on port {}...", DEFAULT_UDP_PORT);
            logger.info("Press Ctrl+C to stop");

            // Add shutdown hook for graceful stop
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                logger.info("Shutdown signal received");
                receiver.stop();
                logger.info("Total packets received: {}", packetCount.get());
            }));

            // Keep main thread alive
            Thread.currentThread().join();

        } catch (IOException e) {
            logger.error("Failed to start UDP receiver: {}", e.getMessage(), e);
            System.exit(1);
        } catch (InterruptedException e) {
            logger.info("Application interrupted");
            receiver.stop();
        }
    }
}
