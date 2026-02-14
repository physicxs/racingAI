package com.racingai.f1telemetry.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Application configuration loaded from application.properties.
 */
public class AppConfig {

    private static final Logger logger = LoggerFactory.getLogger(AppConfig.class);

    private final int udpPort;
    private final int outputRateHz;
    private final int nearbyMaxCars;
    private final double nearbyTimeGapSeconds;
    private final int nearbyAheadPreferred;
    private final int nearbyBehindPreferred;

    public AppConfig() {
        Properties props = loadProperties();

        this.udpPort = Integer.parseInt(props.getProperty("udp.port", "20777"));
        this.outputRateHz = Integer.parseInt(props.getProperty("output.rate.hz", "30"));
        this.nearbyMaxCars = Integer.parseInt(props.getProperty("nearby.cars.max", "6"));
        this.nearbyTimeGapSeconds = Double.parseDouble(props.getProperty("nearby.cars.time.gap.seconds", "1.5"));
        this.nearbyAheadPreferred = Integer.parseInt(props.getProperty("nearby.cars.ahead.preferred", "4"));
        this.nearbyBehindPreferred = Integer.parseInt(props.getProperty("nearby.cars.behind.preferred", "2"));

        logger.info("Configuration loaded:");
        logger.info("  UDP Port: {}", udpPort);
        logger.info("  Output Rate: {} Hz", outputRateHz);
        logger.info("  Nearby Cars: max={}, timeGap={}s, ahead={}, behind={}",
            nearbyMaxCars, nearbyTimeGapSeconds, nearbyAheadPreferred, nearbyBehindPreferred);
    }

    private Properties loadProperties() {
        Properties props = new Properties();
        try (InputStream input = getClass().getClassLoader().getResourceAsStream("application.properties")) {
            if (input != null) {
                props.load(input);
                logger.info("Loaded configuration from application.properties");
            } else {
                logger.warn("application.properties not found, using defaults");
            }
        } catch (IOException e) {
            logger.warn("Failed to load application.properties: {}, using defaults", e.getMessage());
        }
        return props;
    }

    public int getUdpPort() {
        return udpPort;
    }

    public int getOutputRateHz() {
        return outputRateHz;
    }

    public int getNearbyMaxCars() {
        return nearbyMaxCars;
    }

    public double getNearbyTimeGapSeconds() {
        return nearbyTimeGapSeconds;
    }

    public int getNearbyAheadPreferred() {
        return nearbyAheadPreferred;
    }

    public int getNearbyBehindPreferred() {
        return nearbyBehindPreferred;
    }
}
