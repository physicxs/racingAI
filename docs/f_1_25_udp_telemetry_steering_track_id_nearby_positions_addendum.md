# F1 25 UDP Telemetry – Steering, Track ID, Nearby Positions Addendum

## Purpose
This addendum specifies the exact implementation requirements to add:
1) player steering input
2) track identifier
3) positions for nearby cars (time-based selection)

This is **still within telemetry decoding + JSON export only** (no racing AI logic).

---

## Locked decisions
- **Player index:** use `PacketHeader.m_playerCarIndex` only (single player; ignore `m_secondaryPlayerCarIndex`).
- **UDP binding (Windows):** bind to `0.0.0.0:20777`.
- **Track name:** not required. Output **track_id only**.
- **Car positions to output:** **nearby 6 only** (selected by time-gap logic already specified).

---

## Field sources (official F1 25 UDP structs)

### 1) Steering input
- Source packet: `PacketCarTelemetryData`
- Source field: `m_carTelemetryData[playerIdx].m_steer`
- Output:
  - `player.steer` as float in range `[-1.0, 1.0]`

### 2) Track identifier
- Source packet: `PacketSessionData`
- Source field: `m_trackId`
- Output:
  - `meta.track_id` as integer
- No mapping to human-readable track names.

### 3) Nearby cars positions
- Source packet: `PacketMotionData`
- Source fields per car:
  - `m_carMotionData[carIdx].m_worldPositionX`
  - `m_carMotionData[carIdx].m_worldPositionY`
  - `m_carMotionData[carIdx].m_worldPositionZ`
- Units: meters
- Output:
  - For each selected nearby car: `nearby[].world_pos_m = {x, y, z}`

---

## State-store requirements
Maintain a merged live state so JSON frames can be emitted reliably at the output tick rate:
- Latest `PacketSessionData` (for track id)
- Latest `PacketCarTelemetryData` (for steering)
- Latest `PacketMotionData` (world positions for all cars)
- Latest `PacketLapData` (for nearby selection via time gaps)

---

## JSON emission rules (for these fields)
At each publish tick:
1) Read `playerIdx` from header.
2) Read `track_id` from latest session state (if not yet received, output `null`).
3) Read `player.steer` from latest telemetry state (if not yet received, output `null`).
4) Compute **nearby 6** using existing time-gap selection rules.
5) For each nearby car, include `world_pos_m` from latest motion state.

Recommended minimal JSON shape additions:
- `meta.track_id`
- `player.steer`
- `nearby[]` entries include `world_pos_m`

---

## Notes
- This addendum does not change any earlier decisions (UDP format 2025, 30 Hz, JSONL output, nearby selection logic, privacy handling, etc.).
- Track name mapping can be added later by importing the appendix `trackId → name` table, but is intentionally omitted now.

