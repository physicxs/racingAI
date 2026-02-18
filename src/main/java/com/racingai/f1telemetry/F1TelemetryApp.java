package com.racingai.f1telemetry;

import com.racingai.f1telemetry.config.AppConfig;
import com.racingai.f1telemetry.decoder.PacketDecoder;
import com.racingai.f1telemetry.decoder.PacketListener;
import com.racingai.f1telemetry.decoder.UDPReceiver;
import com.racingai.f1telemetry.output.JsonOutputGenerator;
import com.racingai.f1telemetry.packets.*;
import com.racingai.f1telemetry.state.CarState;
import com.racingai.f1telemetry.state.NearbyCarsSelector;
import com.racingai.f1telemetry.state.StateManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
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

    public static void main(String[] args) {
        logger.info("F1 2025 Telemetry Ingestion System - Starting...");

        // Load configuration
        AppConfig config = new AppConfig();

        // Phase 3 & 4: UDP receiver and decoder
        UDPReceiver receiver = new UDPReceiver(config.getUdpPort());
        PacketDecoder decoder = new PacketDecoder();

        // Phase 5: State management
        StateManager stateManager = new StateManager();

        // Phase 6: Nearby cars selection
        NearbyCarsSelector nearbyCarsSelector = new NearbyCarsSelector(
            config.getNearbyTimeGapSeconds(),
            config.getNearbyMaxCars(),
            config.getNearbyAheadPreferred(),
            config.getNearbyBehindPreferred()
        );

        // Phase 7: JSON output generator
        JsonOutputGenerator jsonOutputGenerator = new JsonOutputGenerator(nearbyCarsSelector);

        // Packet statistics
        AtomicLong packetCount = new AtomicLong(0);
        AtomicLong motionPackets = new AtomicLong(0);
        AtomicLong lapDataPackets = new AtomicLong(0);
        AtomicLong telemetryPackets = new AtomicLong(0);
        AtomicLong damagePackets = new AtomicLong(0);
        AtomicLong sessionPackets = new AtomicLong(0);

        // Add packet listener with decoder
        receiver.addListener(new PacketListener() {
            @Override
            public void onPacketReceived(byte[] data, int length) {
                long count = packetCount.incrementAndGet();

                // Decode the packet
                Object packet = decoder.decodePacket(data, length);

                if (packet != null) {
                    // Update state from packet
                    stateManager.processPacket(packet);

                    // Track packet types
                    if (packet instanceof PacketMotionData) {
                        motionPackets.incrementAndGet();
                        if (count == 1) {
                            logger.info("First packet received - telemetry stream active");
                        }
                    } else if (packet instanceof PacketLapData) {
                        lapDataPackets.incrementAndGet();
                    } else if (packet instanceof PacketCarTelemetryData) {
                        telemetryPackets.incrementAndGet();
                    } else if (packet instanceof PacketCarDamageData) {
                        damagePackets.incrementAndGet();
                    } else if (packet instanceof PacketSessionData) {
                        sessionPackets.incrementAndGet();
                        logger.info("Session packet received (total: {})", sessionPackets.get());
                    }

                    // Log summary every 1000 packets
                    if (count % 1000 == 0) {
                        logger.info("Packets: {} total (Motion: {}, Session: {}, Lap: {}, Telemetry: {}, Damage: {})",
                            count, motionPackets.get(), sessionPackets.get(), lapDataPackets.get(),
                            telemetryPackets.get(), damagePackets.get());
                    }
                }
            }

            @Override
            public void onError(Exception error) {
                logger.error("Packet receiver error: {}", error.getMessage());
            }
        });

        // Create JSON output executor
        ScheduledExecutorService outputExecutor = Executors.newSingleThreadScheduledExecutor();

        // Start UDP receiver
        try {
            receiver.start();
            logger.info("UDP receiver started on port {}", config.getUdpPort());

            // Start JSON output
            long periodMs = 1000 / config.getOutputRateHz();
            outputExecutor.scheduleAtFixedRate(() -> {
                String json = jsonOutputGenerator.generateSnapshot(stateManager.getSessionState());
                if (json != null) {
                    System.out.println(json);
                }
            }, 0, periodMs, TimeUnit.MILLISECONDS);

            logger.info("JSON output started at {} Hz", config.getOutputRateHz());
            logger.info("Press Ctrl+C to stop");

            // Add shutdown hook for graceful stop
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                logger.info("Shutdown signal received");
                outputExecutor.shutdown();
                receiver.stop();
                logger.info("=== Packet Statistics ===");
                logger.info("Total packets: {}", packetCount.get());
                logger.info("Motion packets: {}", motionPackets.get());
                logger.info("Session packets: {}", sessionPackets.get());
                logger.info("Lap data packets: {}", lapDataPackets.get());
                logger.info("Telemetry packets: {}", telemetryPackets.get());
                logger.info("Damage packets: {}", damagePackets.get());
            }));

            // Keep main thread alive
            Thread.currentThread().join();

        } catch (IOException e) {
            logger.error("Failed to start UDP receiver: {}", e.getMessage(), e);
            System.exit(1);
        } catch (InterruptedException e) {
            logger.info("Application interrupted");
            outputExecutor.shutdown();
            receiver.stop();
        }
    }
}
