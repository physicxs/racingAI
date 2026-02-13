package com.racingai.f1telemetry;

import com.racingai.f1telemetry.decoder.PacketDecoder;
import com.racingai.f1telemetry.decoder.PacketListener;
import com.racingai.f1telemetry.decoder.UDPReceiver;
import com.racingai.f1telemetry.packets.*;
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

        // Phase 3 & 4: UDP receiver and decoder
        UDPReceiver receiver = new UDPReceiver(DEFAULT_UDP_PORT);
        PacketDecoder decoder = new PacketDecoder();

        // Packet statistics
        AtomicLong packetCount = new AtomicLong(0);
        AtomicLong motionPackets = new AtomicLong(0);
        AtomicLong lapDataPackets = new AtomicLong(0);
        AtomicLong telemetryPackets = new AtomicLong(0);
        AtomicLong damagePackets = new AtomicLong(0);

        // Add packet listener with decoder
        receiver.addListener(new PacketListener() {
            @Override
            public void onPacketReceived(byte[] data, int length) {
                long count = packetCount.incrementAndGet();

                // Decode the packet
                Object packet = decoder.decodePacket(data, length);

                if (packet != null) {
                    // Track packet types
                    if (packet instanceof PacketMotionData) {
                        motionPackets.incrementAndGet();
                        if (count == 1) {
                            PacketMotionData motion = (PacketMotionData) packet;
                            logger.info("First Motion packet received! Frame: {}, Session time: {:.2f}s",
                                motion.getHeader().getFrameIdentifier(),
                                motion.getHeader().getSessionTime());
                        }
                    } else if (packet instanceof PacketLapData) {
                        lapDataPackets.incrementAndGet();
                        PacketLapData lapData = (PacketLapData) packet;
                        LapData playerLap = lapData.getLapData(lapData.getHeader().getPlayerCarIndex());
                        logger.info("Lap Data - Position: {}, Lap: {}, Distance: {:.1f}m, Speed trap: {:.1f} km/h",
                            playerLap.getCarPosition(),
                            playerLap.getCurrentLapNum(),
                            playerLap.getLapDistance(),
                            playerLap.getSpeedTrapFastestSpeed());
                    } else if (packet instanceof PacketCarTelemetryData) {
                        telemetryPackets.incrementAndGet();
                        PacketCarTelemetryData telemetry = (PacketCarTelemetryData) packet;
                        CarTelemetryData playerTelemetry = telemetry.getCarTelemetryData(telemetry.getHeader().getPlayerCarIndex());
                        logger.info("Telemetry - Speed: {} km/h, Gear: {}, Throttle: {:.1f}%, Brake: {:.1f}%",
                            playerTelemetry.getSpeed(),
                            playerTelemetry.getGear(),
                            playerTelemetry.getThrottle() * 100,
                            playerTelemetry.getBrake() * 100);
                    } else if (packet instanceof PacketCarDamageData) {
                        damagePackets.incrementAndGet();
                        PacketCarDamageData damage = (PacketCarDamageData) packet;
                        CarDamageData playerDamage = damage.getCarDamageData(damage.getHeader().getPlayerCarIndex());
                        float[] tyreWear = playerDamage.getTyresWear();
                        logger.info("Damage - Tyre wear: FL={:.1f}%, FR={:.1f}%, RL={:.1f}%, RR={:.1f}%",
                            tyreWear[2], tyreWear[3], tyreWear[0], tyreWear[1]);
                    }

                    // Log summary every 100 packets
                    if (count % 100 == 0) {
                        logger.info("Packets: {} total (Motion: {}, Lap: {}, Telemetry: {}, Damage: {})",
                            count, motionPackets.get(), lapDataPackets.get(),
                            telemetryPackets.get(), damagePackets.get());
                    }
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
                logger.info("=== Packet Statistics ===");
                logger.info("Total packets: {}", packetCount.get());
                logger.info("Motion packets: {}", motionPackets.get());
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
            receiver.stop();
        }
    }
}
