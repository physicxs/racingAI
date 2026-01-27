package com.racingai.f1telemetry.packets;

/**
 * Constants for F1 2025 UDP telemetry packets.
 */
public class PacketConstants {

    public static final int MAX_CARS = 22;
    public static final int MAX_PARTICIPANT_NAME_LENGTH = 32;
    public static final int MAX_TYRE_STINTS = 8;
    public static final int MAX_TYRE_SETS = 20; // 13 slick + 7 wet
    public static final int MAX_MARSHAL_ZONES = 21;
    public static final int MAX_WEATHER_FORECAST_SAMPLES = 64;
    public static final int MAX_SESSIONS_IN_WEEKEND = 12;

    public static final int PACKET_FORMAT_2025 = 2025;
    public static final int GAME_YEAR = 25;

    private PacketConstants() {
        // Utility class
    }
}
