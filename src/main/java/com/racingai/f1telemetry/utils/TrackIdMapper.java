package com.racingai.f1telemetry.utils;

import java.util.HashMap;
import java.util.Map;

/**
 * Maps F1 2025 track IDs to track names.
 */
public class TrackIdMapper {

    private static final Map<Byte, String> TRACK_NAMES = new HashMap<>();

    static {
        TRACK_NAMES.put((byte) -1, "Unknown");
        TRACK_NAMES.put((byte) 0, "Melbourne (Australia)");
        TRACK_NAMES.put((byte) 1, "Paul Ricard (France)");
        TRACK_NAMES.put((byte) 2, "Shanghai (China)");
        TRACK_NAMES.put((byte) 3, "Sakhir (Bahrain)");
        TRACK_NAMES.put((byte) 4, "Catalunya (Spain)");
        TRACK_NAMES.put((byte) 5, "Monaco");
        TRACK_NAMES.put((byte) 6, "Montreal (Canada)");
        TRACK_NAMES.put((byte) 7, "Silverstone (Great Britain)");
        TRACK_NAMES.put((byte) 8, "Hockenheim (Germany)");
        TRACK_NAMES.put((byte) 9, "Hungaroring (Hungary)");
        TRACK_NAMES.put((byte) 10, "Spa (Belgium)");
        TRACK_NAMES.put((byte) 11, "Monza (Italy)");
        TRACK_NAMES.put((byte) 12, "Singapore");
        TRACK_NAMES.put((byte) 13, "Suzuka (Japan)");
        TRACK_NAMES.put((byte) 14, "Abu Dhabi (UAE)");
        TRACK_NAMES.put((byte) 15, "Texas (USA)");
        TRACK_NAMES.put((byte) 16, "Brazil");
        TRACK_NAMES.put((byte) 17, "Austria");
        TRACK_NAMES.put((byte) 18, "Sochi (Russia)");
        TRACK_NAMES.put((byte) 19, "Mexico");
        TRACK_NAMES.put((byte) 20, "Baku (Azerbaijan)");
        TRACK_NAMES.put((byte) 21, "Sakhir Short");
        TRACK_NAMES.put((byte) 22, "Silverstone Short");
        TRACK_NAMES.put((byte) 23, "Texas Short");
        TRACK_NAMES.put((byte) 24, "Suzuka Short");
        TRACK_NAMES.put((byte) 25, "Hanoi (Vietnam)");
        TRACK_NAMES.put((byte) 26, "Zandvoort (Netherlands)");
        TRACK_NAMES.put((byte) 27, "Imola (Italy)");
        TRACK_NAMES.put((byte) 28, "Portimão (Portugal)");
        TRACK_NAMES.put((byte) 29, "Jeddah (Saudi Arabia)");
        TRACK_NAMES.put((byte) 30, "Miami (USA)");
        TRACK_NAMES.put((byte) 31, "Las Vegas (USA)");
        TRACK_NAMES.put((byte) 32, "Losail (Qatar)");
    }

    /**
     * Get track name from track ID.
     *
     * @param trackId The track ID (-1 for unknown, 0-32 for specific tracks)
     * @return Track name, or "Unknown Track" if not recognized
     */
    public static String getTrackName(byte trackId) {
        return TRACK_NAMES.getOrDefault(trackId, "Unknown Track (ID: " + trackId + ")");
    }

    /**
     * Get track name from nullable Byte track ID.
     *
     * @param trackId The track ID, or null
     * @return Track name, or "Not Set" if null
     */
    public static String getTrackName(Byte trackId) {
        if (trackId == null) {
            return "Not Set";
        }
        return getTrackName(trackId.byteValue());
    }
}
